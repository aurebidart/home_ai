import time
import logging
from pathlib import Path
from threading import Lock

import cv2
import numpy as np

from home_ai.cameras.manager import CameraManager
from home_ai.vision.detector import Detector
from home_ai.vision.models import Detection
from home_ai.recording.recorder import ContinuousVideoRecorder, VideoRecorder
from home_ai.recording.policies import FixedDurationPolicy
from home_ai.notifications.notifier import Notifier

log = logging.getLogger(__name__)


class SecuritySystem:
    def __init__(
        self,
        cameras: CameraManager,
        detector: Detector,
        recorder: VideoRecorder,
        continuous_recorder: ContinuousVideoRecorder | None,
        recording_policy: FixedDurationPolicy,
        notifier: Notifier,
        cooldown_s: int,
        show_window: bool,
        window_name: str,
    ) -> None:
        self._cameras = cameras
        self._detector = detector
        self._recorder = recorder
        self._continuous_recorder = continuous_recorder
        self._policy = recording_policy
        self._notifier = notifier
        self._cooldown_s = cooldown_s
        self._show_window = show_window
        self._window_name = window_name

        self._last_alert_ts: float = 0.0
        self._system_active: bool = True
        self._latest_frames: dict[str, np.ndarray] = {}
        self._latest_frames_lock = Lock()

    # ---------- control externo ----------

    def activate(self) -> None:
        self._system_active = True
        self._notifier.send_text("🟢 Sistema ACTIVADO")

    def deactivate(self) -> None:
        self._system_active = False
        self._notifier.send_text("🔴 Sistema DESACTIVADO")

    def status(self) -> str:
        return "ACTIVO 🟢" if self._system_active else "INACTIVO 🔴"

    def send_snapshot(self) -> None:
        with self._latest_frames_lock:
            camera_id = next(iter(self._latest_frames), None)
            frame = None
            if camera_id is not None:
                frame = self._latest_frames[camera_id].copy()

        if frame is None or camera_id is None:
            self._notifier.send_text("📸 Todavía no hay imagen disponible")
            return

        self._notifier.send_photo(
            frame,
            caption=f"📸 Captura actual ({camera_id})",
        )

    # ---------- loop principal ----------

    def run(self) -> None:
        log.info("Inicializando sistema de seguridad")

        self._cameras.open_all()

        if self._show_window:
            cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)

        try:
            while True:
                for cam in self._cameras.all():
                    frame = cam.read()
                    if frame is None:
                        continue

                    self._process_frame(cam.camera_id, frame)

                if self._show_window:
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

        finally:
            self.shutdown()

    # ---------- procesamiento ----------

    def _process_frame(self, camera_id: str, frame: np.ndarray) -> None:
        with self._latest_frames_lock:
            self._latest_frames[camera_id] = frame.copy()

        # enviar frame a detector (no bloqueante)
        self._detector.submit_frame(frame)

        detections = self._detector.poll_detections()
        person_detected = any(d.is_person for d in detections)

        now = time.time()

        # ---- grabación continua / archivo circular ----
        if self._continuous_recorder is not None:
            frame_resized = cv2.resize(
                frame,
                self._continuous_recorder.frame_size,
            )
            self._continuous_recorder.write(camera_id, frame_resized)

        # ---- lógica de alerta / grabación ----
        if self._system_active and person_detected:
            if now - self._last_alert_ts >= self._cooldown_s:
                self._last_alert_ts = now
                log.info("🚨 Persona detectada en cámara [%s]", camera_id)

                self._notifier.send_text(
                    f"🚨 Persona detectada en cámara [{camera_id}]"
                )
                self._notifier.send_photo(
                    frame,
                    caption=f"📸 Inicio del evento ({camera_id})",
                )

                self._policy.start()
                self._recorder.start()

        # ---- grabación continua ----
        if self._recorder.is_recording:
            frame_resized = cv2.resize(
                frame,
                self._recorder.frame_size,
            )

            self._recorder.write(frame_resized)

            if self._policy.should_stop():
                video_path: Path | None = self._recorder.stop()
                self._policy.reset()

                if video_path:
                    self._notifier.send_video(
                        video_path,
                        caption="🎥 Video del evento",
                    )

        # ---- visualización ----
        if self._show_window:
            annotated = self._draw_detections(frame, detections)
            cv2.imshow(self._window_name, annotated)

    # ---------- utilidades ----------

    def _draw_detections(
        self,
        frame: np.ndarray,
        detections: list[Detection],
    ) -> np.ndarray:
        annotated = frame.copy()

        for d in detections:
            color = (0, 255, 0) if d.is_person else (255, 255, 0)
            label = f"{d.cls.name.lower()} {d.confidence:.2f}"

            cv2.rectangle(
                annotated,
                (d.x1, d.y1),
                (d.x2, d.y2),
                color,
                2,
            )
            cv2.putText(
                annotated,
                label,
                (d.x1, max(15, d.y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

        return annotated

    # ---------- cierre ----------

    def shutdown(self) -> None:
        log.info("Cerrando sistema")

        try:
            self._detector.close()
        except Exception:
            pass

        if self._continuous_recorder is not None:
            self._continuous_recorder.close()

        self._cameras.close_all()
        cv2.destroyAllWindows()
