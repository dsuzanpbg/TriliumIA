# Observabilidad y Monitoreo

## IMPORTANCIA

Esta regla establece los estandares de observabilidad para todos los microservicios, incluyendo logging, metricas, tracing y alertas.

**Importante**: Ver referencia en `PBGMicroServices/src/templates/pbg-ms-python-template/` para implementacion real.

---

## Stack de Observabilidad

| Componente | Herramienta | Proposito | Estado |
|------------|-------------|-----------|--------|
| Logging | **Structlog** | Logs estructurados en JSON | ✅ Implementado |
| Errores | **Sentry** | Tracking de errores y excepciones | ✅ Implementado |
| Metrics | **Prometheus** | Metricas y monitoreo | ⚠️ Por agregar |
| Logs Aggregation | **Loki** | Agregacion de logs | ⚠️ Por agregar |
| Dashboards | **Grafana** | Visualizacion | ⚠️ Por agregar |

---

## Logging con Structlog

### Instalacion

```bash
pip install structlog
```

### Configuracion (Igual a PBGMicroServices)

```python
# src/utils/logging.py
import logging
import sys
from typing import Any
import structlog
from structlog.stdlib import LoggerFactory
from src.config import get_settings

settings = get_settings()

def configure_logging() -> None:
    """Configura logging estructurado para todo el servicio."""
    
    # Configurar logging estandar
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if settings.ENVIRONMENT == "production"
                else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str | None = None, **kwargs: Any) -> structlog.BoundLogger:
    """Obtiene un logger configurado."""
    logger = structlog.get_logger(name or settings.SERVICE_NAME)
    if kwargs:
        logger = logger.bind(**kwargs)
    return logger
```

### Uso en el Codigo

```python
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Log basico
logger.info("pdf_processing_started", invoice_id="123", filename="factura.pdf")

# Log con contexto
logger.warning("retry_attempt", attempt=2, max_attempts=3, error="Timeout")

# Log de error
logger.error(
    "ocr_processing_failed",
    invoice_id="123",
    error_type="OcrTimeoutError",
    exc_info=True
)
```

---

## Sentry (Error Tracking)

### Instalacion

```bash
pip install sentry-sdk
```

### Configuracion (Igual a PBGMicroServices)

```python
# src/main.py
from sentry_sdk import init as sentry_init
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# Sentry - inicializar si hay DSN
if settings.SENTRY_DSN:
    sentry_init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
        ],
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
        attach_stacktrace=True,
        send_default_pii=False,
    )
    logger.info("sentry_initialized", dsn_set=True)
```

---

## Configuracion Centralizada

### settings.py (Igual a PBGMicroServices)

```python
# src/config.py
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # SERVICIO
    SERVICE_NAME: str = "pbg-ms-ocr"
    ENVIRONMENT: str = Field(default="development")
    
    # SENTRY (Observabilidad)
    SENTRY_DSN: Optional[str] = Field(default=None)
    
    # REDIS
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    
    # RABBITMQ
    RABBITMQ_HOST: str = Field(default="localhost")
    RABBITMQ_PORT: int = Field(default=5672)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## Prometheus (Metricas) - Por Agregar

### Instalacion

```bash
pip install prometheus-client
```

### Configuracion

```python
from prometheus_client import Counter, Histogram, Gauge

# Contador de requests
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Histograma de latencia
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Gauge para procesos activos
ocr_processing_active = Gauge(
    'ocr_processing_active',
    'Number of OCR processes currently running'
)
```

### Exponer Endpoint de Metricas

```python
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

---

## Variables de Entorno

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `SERVICE_NAME` | Nombre del servicio | `pbg-ms-ocr` |
| `ENVIRONMENT` | Entorno | `production` |
| `SENTRY_DSN` | DSN de Sentry | `https://xxx@sentry.io/xxx` |
| `REDIS_HOST` | Host de Redis | `redis` |
| `RABBITMQ_HOST` | Host de RabbitMQ | `rabbitmq` |

---

## Checklist de Implementacion

- [x] Structlog configurado (ver PBGMicroServices)
- [x] Sentry integrado (ver PBGMicroServices)
- [ ] Prometheus metrics expuestas en /metrics
- [ ] Loki configurado para agregacion de logs
- [ ] Grafana dashboard creado

---

## Referencia

Ver implementacion completa en:
```
PBGMicroServices/src/templates/pbg-ms-python-template/
├── src/main.py           # Sentry init
├── src/config.py        # Settings
└── src/utils/logging.py # Structlog
```
