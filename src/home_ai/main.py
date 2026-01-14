import threading
import logging
from pathlib import Path

from home_ai.config.logging import setup_logging
from home_ai.config.settings import build_settings

from home_ai.cameras import RTSPCamera, CameraManager
from home_ai.vision import YoloDetector
from home_ai.recording import VideoRecorder, FixedDurationPolicy
from home_ai.notifications import TelegramNotifier
from home_ai.orchestration import SecuritySystem
from home_ai.api import create_webhook_app


log = logging.getLogger(__name__)


def main() -> None:
    # =========================================================
    # 1. Configuración y logging
    # =========================================================
    settings = build_settings()
    setup_logging(settings.log_level)

    log.info("Inicializando Home AI")

    # =========================================================
    # 2. Cámaras (MÚLTIPLES, MISMO SYSTEM)
    # =========================================================
    camera_objects = [
        RTSPCamera(
            camera_id=cam.camera_id,
            rtsp_url=cam.rtsp_url,
        )
        for cam in settings.cameras
    ]

    cameras = CameraManager(camera_objects)

    # =========================================================
    # 3. Detector (YOLO en proceso separado)
    # =========================================================
    detector = YoloDetector(
        classes=settings.detection.classes,
        conf=settings.detection.conf,
        device=settings.detection.device,
        imgsz=settings.detection.imgsz,
    )

    # =========================================================
    # 4. Grabación
    # =========================================================
    recorder = VideoRecorder(
        output_dir=Path("/tmp/home_ai/videos"),
        fps=settings.recording.fps,
        frame_size=(
            settings.camera.resize_w,
            settings.camera.resize_h,
        ),
    )

    recording_policy = FixedDurationPolicy(
        duration_s=settings.recording.duration_s
    )

    # =========================================================
    # 5. Notificaciones
    # =========================================================
    notifier = TelegramNotifier(
        bot_token=settings.telegram.bot_token,
        chat_id=settings.telegram.default_chat_id,
    )

    # =========================================================
    # 6. Sistema de orquestación (UNO SOLO)
    # =========================================================
    system = SecuritySystem(
        cameras=cameras,
        detector=detector,
        recorder=recorder,
        recording_policy=recording_policy,
        notifier=notifier,
        cooldown_s=settings.cooldown_s,
        show_window=settings.show_window,
        window_name=settings.window_name,
    )

    # =========================================================
    # 7. Webhook (Telegram)
    # =========================================================
    app = create_webhook_app(
        system=system,
        path=settings.webhook.path,
    )

    def run_webhook() -> None:
        log.info(
            "Webhook escuchando en http://%s:%s%s",
            settings.webhook.host,
            settings.webhook.port,
            settings.webhook.path,
        )
        app.run(
            host=settings.webhook.host,
            port=settings.webhook.port,
            debug=False,
            use_reloader=False,
        )

    threading.Thread(
        target=run_webhook,
        daemon=True,
    ).start()

    # =========================================================
    # 8. Loop principal
    # =========================================================
    system.run()


if __name__ == "__main__":
    main()
