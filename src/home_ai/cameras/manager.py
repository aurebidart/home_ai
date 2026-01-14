import logging
from collections.abc import Iterable

from home_ai.cameras.camera import Camera

log = logging.getLogger(__name__)


class CameraManager:
    def __init__(self, cameras: Iterable[Camera]) -> None:
        self._cameras: dict[str, Camera] = {
            cam.camera_id: cam for cam in cameras
        }

    def open_all(self) -> None:
        for cam in self._cameras.values():
            cam.open()

    def close_all(self) -> None:
        for cam in self._cameras.values():
            cam.close()

    def get(self, camera_id: str) -> Camera | None:
        return self._cameras.get(camera_id)

    def all(self) -> list[Camera]:
        return list(self._cameras.values())
