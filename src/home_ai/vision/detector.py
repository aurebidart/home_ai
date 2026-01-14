from abc import ABC, abstractmethod
import numpy as np

from home_ai.vision.models import Detection


class Detector(ABC):
    """
    Interfaz base para cualquier detector de visión.
    """

    @abstractmethod
    def submit_frame(self, frame_bgr: np.ndarray) -> None:
        """
        Envia un frame para procesar (no bloqueante).
        """
        pass

    @abstractmethod
    def poll_detections(self) -> list[Detection]:
        """
        Devuelve las últimas detecciones disponibles (no bloqueante).
        """
        pass

    @abstractmethod
    def close(self) -> None:
        pass
