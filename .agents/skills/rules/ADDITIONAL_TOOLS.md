# Herramientas Adicionales

## IMPORTANCIA

Esta regla documenta las herramientas adicionales disponibles en el ecosistema que pueden utilizarse para facilitar ciertas tareas.

---

## n8n (Self-Hosted)

### Descripcion
n8n es una herramienta de automatización de flujos de trabajo (workflow automation) que permite conectar diferentes servicios y automatizar tareas sin escribir código.

### Cuándo Considerar

| Caso de uso | Recomendacion |
|-------------|---------------|
| Integraciones simples entre APIs | Usar n8n |
| Automatizaciones con UI visual | Usar n8n |
| Conexiones con webhooks | Usar n8n |
| Procesamiento complejo de datos | Python/Node.js |
| Lógica de negocio critica | Python/Node.js |
| OCR de alto volumen | Python (servicio dedicado) |

### Integracion con el Proyecto

n8n puede ser utilizado para:

1. **Monitoreo**
   - Alertas cuando el servicio OCR falla
   - Notificaciones de estado

2. **Orquestacion**
   - Iniciar flujos de procesamiento
   - Coordinar múltiples servicios

3. **Webhooks**
   - Recibir callbacks de Xero
   - Reenviar eventos a otros sistemas

4. **Backup/Export**
   - Exportar resultados a otras herramientas
   - Sincronizar con otros sistemas

### Configuracion n8n

```
URL: http://n8n.tudominio.com:5678
Puerto: 5678
Authentication: Activada
```

### Ejemplo de Workflow n8n

```
[Webhook] --> [HTTP Request (OCR)] --> [Condition] --> [Slack Notification]
                                              |
                                              v
                                    [Update Google Sheet]
```

---

## Comparativa de Herramientas

| Herramienta | Fortalezas | Cuando usar |
|------------|------------|-------------|
| **Python/FastAPI** | Control total, alto rendimiento | OCR, APIs, procesamiento |
| **Google Apps Script** | Integracion Google | Automatizacion Sheets/Drive |
| **n8n** | UI visual, rapido de prototipar | Integraciones simples, webhooks |
| **Docker** | Portabilidad | Produccion, despliegue |

---

## Regla de decision

1. **Si la tarea es simple** (conectar 2-3 servicios, webhooks) → Considerar n8n
2. **Si la tarea es compleja** (lógica de negocio, procesamiento) → Python/Node.js
3. **Si requiere integración Google** → Google Apps Script
4. **Si es crítico para el negocio** → Python/Node.js (más control)

---

*Last updated: 2026-03-02*
