# API Design

## Principios

- RESTful y predecible
- Versionado de APIs
- Documentacion clara
- Estandarizacion de responses

## Estructura de URLs

```
/api/v1/<recurso>
```

Ejemplos:
```
GET    /api/v1/users
GET    /api/v1/users/{id}
POST   /api/v1/users
PUT    /api/v1/users/{id}
DELETE /api/v1/users/{id}
```

## Versionado

```python
# Version en URL
@app.router("/api/v1/users")
class UsersV1:
    ...

@app.router("/api/v2/users")
class UsersV2:
    ...
```

## Response estandar

```python
# Success
{
    "success": true,
    "data": {...},
    "message": "Operation successful"
}

# Error
{
    "success": false,
    "error": {
        "code": "USER_NOT_FOUND",
        "message": "User not found"
    }
}

# Paginado
{
    "success": true,
    "data": [...],
    "pagination": {
        "page": 1,
        "per_page": 10,
        "total": 100,
        "pages": 10
    }
}
```

## Metodos HTTP

| Metodo | Uso |
|--------|-----|
| GET | Obtener recursos |
| POST | Crear recursos |
| PUT | Actualizar recurso completo |
| PATCH | Actualizar parcialmente |
| DELETE | Eliminar recurso |

## Codigos de estado

| Codigo | Significado |
|--------|------------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Error |

## Documentacion

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

@app.get("/api/v1/users", tags=["users"])
async def get_users(
    page: int = 1,
    per_page: int = 10,
    search: str = None
):
    """
    Obtener lista de usuarios.
    
    - **page**: Numero de pagina
    - **per_page**: Elementos por pagina
    - **search**: Buscar por nombre o email
    """
    ...
```

## Best Practices

- Usar sustantivos en plural
- Usar query params para filtros
- Usar path params para recursos especificos
- Siempre documentar
- Versionar desde el inicio
- Mantener backward compatibility
