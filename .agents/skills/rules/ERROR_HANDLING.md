# Manejo de Errores (Error Handling)

## IMPORTANCIA

Esta regla define los patrones estandar para el manejo de errores en el proyecto.

---

## Principios

1. **Fail Fast** - Detectar errores temprano
2. **Fail Gracefully** - Manejar errores de forma elegante
3. **Log Everything** - Registrar todos los errores
4. **Never Expose Secrets** - No exponer informacion sensible

---

## Python - Estructura de Errores

### Custom Exceptions

```python
# src/core/exceptions.py

class OcrServiceError(Exception):
    """Error base del servicio OCR"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class OcrTimeoutError(OcrServiceError):
    """Tiempo de espera agotado"""
    pass


class OcrProcessingError(OcrServiceError):
    """Error al procesar PDF"""
    pass


class ValidationError(OcrServiceError):
    """Error de validacion de entrada"""
    pass


class ExternalServiceError(OcrServiceError):
    """Error en servicio externo (AWS, etc)"""
    pass


class AuthenticationError(OcrServiceError):
    """Error de autenticacion"""
    pass
```

---

## Python - Try-Catch con Contexto

### Patron Basico

```python
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)


def handle_errors(func):
    """Decorator para manejo automatico de errores."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validacion fallida: {e.message}")
            raise
        except OcrServiceError as e:
            logger.error(f"Error OCR: {e.message}", extra={"details": e.details})
            raise
        except Exception as e:
            logger.exception(f"Error inesperado en {func.__name__}: {e}")
            raise OcrServiceError(f"Error inesperado: {str(e)}")
    return wrapper


@handle_errors
async def process_pdf(document: bytes, filename: str) -> dict:
    # Logica de procesamiento
    pass
```

### Retry Logic

```python
import asyncio
from typing import Callable, TypeVar
from functools import wraps

T = TypeVar('T')


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator con retry exponencial."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Max attempts reached for {func.__name__}: {e}")
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator


@retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(asyncio.TimeoutError, ExternalServiceError))
async def call_external_service(data: dict) -> dict:
    # Llamada a servicio externo
    pass
```

---

## Python - Respuestas de Error API

### FastAPI Exception Handler

```python
# src/core/exceptions.py

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


async def ocr_service_exception_handler(request: Request, exc: OcrServiceError):
    """Manejo personalizado de errores OCR."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            },
            "request_id": request.state.request_id
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    """Manejo de errores de validacion."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Manejo de errores genericos."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor"
            }
        }
    )
```

### Uso en FastAPI

```python
# src/main.py

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

app = FastAPI()

# Registrar handlers
app.add_exception_handler(OcrServiceError, ocr_service_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

---

## Google Apps Script - Manejo de Errores

### Try-Catch Estandar

```javascript
/**
 * Procesa una factura con manejo de errores.
 * 
 * @param {Object} invoice - Datos de la factura
 * @returns {Object} Resultado del procesamiento
 */
function processInvoice(invoice) {
  try {
    // 1. Validar entrada
    if (!invoice.id || !invoice.number) {
      throw new Error("Factura invalida: faltan datos requeridos");
    }
    
    // 2. Obtener attachments
    const attachments = listAttachments_(invoice.id);
    
    // 3. Procesar cada attachment
    const results = attachments.map(att => processAttachment(invoice, att));
    
    // 4. Retornar resultados
    return {
      success: true,
      invoiceId: invoice.id,
      results: results
    };
    
  } catch (error) {
    // Log del error
    console.error("Error procesando factura " + invoice.id + ": " + error.message);
    
    // Retornar estructura de error
    return {
      success: false,
      invoiceId: invoice.id,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
}
```

### Retry con Utilities.sleep

```javascript
/**
 * Reintenta una operacion varias veces.
 * 
 * @param {Function} operation - Funcion a ejecutar
 * @param {number} maxAttempts - Intentos maximos
 * @param {number} delayMs - Delay entre intentos
 * @returns {*} Resultado de la operacion
 */
function retryOperation(operation, maxAttempts = 3, delayMs = 1000) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return operation();
    } catch (error) {
      lastError = error;
      console.log("Intento " + attempt + " fallido: " + error.message);
      
      if (attempt < maxAttempts) {
        Utilities.sleep(delayMs * attempt); // Backoff lineal
      }
    }
  }
  
  throw new Error("Todos los intentos fallaron: " + lastError.message);
}
```

---

## Logging Estructurado

### Python (structlog)

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# Uso
logger.info(
    "pdf_processing_started",
    invoice_id="123",
    filename="factura.pdf",
    file_size_mb=2.5
)

logger.error(
    "pdf_processing_failed",
    invoice_id="123",
    error_type="OCRTimeout",
    error_message="Timeout al procesar PDF",
    retry_count=3
)
```

### Google Apps Script

```javascript
/**
 * Log estructurado para Google Apps Script.
 * 
 * @param {string} level - Nivel de log (info, warn, error)
 * @param {string} message - Mensaje
 * @param {Object} context - Contexto adicional
 */
function structuredLog(level, message, context = {}) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level: level,
    message: message,
    context: context,
    executionId: ScriptApp.getExecutionId()
  };
  
  switch (level) {
    case 'error':
      console.error(JSON.stringify(logEntry));
      break;
    case 'warn':
      console.warn(JSON.stringify(logEntry));
      break;
    default:
      console.log(JSON.stringify(logEntry));
  }
}
```

---

## Health Checks

### Endpoint de Health

```python
# src/presentation/api/routes/health.py

from fastapi import APIRouter, status

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check del servicio."""
    return {
        "status": "healthy",
        "service": "ocr-service",
        "version": "1.0.0"
    }


@router.get("/health/ready")
async def readiness_check():
    """Verifica si el servicio esta listo para recibir requests."""
    checks = {
        "ocr_engine": check_ocr_engine(),
        "dependencies": check_dependencies()
    }
    
    all_healthy = all(check["healthy"] for check in checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }


def check_ocr_engine() -> dict:
    """Verifica que Tesseract este disponible."""
    try:
        # Intentar una operacion simple de OCR
        return {"healthy": True, "engine": "tesseract"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}
```

---

## Lista de Verificacion

- [ ] Usar excepciones custom para errores de negocio
- [ ] No exponer detalles de errores internos al cliente
- [ ] Logging estructurado en todos los catch
- [ ] Retry logic con backoff para operaciones de red
- [ ] Timeouts en todas las llamadas externas
- [ ] Health check endpoint en todos los servicios
- [ ] Circuit breaker para servicios externos

---

*Last updated: 2026-03-02*
