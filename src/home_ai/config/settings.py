import os
from pydantic import BaseModel, Field
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


def _env_list_str(name: str, default: str) -> list[str]:
    return [x.strip() for x in (_env(name) or default).split(",") if x.strip()]


# ====================== MODELOS ======================

class TelegramSettings(BaseModel):
    bot_token: str
    chat_ids: list[str]


class CameraSettings(BaseModel):
    rtsp_url: str
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
    event_output_dir: str
    continuous_output_dir: str
    continuous_segment_seconds: int
    continuous_retention_hours: int
    continuous_enabled: bool


class WebhookSettings(BaseModel):
    host: str
    port: int
    path: str


class AppSettings(BaseModel):
    log_level: str
    cooldown_s: int
    show_window: bool
    window_name: str

    telegram: TelegramSettings
    camera: CameraSettings
    detection: DetectionSettings
    recording: RecordingSettings
    webhook: WebhookSettings


# ====================== BUILDER ======================

def build_settings() -> AppSettings:
    return AppSettings(
        log_level=_env("LOG_LEVEL", "INFO"),
        cooldown_s=_env_int("COOLDOWN_SECONDS", 60),
        show_window=_env_bool("SHOW_WINDOW", True),
        window_name=_env("WINDOW_NAME", "YOLO Seguridad"),

        telegram=TelegramSettings(
            bot_token=_env("TELEGRAM_BOT_TOKEN"),
            chat_ids=_env_list_str(
                "TELEGRAM_CHAT_IDS",
                _env("TELEGRAM_CHAT_ID", ""),
            ),
        ),

        camera=CameraSettings(
            rtsp_url=_env("CAMERA_RTSP_URL"),
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
            event_output_dir=_env("RECORD_EVENT_OUTPUT_DIR", "/tmp/home_ai/videos"),
            continuous_output_dir=_env(
                "RECORD_CONTINUOUS_OUTPUT_DIR",
                "/tmp/home_ai/continuous",
            ),
            continuous_segment_seconds=_env_int(
                "RECORD_CONTINUOUS_SEGMENT_SECONDS",
                300,
            ),
            continuous_retention_hours=_env_int(
                "RECORD_CONTINUOUS_RETENTION_HOURS",
                48,
            ),
            continuous_enabled=_env_bool("RECORD_CONTINUOUS_ENABLED", True),
        ),

        webhook=WebhookSettings(
            host=_env("WEBHOOK_HOST", "0.0.0.0"),
            port=_env_int("WEBHOOK_PORT", 8080),
            path=_env("WEBHOOK_PATH", "/telegram"),
        ),
    )
