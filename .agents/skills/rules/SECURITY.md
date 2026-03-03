# Seguridad

## Principios

- Defense in depth
- Least privilege
- Fail secure
- No secrets en codigo

## Autenticacion

### API Keys

```python
# Header: x-api-key
async def verify_api_key(request: Request):
    api_key = request.headers.get("x-api-key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    if not await validate_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True
```

### JWT Tokens

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## Manejo de secretos

### Variables de entorno

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    secret_key: str
    
    class Config:
        env_file = ".env"
```

### No hacer

```python
# MALO - No commitear secrets
API_KEY = "sk-1234567890abcdef"

# MALO - No hardcodear
password = "mi_password_seguro"
```

### Secrets en produccion

- AWS Secrets Manager
- HashiCorp Vault
- GitHub Secrets
- .env.local (no commitear)

## Rate Limiting

```python
from fastapi import FastAPI
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

@app.post("/api/v1/email/send")
@limiter.limit("10/minute")
async def send_email(request: Request):
    # ...
```

## CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tuapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Validacion de entrada

```python
from pydantic import BaseModel, validator

class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    
    @validator('subject')
    def subject_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Subject cannot be empty')
        return v
```

## SQL Injection

```python
# MALO
query = f"SELECT * FROM users WHERE id = {user_id}"

# BIEN - usar parametros
query = "SELECT * FROM users WHERE id = :user_id"
```

## Headers de seguridad

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    middleware_class=GZipMiddleware,
    minimum_size=1000
)
```

## Checklist de seguridad

- [ ] No exponer secretos en codigo
- [ ] Usar HTTPS siempre
- [ ] Validar entrada de usuarios
- [ ] Autenticacion robusta
- [ ] Rate limiting
- [ ] CORS configurado
- [ ] Sanitizar HTML/JS output
- [ ] SQL parameterized queries
- [ ] Dependencias actualizadas
- [ ] Scan de vulnerabilidades
