# 🏠 Home AI – Sistema de Seguridad Inteligente con YOLO

Home AI es un sistema de **seguridad por visión artificial**, diseñado para operar en tiempo real con **cámaras IP (RTSP)**, detectar eventos mediante **YOLO (GPU)**, **grabar video automáticamente**, y **enviar alertas interactivas por Telegram** usando **webhooks expuestos vía Cloudflare Tunnel**.

El proyecto está pensado como un **backend profesional**, escalable a:
- múltiples cámaras
- múltiples usuarios
- múltiples reglas de detección
- distintos canales de notificación

---

## ✨ Características principales

- 🎥 Captura de video desde cámaras IP (RTSP)
- 🧠 Detección en tiempo real con YOLOv8 (GPU, proceso separado)
- 🚨 Detección de:
  - personas
  - gatos
  - perros
  - mochilas
- 📸 Envío automático de fotos al detectar eventos
- 🎬 Grabación automática de video (ej. 30 segundos por evento)
- 📼 Grabación continua en segmentos comprimidos con retención de 48 horas
- 📤 Envío del video por Telegram
- 📡 Control remoto vía comandos de Telegram (`/on`, `/off`, `/estado`)
- 🌐 Webhook expuesto con **Cloudflare Tunnel**
- 🧱 Arquitectura modular y escalable
- 🔐 Configuración mediante `.env` (sin secretos en código)

---

## 🧠 Arquitectura del sistema

El proyecto sigue una **arquitectura por capas**, con responsabilidades claras:

```

home_ai/
├── cameras/        # Fuentes de video (RTSP, futuras USB/HTTP)
├── vision/         # Detección (YOLO en proceso separado)
├── recording/      # Grabación de video + políticas
├── notifications/  # Telegram (extensible a otros canales)
├── orchestration/  # Lógica central del sistema
├── api/            # Webhook y comandos
├── config/         # Settings, logging, .env
└── main.py         # Entry point (solo composición)

````

### Principios clave
- **YOLO desacoplado** del loop principal
- **No bloqueo** del sistema por red o I/O
- **Escalable** a múltiples cámaras y usuarios
- **Extensible** sin tocar el core

---

## ⚙️ Requisitos

- Python ≥ 3.10
- Linux (probado en Ubuntu)
- GPU NVIDIA + CUDA (opcional, recomendado)
- Cámara IP con RTSP
- Bot de Telegram ya creado
- `cloudflared` instalado

---

## 📦 Instalación

Se recomienda usar un **entorno virtual**.

```bash
git clone https://github.com/tu-usuario/home-ai.git
cd home-ai

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
````

---

## 🔐 Configuración (.env)

Crear un archivo `.env` en la raíz del proyecto:

```env
# Telegram
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=123456789
TELEGRAM_CHAT_IDS=123456789,987654321

# Cámara
CAMERA_RTSP_URL=rtsp://user:pass@192.168.1.100:554/stream1

# Webhook
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8080
WEBHOOK_PATH=/telegram

# Sistema
LOG_LEVEL=INFO
COOLDOWN_SECONDS=60
SHOW_WINDOW=true
WINDOW_NAME=YOLO Seguridad

# Video
RECORD_DURATION_SECONDS=30
RECORD_FPS=15
RECORD_EVENT_OUTPUT_DIR=/tmp/home_ai/videos
RECORD_CONTINUOUS_ENABLED=true
RECORD_CONTINUOUS_OUTPUT_DIR=/tmp/home_ai/continuous
RECORD_CONTINUOUS_SEGMENT_SECONDS=300
RECORD_CONTINUOUS_RETENTION_HOURS=48
RESIZE_WIDTH=640
RESIZE_HEIGHT=360

# YOLO
YOLO_CONF=0.4
YOLO_DEVICE=0
YOLO_IMGSZ=640
YOLO_CLASSES=0,15,16,24
```

Para enviar alertas a más de una persona, usar `TELEGRAM_CHAT_IDS` con IDs
separados por coma. `TELEGRAM_CHAT_ID` queda como compatibilidad para un solo
destinatario.

En servidores con entorno gráfico, `SHOW_WINDOW=true` muestra la cámara en una
ventana local. Si el servidor corre sin escritorio o como servicio sin acceso a
display, usar `SHOW_WINDOW=false`.

> ⚠️ **Nunca subas `.env` a GitHub**. Usá `.env.example`.

---

## ▶️ Ejecución del sistema

Gracias al entrypoint configurado, simplemente ejecutá:

```bash
home-ai
```

Salida esperada:

* cámara conectada
* YOLO inicializado
* webhook activo
* ventana de video (si está habilitada)

---

## 🌐 Exponer el webhook con Cloudflare Tunnel

Telegram **requiere HTTPS**, por lo que usamos **Cloudflare Tunnel**.

### 1️⃣ Levantar el backend

En una terminal:

```bash
home-ai
```

Debe quedar escuchando en:

```
http://localhost:8080/telegram
```

---

### 2️⃣ Levantar Cloudflare Tunnel

En **otra terminal**:

```bash
cloudflared tunnel --url http://localhost:8080
```

Salida esperada:

```
Your quick Tunnel has been created!
https://xxxx.trycloudflare.com
```

Copiar la URL.

---

### 3️⃣ Configurar el webhook de Telegram

```bash
curl -X POST \
"https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
-d "url=https://xxxx.trycloudflare.com/telegram"
```

Verificar:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

Debe mostrar la URL configurada y `pending_update_count: 0`.

---

## 🤖 Comandos de Telegram disponibles

Desde el chat con el bot:

* `/on` → Activa el sistema
* `/off` → Desactiva detecciones
* `/estado` → Devuelve el estado actual

(Extensible fácilmente desde `api/commands.py`)

---

## 🎥 Flujo de un evento

1. Se detecta una **persona**
2. Se envía una **alerta por Telegram**
3. Se envía una **foto**
4. Se inicia grabación de video
5. Luego de N segundos:

   * se cierra el video
   * se envía por Telegram
6. El sistema sigue funcionando sin reiniciarse

---

## 📼 Grabación continua

Mientras el sistema monitorea, también guarda video continuo en segmentos `.mp4`.
Por defecto:

* Directorio: `/tmp/home_ai/continuous`
* Duración de cada segmento: `300` segundos
* Retención: `48` horas

Cuando un segmento nuevo se cierra, el sistema elimina automáticamente los
segmentos continuos que superan la retención configurada. Para cambiarlo, editá:

```env
RECORD_CONTINUOUS_OUTPUT_DIR=/tmp/home_ai/continuous
RECORD_CONTINUOUS_SEGMENT_SECONDS=300
RECORD_CONTINUOUS_RETENTION_HOURS=48
```

---

## 🧪 Estado del proyecto

✔ Arquitectura estable
✔ Separación de responsabilidades
✔ Listo para producción
✔ Escalable

---

## 🚀 Roadmap (ideas futuras)

* Multi-cámara real (por ID)
* Multi-usuario / roles
* Detección por zonas
* Extensión de grabación mientras haya evento
* Persistencia de eventos (DB)
* Docker / systemd service
* App móvil

---

## ⚠️ Seguridad

* Rotar tokens expuestos
* Usar `.env`
* No exponer puertos sin Cloudflare
* Limitar acceso al bot

---

## 📜 Licencia

MIT License

---

## 🙌 Autor

aurebidart

Proyecto desarrollado como sistema de seguridad inteligente, con foco en:

* robustez
* escalabilidad
* buenas prácticas de ingeniería
