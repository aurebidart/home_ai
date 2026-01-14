import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default=None):
    return os.getenv(name, default)


def _env_bool(name: str, default=False) -> bool:
    return _env(name, str(default)).lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default=0) -> int:
    return int(_env(name, default))


def _env_float(name: str, default=0.0) -> float:
    return float(_env(name, default))


def _env_list_int(name: str, default: str) -> list[int]:
    return [int(x) for x in _env(name, default).split(",") if x.strip()]


# ====================== MODELOS ======================

class CameraConfig(BaseModel):
    camera_id: str
    rtsp_url: str


class TelegramSettings(BaseModel):
    bot_token: str
    default_chat_id: str


class CameraSettings(BaseModel):
    resize_w: int
    resize_h: int
    input_send_every_s: float = 0.10


class DetectionSettings(BaseModel):
    classes: list[int]
    conf: float
    device: str | int
    imgsz: int


class RecordingSettings(BaseModel):
    duration_s: int
    fps: int


class WebhookSettings(BaseModel):
    host: str
    port: int
    path: str


class AppSettings(BaseModel):
    log_level: str
    cooldown_s: int
    show_window: bool
    window_name: str

    cameras: list[CameraConfig]
    camera: CameraSettings
    telegram: TelegramSettings
    detection: DetectionSettings
    recording: RecordingSettings
    webhook: WebhookSettings


# ====================== BUILDER ======================

def build_settings() -> AppSettings:
    camera_ids = [c for c in _env("CAMERAS", "").split(",") if c]

    cameras = [
        CameraConfig(
            camera_id=cid,
            rtsp_url=_env(f"CAMERA_{cid.upper()}_RTSP"),
        )
        for cid in camera_ids
    ]

    return AppSettings(
        log_level=_env("LOG_LEVEL", "INFO"),
        cooldown_s=_env_int("COOLDOWN_SECONDS", 60),
        show_window=_env_bool("SHOW_WINDOW", True),
        window_name=_env("WINDOW_NAME", "YOLO Seguridad"),

        cameras=cameras,

        telegram=TelegramSettings(
            bot_token=_env("TELEGRAM_BOT_TOKEN"),
            default_chat_id=_env("TELEGRAM_CHAT_ID"),
        ),

        camera=CameraSettings(
            resize_w=_env_int("RESIZE_WIDTH", 640),
            resize_h=_env_int("RESIZE_HEIGHT", 360),
        ),

        detection=DetectionSettings(
            classes=_env_list_int("YOLO_CLASSES", "0,15,16,24"),
            conf=_env_float("YOLO_CONF", 0.4),
            device=_env("YOLO_DEVICE", "0"),
            imgsz=_env_int("YOLO_IMGSZ", 640),
        ),

        recording=RecordingSettings(
            duration_s=_env_int("RECORD_DURATION_SECONDS", 30),
            fps=_env_int("RECORD_FPS", 15),
        ),

        webhook=WebhookSettings(
            host=_env("WEBHOOK_HOST", "0.0.0.0"),
            port=_env_int("WEBHOOK_PORT", 8080),
            path=_env("WEBHOOK_PATH", "/telegram"),
        ),
    )
