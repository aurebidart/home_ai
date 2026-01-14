from abc import ABC, abstractmethod
import numpy as np


class Camera(ABC):
    """
    Interfaz base para cualquier tipo de cámara.
    """

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def read(self) -> np.ndarray | None:
        """
        Devuelve un frame BGR o None si no hay frame disponible.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @property
    @abstractmethod
    def camera_id(self) -> str:
        pass
