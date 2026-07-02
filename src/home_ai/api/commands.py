from typing import Callable
import logging

from home_ai.orchestration.system import SecuritySystem

log = logging.getLogger(__name__)


class CommandRouter:
    """
    Rutea comandos de texto hacia acciones del sistema.
    """

    def __init__(self, system: SecuritySystem) -> None:
        self._system = system
        self._commands: dict[str, Callable[[], None | str]] = {
            "/on": self._on,
            "/off": self._off,
            "/estado": self._status,
            "/foto": self._photo,
        }

    def handle(self, text: str) -> None:
        text = text.strip().lower()

        handler = self._commands.get(text)
        if handler is None:
            log.debug("Comando ignorado: %s", text)
            return

        result = handler()
        if isinstance(result, str):
            # El sistema decide cómo notificar
            self._system._notifier.send_text(result)

    # ---------- comandos ----------

    def _on(self) -> None:
        self._system.activate()

    def _off(self) -> None:
        self._system.deactivate()

    def _status(self) -> str:
        return f"📡 Estado: {self._system.status()}"

    def _photo(self) -> None:
        self._system.send_snapshot()
