import os
import logging
import time
from multiprocessing import Process, Queue, Event
from typing import Iterable

import cv2
import numpy as np

from home_ai.vision.detector import Detector
from home_ai.vision.models import Detection, DetectionClass

log = logging.getLogger(__name__)


class YoloDetector(Detector):
    def __init__(
        self,
        classes: Iterable[int],
        conf: float,
        device: str | int,
        imgsz: int,
        max_queue: int = 2,
    ) -> None:
        self._frames_q: Queue = Queue(maxsize=max_queue)
        self._results_q: Queue = Queue(maxsize=5)
        self._stop_event: Event = Event()

        self._process = Process(
            target=_yolo_process,
            args=(
                self._frames_q,
                self._results_q,
                self._stop_event,
                list(classes),
                conf,
                device,
                imgsz,
            ),
            daemon=True,
        )
        self._process.start()

    # ---------- API Detector ----------

    def submit_frame(self, frame_bgr: np.ndarray) -> None:
        ok, jpg = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            return

        try:
            self._frames_q.put_nowait(jpg.tobytes())
        except Exception:
            pass  # descartar frame si está llena la cola

    def poll_detections(self) -> list[Detection]:
        detections: list[Detection] = []

        try:
            while True:
                detections = self._results_q.get_nowait()
        except Exception:
            pass

        return detections

    def close(self) -> None:
        self._stop_event.set()
        if self._process.is_alive():
            self._process.join(timeout=2)

# ================== PROCESO YOLO =====================

def _yolo_process(
    frames_q: Queue,
    results_q: Queue,
    stop_event: Event,
    classes: list[int],
    conf: float,
    device: str | int,
    imgsz: int,
) -> None:
    os.environ["YOLO_VERBOSE"] = "False"
    os.environ["ULTRALYTICS_VERBOSE"] = "False"
    os.environ.setdefault("TORCH_CPP_LOG_LEVEL", "ERROR")
    os.environ.setdefault("GLOG_minloglevel", "2")

    from ultralytics import YOLO
    import torch

    try:
        torch.backends.nnpack.enabled = False
    except Exception:
        pass

    selected_device = str(device).strip().lower()
    if selected_device not in ("cpu", "mps") and not torch.cuda.is_available():
        log.warning(
            "CUDA no disponible para YOLO_DEVICE=%s; usando CPU",
            device,
        )
        selected_device = "cpu"

    log.info("Inicializando YOLO (device=%s)", selected_device)
    model = YOLO("yolov8n.pt", verbose=False)

    while not stop_event.is_set():
        try:
            jpg = frames_q.get(timeout=0.2)
        except Exception:
            continue

        frame = cv2.imdecode(
            np.frombuffer(jpg, dtype=np.uint8),
            cv2.IMREAD_COLOR,
        )
        if frame is None:
            continue

        try:
            results = model.predict(
                frame,
                conf=conf,
                classes=classes,
                device=selected_device,
                imgsz=imgsz,
                verbose=False,
            )
        except Exception as exc:
            log.warning("YOLO error (%s), fallback CPU", exc)
            results = model.predict(
                frame,
                conf=conf,
                classes=classes,
                device="cpu",
                imgsz=imgsz,
                verbose=False,
            )

        detections: list[Detection] = []

        r0 = results[0]
        if r0.boxes is not None:
            for b in r0.boxes:
                cls_id = int(b.cls[0])
                try:
                    cls = DetectionClass(cls_id)
                except ValueError:
                    continue

                x1, y1, x2, y2 = map(int, b.xyxy[0])
                detections.append(
                    Detection(
                        cls=cls,
                        confidence=float(b.conf[0]),
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                    )
                )

        try:
            results_q.put_nowait(detections)
        except Exception:
            pass
