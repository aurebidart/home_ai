import logging
import threading
from flask import Flask, request, Response

from home_ai.api.commands import CommandRouter
from home_ai.orchestration.system import SecuritySystem

log = logging.getLogger(__name__)


def create_webhook_app(system: SecuritySystem, path: str = "/telegram") -> Flask:
    app = Flask(__name__)
    router = CommandRouter(system)

    @app.post(path)
    def telegram_webhook() -> Response:
        data = request.get_json(silent=True) or {}
        msg = (data.get("message") or {}).get("text")

        if msg:
            log.info("📩 Comando recibido: %s", msg)

            # Procesar en background para responder rápido a Telegram
            threading.Thread(
                target=router.handle,
                args=(msg,),
                daemon=True,
            ).start()

        return Response("ok", status=200)

    return app
