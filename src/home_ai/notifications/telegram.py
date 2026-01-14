import os
import uuid
import threading
import logging
from pathlib import Path

import cv2
import numpy as np
import requests

from home_ai.notifications.notifier import Notifier


log = logging.getLogger(__name__)


class TelegramNotifier(Notifier):
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._base_url = f"https://api.telegram.org/bot{bot_token}"

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
        try:
            requests.post(
                f"{self._base_url}/sendMessage",
                data={
                    "chat_id": self._chat_id,
                    "text": text,
                },
                timeout=5,
            )
        except Exception as exc:
            log.warning("Error enviando texto Telegram: %s", exc)

    def _send_photo_impl(self, frame_bgr: np.ndarray, caption: str | None) -> None:
        filename = Path(f"/tmp/telegram_img_{uuid.uuid4().hex}.jpg")

        try:
            cv2.imwrite(str(filename), frame_bgr)

            with open(filename, "rb") as img:
                data = {"chat_id": self._chat_id}
                if caption:
                    data["caption"] = caption

                requests.post(
                    f"{self._base_url}/sendPhoto",
                    data=data,
                    files={"photo": img},
                    timeout=20,
                )

        except Exception as exc:
            log.warning("Error enviando foto Telegram: %s", exc)

        finally:
            try:
                if filename.exists():
                    filename.unlink()
            except Exception:
                pass

    def _send_video_impl(self, video_path: Path, caption: str | None) -> None:
        try:
            with open(video_path, "rb") as vid:
                data = {"chat_id": self._chat_id}
                if caption:
                    data["caption"] = caption

                requests.post(
                    f"{self._base_url}/sendVideo",
                    data=data,
                    files={"video": vid},
                    timeout=60,
                )

        except Exception as exc:
            log.warning("Error enviando video Telegram: %s", exc)
