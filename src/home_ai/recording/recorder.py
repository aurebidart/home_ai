import cv2
import time
import uuid
import logging
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)


class VideoRecorder:
    def __init__(
        self,
        output_dir: Path,
        fps: int,
        frame_size: tuple[int, int],
        codec: str = "mp4v",
    ) -> None:
        self._output_dir = output_dir
        self._fps = fps
        self._frame_size = frame_size
        self._codec = codec

        self._writer: cv2.VideoWriter | None = None
        self._start_ts: float | None = None
        self._path: Path | None = None

        self._output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def frame_size(self) -> tuple[int, int]:
        return self._frame_size

    @property
    def is_recording(self) -> bool:
        return self._writer is not None

    def start(self) -> None:
        if self._writer is not None:
            return

        filename = f"event_{int(time.time())}_{uuid.uuid4().hex}.mp4"
        self._path = self._output_dir / filename

        fourcc = cv2.VideoWriter_fourcc(*self._codec)
        self._writer = cv2.VideoWriter(
            str(self._path),
            fourcc,
            self._fps,
            self._frame_size,
        )
        self._start_ts = time.time()

        log.info("🎥 Grabación iniciada: %s", self._path)

    def write(self, frame_bgr: np.ndarray) -> None:
        if self._writer is None:
            return

        self._writer.write(frame_bgr)

    def stop(self) -> Path | None:
        if self._writer is None:
            return None

        self._writer.release()
        self._writer = None

        path = self._path
        self._path = None
        self._start_ts = None

        log.info("🛑 Grabación finalizada: %s", path)
        return path


class ContinuousVideoRecorder:
    def __init__(
        self,
        output_dir: Path,
        fps: int,
        frame_size: tuple[int, int],
        segment_seconds: int,
        retention_hours: int,
        codec: str = "mp4v",
    ) -> None:
        self._output_dir = output_dir
        self._fps = fps
        self._frame_size = frame_size
        self._segment_seconds = segment_seconds
        self._retention_seconds = retention_hours * 60 * 60
        self._codec = codec

        self._writer: cv2.VideoWriter | None = None
        self._segment_start_ts: float | None = None
        self._path: Path | None = None
        self._last_cleanup_ts: float = 0.0

        self._output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def frame_size(self) -> tuple[int, int]:
        return self._frame_size

    def write(self, camera_id: str, frame_bgr: np.ndarray) -> None:
        now = time.time()

        if self._writer is None:
            self._start_segment(camera_id, now)
        elif self._segment_start_ts is not None:
            if now - self._segment_start_ts >= self._segment_seconds:
                self._stop_segment()
                self._cleanup_old_segments(now)
                self._start_segment(camera_id, now)

        if self._writer is not None:
            self._writer.write(frame_bgr)

    def close(self) -> None:
        self._stop_segment()

    def _start_segment(self, camera_id: str, now: float) -> None:
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(now))
        safe_camera_id = "".join(
            c if c.isalnum() or c in ("-", "_") else "_"
            for c in camera_id
        )
        filename = f"continuous_{safe_camera_id}_{timestamp}.mp4"
        self._path = self._output_dir / filename

        fourcc = cv2.VideoWriter_fourcc(*self._codec)
        self._writer = cv2.VideoWriter(
            str(self._path),
            fourcc,
            self._fps,
            self._frame_size,
        )
        self._segment_start_ts = now

        log.info("📼 Grabación continua iniciada: %s", self._path)

    def _stop_segment(self) -> None:
        if self._writer is None:
            return

        self._writer.release()
        self._writer = None

        log.info("📼 Grabación continua cerrada: %s", self._path)
        self._path = None
        self._segment_start_ts = None

    def _cleanup_old_segments(self, now: float) -> None:
        if now - self._last_cleanup_ts < 60:
            return

        self._last_cleanup_ts = now
        cutoff = now - self._retention_seconds

        for path in self._output_dir.glob("continuous_*.mp4"):
            if self._path is not None and path == self._path:
                continue

            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    log.info("🧹 Video continuo eliminado por retención: %s", path)
            except FileNotFoundError:
                continue
