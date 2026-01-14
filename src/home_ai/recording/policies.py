import time


class FixedDurationPolicy:
    """
    Política simple:
    - empieza a grabar cuando se dispara
    - corta luego de N segundos
    """

    def __init__(self, duration_s: int) -> None:
        self._duration_s = duration_s
        self._start_ts: float | None = None

    def start(self) -> None:
        self._start_ts = time.time()

    def should_stop(self) -> bool:
        if self._start_ts is None:
            return False

        return (time.time() - self._start_ts) >= self._duration_s

    def reset(self) -> None:
        self._start_ts = None
