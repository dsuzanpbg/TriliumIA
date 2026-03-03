# Troubleshooting

## Problemas comunes

### Python

#### ModuleNotFoundError

```bash
# Solucion
pip install -r requirements.txt
```

#### ImportError

```bash
# Verificar path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Memory error

```bash
# Aumentar memoria
ulimit -v unlimited
```

### Docker

#### Container no inicia

```bash
# Ver logs
docker logs <container>

# Ver status
docker ps -a
```

#### Puerto en uso

```bash
# Ver que usa el puerto
lsof -i :8000

# Matar proceso
kill <PID>
```

#### Out of memory

```bash
# Aumentar memoria Docker
docker system prune -a
```

### Database

#### Connection refused

```bash
# Verificar servicio
pg_isready -h localhost -p 5432

# Ver logs
docker logs postgres_container
```

#### Too many connections

```python
# Reducir pool
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10
)
```

### RabbitMQ

#### Connection refused

```bash
# Verificar que esta corriendo
docker ps | grep rabbitmq

# Ver logs
docker logs rabbitmq_container
```

### Redis

#### Connection refused

```bash
# Verificar
redis-cli ping

# Si no responde, reiniciar
docker-compose restart redis
```

## Debugging

### Python

```python
import logging

# Habilitar debug
logging.basicConfig(level=logging.DEBUG)

# Usar breakpoints
breakpoint()  # Python 3.7+
```

### FastAPI

```python
# Habilitar debug
app = FastAPI(debug=True)
```

### Sentry

```python
# Ver errores en Sentry dashboard
# Buscar por: environment, release, user
```

## Comandos utiles

```bash
# Ver procesos
ps aux | grep python

# Ver puertos
netstat -tulpn

# Ver memoria
free -h

# Ver disco
df -h
```
