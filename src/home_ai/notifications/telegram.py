import threading
import logging
from pathlib import Path

import cv2
import numpy as np
import requests

from home_ai.notifications.notifier import Notifier


log = logging.getLogger(__name__)


class TelegramNotifier(Notifier):
    def __init__(self, bot_token: str, chat_ids: list[str]) -> None:
        self._bot_token = bot_token
        self._chat_ids = chat_ids
        self._base_url = f"https://api.telegram.org/bot{bot_token}"

        if not self._chat_ids:
            log.warning("Telegram sin destinatarios: TELEGRAM_CHAT_IDS está vacío")

    # ---------- API pública ----------

    def send_text(self, text: str) -> None:
        threading.Thread(
            target=self._send_text_impl,
            args=(text,),
            daemon=True,
        ).start()

    def send_photo(self, frame_bgr: np.ndarray, caption: str | None = None) -> None:
        threading.Thread(
            target=self._send_photo_impl,
            args=(frame_bgr, caption),
            daemon=True,
        ).start()

    def send_video(self, video_path: Path, caption: str | None = None) -> None:
        threading.Thread(
            target=self._send_video_impl,
            args=(video_path, caption),
            daemon=True,
        ).start()

    # ---------- Implementación interna ----------

    def _send_text_impl(self, text: str) -> None:
        for chat_id in self._chat_ids:
            try:
                response = requests.post(
                    f"{self._base_url}/sendMessage",
                    data={
                        "chat_id": chat_id,
                        "text": text,
                    },
                    timeout=5,
                )
                self._log_telegram_error(response, "texto", chat_id)
            except Exception as exc:
                log.warning("Error enviando texto Telegram a %s: %s", chat_id, exc)

    def _send_photo_impl(self, frame_bgr: np.ndarray, caption: str | None) -> None:
        try:
            ok, encoded = cv2.imencode(".jpg", frame_bgr)
            if not ok:
                log.warning("Error codificando foto Telegram")
                return

            image_bytes = encoded.tobytes()

            for chat_id in self._chat_ids:
                data = {"chat_id": chat_id}
                if caption:
                    data["caption"] = caption

                try:
                    response = requests.post(
                        f"{self._base_url}/sendPhoto",
                        data=data,
                        files={"photo": ("alert.jpg", image_bytes, "image/jpeg")},
                        timeout=20,
                    )
                    self._log_telegram_error(response, "foto", chat_id)
                except Exception as exc:
                    log.warning("Error enviando foto Telegram a %s: %s", chat_id, exc)

        except Exception as exc:
            log.warning("Error enviando foto Telegram: %s", exc)

    def _send_video_impl(self, video_path: Path, caption: str | None) -> None:
        for chat_id in self._chat_ids:
            try:
                with open(video_path, "rb") as vid:
                    data = {"chat_id": chat_id}
                    if caption:
                        data["caption"] = caption

                    response = requests.post(
                        f"{self._base_url}/sendVideo",
                        data=data,
                        files={"video": vid},
                        timeout=60,
                    )
                    self._log_telegram_error(response, "video", chat_id)

            except Exception as exc:
                log.warning("Error enviando video Telegram a %s: %s", chat_id, exc)

    def _log_telegram_error(
        self,
        response: requests.Response,
        kind: str,
        chat_id: str,
    ) -> None:
        if response.ok:
            return

        log.warning(
            "Telegram rechazo %s a %s: status=%s body=%s",
            kind,
            chat_id,
            response.status_code,
            response.text[:300],
        )
