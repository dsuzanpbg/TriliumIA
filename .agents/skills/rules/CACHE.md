# Cache - Redis

## Uso

- Cache de datos
- Sesiones
- Rate limiting
- Colas de jobs

## Redis con Python

```python
import redis
from typing import Optional
import json

class Cache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def get(self, key: str) -> Optional[dict]:
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    def set(self, key: str, value: dict, ttl: int = 300):
        self.redis.setex(key, ttl, json.dumps(value))
    
    def delete(self, key: str):
        self.redis.delete(key)
    
    def exists(self, key: str) -> bool:
        return self.redis.exists(key) > 0
```

## Cache de funciones

```python
from functools import wraps

def cache(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            cached = cache.get(key)
            if cached:
                return cached
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator

@cache(ttl=60)
def get_user(user_id: int):
    return db.query(User).get(user_id)
```

## Keys

```
pbg:<servicio>:<entidad>:<id>
```

Ejemplos:
```
pbg:email:template:1
pbg:user:session:abc123
pbg:order:cache:456
```

## TTL recomendados

| Tipo | TTL |
|------|-----|
| Sesiones | 24 horas |
| Datos de usuario | 5 minutos |
| Consultas DB | 1 minuto |
| Configuracion | 1 hora |
| Rate limits | 1 minuto |

## Patterns

### Cache-Aside

```python
# 1. Leer cache
user = cache.get(f"user:{user_id}")

# 2. Si no esta, leer DB
if not user:
    user = db.query(User).get(user_id)
    cache.set(f"user:{user_id}", user)

# 3. Retornar
return user
```

### Write-Through

```python
def create_user(user):
    db.add(user)
    db.commit()
    cache.set(f"user:{user.id}", user)
    return user
```

## Comandos

```bash
# CLI
redis-cli ping
redis-cli KEYS "pbg:*"
redis-cli GET key
redis-cli SET key value
redis-cli DEL key
redis-cli FLUSHDB
```
