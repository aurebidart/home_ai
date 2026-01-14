import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """
    Logging estándar para consola.
    - Sin spam por frame.
    - Formato consistente.
    """
    lvl = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(lvl)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(lvl)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Evitar duplicados si se llama más de una vez
    root.handlers.clear()
    root.addHandler(handler)

    # Silenciar logs ruidosos
    logging.getLogger("ultralytics").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
