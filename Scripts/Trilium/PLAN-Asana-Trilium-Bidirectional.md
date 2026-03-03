# Plan: Script Asana-Trilium Bidireccional

## Objetivo

Crear un script de sincronizacion bidireccional entre Asana y Trilium Notes que respete el formato completo de Asana y permita edicion desde ambas plataformas.

## Analisis de API

### Asana API - Endpoints Principales

| Recurso | Endpoint | Descripcion |
|---------|----------|-------------|
| Tasks | GET /tasks | Lista tareas |
| Task | GET /tasks/{gid} | Detalle tarea |
| Subtasks | GET /tasks/{gid}/subtasks | Subtareas |
| Projects | GET /projects | Lista proyectos |
| Sections | GET /projects/{gid}/sections | Secciones |
| Stories | GET /tasks/{gid}/stories | Comentarios |
| Attachments | GET /tasks/{gid}/attachments | Adjuntos |
| Custom Fields | GET /projects/{gid}/custom_field_settings | Campos personalizados |

### Trilium API - Capacidades

- Crear/editar/borrar notas
- Setear labels
- Organizar jerarquia (parent/child)
- Contenido en formato markdown/HTML

## Requisitos

### 1. Sincronizacion Asana -> Trilium

- Estructura de proyectos y secciones
- Tareas con todos los campos
- Subtareas anidadas
- Descripciones HTML
- Campos personalizados
- Tags de Asana
- Comentarios (stories)
- Adjuntos (referencias)
- Fechas: due_on, due_at, start_at
- Prioridad (si existe)
- Dependencies

### 2. Sincronizacion Trilium -> Asana

- Detectar cambios en Trilium
- Actualizar tareas en Asana
- Crear nuevas tareas desde Trilium
- Manejo de conflictos

### 3. Formato (Reglas del Proyecto)

- **Sin emojis** - texto plano
- Lenguaje ubiquo por dominio
- Formato legible en Trilium

## Estructura de Datos en Trilium

```
Carpeta Raiz (configurable)
├── Projects/
│   ├── Proyecto 1/
│   │   ├── Seccion 1/
│   │   │   ├── TAREA-001: Nombre tarea
│   │   │   │   ├── Descripcion
│   │   │   │   ├── Subtareas/
│   │   │   │   ├── Comentarios/
│   │   │   │   └── Metadata (labels)
│   │   │   └── TAREA-002: ...
│   │   └── Seccion 2/
│   └── Proyecto 2/
└── Sync-Metadata/
    └── ultima-sincronizacion
```

## Labels en Trilium

| Label | Uso |
|-------|-----|
| asanaTaskGid | ID de Asana |
| asanaProjectGid | ID del proyecto |
| asanaSectionGid | ID de seccion |
| asanaParentTaskGid | ID de tarea padre (subtarea) |
| syncStatus | pending/synced/modified |
| lastModified | Fecha de ultima modificacion |
| pendingSync | Cambios pendientes de enviar |
| priority | Prioridad |
| dueDate | Fecha limite |
| startDate | Fecha de inicio |

## Arquitectura del Script

### Modulos

1. **AsanaClient** - Cliente API de Asana
2. **TriliumClient** - Cliente API de Trilium
3. **SyncEngine** - Motor de sincronizacion
4. **ConflictResolver** - Resolucion de conflictos
5. **Formatter** - Formateo de datos

### Flujo de Sincronizacion

```
1. syncFromAsana()
   a. Obtener proyectos
   b. Obtener secciones
   c. Obtener tareas
   d. Obtener subtareas
   e. Obtener campos personalizados
   f. Obtener comentarios
   g. Construir estructura
   h. Crear/actualizar en Trilium

2. syncToAsana()
   a. Buscar notas con pendingSync
   b. Comparar timestamps
   c. Actualizar en Asana
   d. Marcar como synced
```

## Features Detalladas

### 1. Estructura de Proyectos

- Mantener jerarquia proyecto -> seccion -> tarea
- Crear notas separadas por proyecto
- Crear subnotas por seccion

### 2. Descripciones HTML

- Preservar formato HTML de Asana
- Convertir a formato compatible con Trilium

### 3. Subtareas

- Anidar como notas hijos
- Mantener relacion padre-hijo

### 4. Campos Personalizados

- Extraer del proyecto
- Mostrar como metadata en la tarea

### 5. Tags

- Traducir a labels en Trilium

### 6. Comentarios

- Crear seccion de comentarios
- Incluir autor y fecha

### 7. Adjuntos

- Referenciar en la tarea
- Link al archivo en Asana

### 8. Fechas

- due_on (fecha)
- due_at (fecha + hora)
- start_at / start_on

### 9. Bidireccional

- Modificar en Trilium -> actualizar en Asana
- Usar labels para tracking
- Timestamp para deteccion de cambios

## Configuracion (Labels en Nota Script)

```
#asanaToken=xxxxx
#asanaWorkspaceGid=xxxxx
#asanaParentNoteId=xxxxx
#asanaIncludeCompleted=1
#triliumBaseSyncFolder=Asana
#syncDirection=bidirectional  (o "asana-to-trilium")
#conflictResolution=trilium-wins (o "asana-wins", "latest-wins")
```

## Manejo de Conflictos

| Estrategia | Descripcion |
|------------|-------------|
| asana-wins | Siempre toma datos de Asana |
| trilium-wins | Siempre toma datos de Trilium |
| latest-wins | Toma el mas reciente |
| manual | Pide confirmacion |

## Tareas Tecnicas

| Task | Descripcion | Estimacion |
|------|-------------|------------|
| T-001 | Crear clase AsanaClient | 2h |
| T-002 | Crear clase TriliumClient | 2h |
| T-003 | Implementar sync Asana->Trilium | 4h |
| T-004 | Implementar sync Trilium->Asana | 4h |
| T-005 | Agregar manejo de conflictos | 2h |
| T-006 | Agregar logs y errores | 1h |
| T-007 | Testing y ajustes | 3h |

**Total estimado:** 18 horas

---

*Last updated: 2026-02-28*
