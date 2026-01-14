import time
import logging
import cv2
import numpy as np

from home_ai.cameras.camera import Camera

log = logging.getLogger(__name__)


class RTSPCamera(Camera):
    def __init__(self, camera_id: str, rtsp_url: str) -> None:
        self._camera_id = camera_id
        self._rtsp_url = rtsp_url
        self._cap: cv2.VideoCapture | None = None
        self._last_fail_ts: float = 0.0

    @property
    def camera_id(self) -> str:
        return self._camera_id

    def open(self) -> None:
        log.info("Abriendo cámara RTSP [%s]", self._camera_id)
        self._cap = cv2.VideoCapture(self._rtsp_url, cv2.CAP_FFMPEG)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

    def read(self) -> np.ndarray | None:
        if self._cap is None or not self._cap.isOpened():
            self._try_reconnect()
            return None

        ok, frame = self._cap.read()
        if not ok:
            self._try_reconnect()
            return None

        return frame

    def close(self) -> None:
        if self._cap is not None:
            log.info("Cerrando cámara [%s]", self._camera_id)
            self._cap.release()
            self._cap = None

    # ---------- internos ----------

    def _try_reconnect(self) -> None:
        now = time.time()
        # evitar reconectar en loop
        if now - self._last_fail_ts < 2.0:
            return

        self._last_fail_ts = now
        log.warning("Reconectando cámara [%s]...", self._camera_id)

        try:
            if self._cap is not None:
                self._cap.release()
        except Exception:
            pass

        self._cap = cv2.VideoCapture(self._rtsp_url, cv2.CAP_FFMPEG)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
