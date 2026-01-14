from abc import ABC, abstractmethod
from pathlib import Path
import numpy as np


class Notifier(ABC):
    """
    Interfaz base para cualquier sistema de notificaciones.
    """

    @abstractmethod
    def send_text(self, text: str) -> None:
        pass

    @abstractmethod
    def send_photo(self, frame_bgr: np.ndarray, caption: str | None = None) -> None:
        pass

    @abstractmethod
    def send_video(self, video_path: Path, caption: str | None = None) -> None:
        pass
