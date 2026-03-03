# Configuration

## pydantic-settings

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # App
    app_name: str = "My Service"
    debug: bool = False
    environment: str = "development"
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    
    # API
    api_key: str
    api_version: str = "v1"
    
    # External services
    sentry_dsn: Optional[str] = None
    
    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

# Instancia global
settings = Settings()
```

## Variables de entorno

```
# .env
APP_NAME=My Service
DEBUG=false
ENVIRONMENT=production

DATABASE_URL=postgresql://user:pass@localhost:5432/mydb

REDIS_URL=redis://localhost:6379

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

SENTRY_DSN=https://xxx@sentry.io/xxx
```

## .env.example

```bash
# Copiar a .env y completar
cp .env.example .env
```

## En FastAPI

```python
from fastapi import FastAPI
from src.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.environment}
```

## Secretos

No poner en .env:
- Tokens reales
- Passwords de produccion
- API keys de prod

Usar:
- GitHub Secrets
- AWS Secrets Manager
- HashiCorp Vault

## Ambientes

| Entorno | Caracteristicas |
|---------|----------------|
| development | Debug=True, DB local |
| staging | Debug=False, DB staging |
| production | Debug=False, DB prod, Sentry |

```python
# Segun ambiente
if settings.environment == "production":
    # Configuracion adicional de seguridad
```
