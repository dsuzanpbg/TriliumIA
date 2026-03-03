# Docker y Containerizacion

## Principios

- Imagenes pequenas y seguras
- Una responsabilidad por contenedor
- Configuracion via variables de entorno
- Health checks incluidos

## Estructura de Dockerfile

```dockerfile
# Usar imagen base oficial
FROM python:3.11-slim

# Definir metadata
LABEL maintainer="dev@tuempresa.com"
LABEL version="1.0"

# Argumentos de build
ARG BUILD_DATE
ARG VERSION

# Setear variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Trabajador no root
RUN useradd -m -s /bin/bash appuser

# Instalar dependencias primero (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo
COPY src/ ./src/

# Cambiar a usuario no root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando inicial
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Mejores practicas

### Seguridad

```dockerfile
# NO hacer esto:
# RUN apt-get update && apt-get install -y curl

# En su lugar, usar imagen slim y agregar solo lo necesario
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Usar usuario no root
USER appuser

# No exponer secretos
# Malo: ENV API_KEY=secret
# Bien: Passing via runtime -e API_KEY=$API_KEY
```

### Optimizacion

```dockerfile
# Orden correcto para cache
COPY requirements.txt .
RUN pip install ...

COPY src/ ./src/

# Multi-stage build para reducir tamano
FROM python:3.11-slim AS builder
RUN pip install --target=/deps -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /deps /usr/local/lib/python3.11/site-packages
COPY src/ ./src/
```

### Health checks

```python
# FastAPI example
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/ready")
def ready():
    # Verificar conexiones
    check_db()
    check_redis()
    return {"status": "ready"}
```

## Comandos utiles

```bash
# Build
docker build -t mi-servicio:v1.0.0 .

# Run
docker run -d -p 8000:8000 --name mi-servicio mi-servicio:v1.0.0

# Logs
docker logs -f mi-servicio

# Exec
docker exec -it mi-servicio bash

# Compose
docker-compose up -d
docker-compose logs -f
docker-compose down

# Rebuild
docker-compose build --no-cache
```
