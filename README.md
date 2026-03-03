# TriliumIA

Herramienta para importar tareas desde archivos YAML a Asana y Trilium Notes.

## Caracteristicas

- Importacion de YAML a Asana (REST API)
- Importacion a Trilium Notes (ETAPI)
- Estructura padre/subtareas en Asana
- Soporte para secciones Agile (To Do, In Progress, Done)
- CLI con modo interactivo y TUI

## Estructura del Proyecto

```
/
├── .agents/                      # Configuracion para IAs
│   └── skills/
│       ├── SKILL.md
│       └── rules/
│           ├── ADDITIONAL_TOOLS.md
│           ├── AGILE.md              # Metodologia SCRUM
│           ├── CONVENTIONS.md        # Convenciones de codigo
│           ├── DDD.md                # Domain-Driven Design
│           ├── ERROR_HANDLING.md     # Manejo de errores
│           ├── ESTIMATIONS.md       # Guia de estimaciones
│           ├── OBSERVABILITY.md      # Logging, metrics, monitoreo
│           ├── ONBOARDING.md        # Incorporacion de nuevos miembros
│           ├── PLANNING.md          # Guia de planificacion
│           ├── RELEASE.md           # Proceso de lanzamiento
│           ├── REPOSITORY.md        # Git submodules
│           ├── TEMPLATES.md
│           ├── UNIT_TESTING.md      # Testing unitario
│           ├── YAML_EXAMPLE.yml
│           └── YAML_STRUCTURE.md
│
├── Scripts/                      # Scripts de integracion
│   ├── Python/                  # CLI tool
│   │   ├── adapters/            # Asana y Trilium adapters
│   │   ├── cli.py              # CLI principal
│   │   ├── tui.py              # Interfaz TUI
│   │   └── config.json         # Configuracion
│   │
│   └── Trilium/                # Scripts legacy
│
├── planning/                     # Proyectos planeados
│   ├── README.md
│   └── projects/
│       ├── pbg-microservices.yml
│       ├── toolkits-ocr.yml
│       ├── it-ticket-system.yml
│       └── ejemplo.yml
│
└── README.md
```

## Uso Rapido

### CLI

```bash
cd Scripts/Python

# Ver proyectos disponibles
python cli.py list

# Analizar (dry-run)
python cli.py asn -y ../planning/projects/pbg-microservices.yml

# Ejecutar import
python cli.py asn -y ../planning/projects/pbg-microservices.yml --execute
```

### Configuracion

Editar `config.json`:

```json
{
  "asana": {
    "token": "tu_token",
    "workspace_gid": "tu_workspace_id",
    "team_gid": "tu_team_id"
  },
  "person_map": {
    "P1": "email@tuempresa.com",
    "P2": "email2@tuempresa.com"
  }
}
```

## Estructura YAML

Las tareas usan formato `1.1`, `1.2`, etc. La `section` se convierte en tarea padre:

```yaml
project:
  name: "Mi Proyecto"

tasks:
  - name: "1.1 Primera tarea"
    section: "Infraestructura"
    assignee: "P1"
    due_date: "2026-03-01"
    notes: |
      Descripcion en Markdown
```

Resultado en Asana:
```
To Do
├── [PADRE] Infraestructura
│   ├── 1.1 Primera tarea
│   └── 1.2 Segunda tarea
```

## Reglas del Proyecto

1. **Sin emojis** - texto plano siempre
2. **Idioma** - Espanol para docs, Ingles para codigo
3. **DDD** - Lenguaje Ubicuo por dominio

---

*Last updated: 2026-03-03*
