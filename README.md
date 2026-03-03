# Trilium Project

Personal project management workspace with scripts and integrations.

## Estructura del Proyecto

```
/
├── .agents/                    # Configuracion para IAs
│   └── skills/
│       ├── SKILL.md
│       └── rules/
│           ├── AGILE.md        # Metodologia SCRUM
│           ├── CONVENTIONS.md  # Convenciones de codigo
│           ├── DDD.md          # Domain-Driven Design
│           └── TEMPLATES.md    # Referencia de templates
│
├── Scripts/                     # Scripts de integracion
│   └── Trilium/
│       ├── Asana-Trilium.js              # Script basico
│       └── Asana-Trilium-Bidirectional.js # Script completo
│
├── _docs/                      # Documentacion
│   ├── templates/
│   │   ├── TEMPLATE-TASK.md
│   │   ├── TEMPLATE-ROADMAP.md
│   │   ├── TEMPLATE-BUG-REPORT.md
│   │   ├── TEMPLATE-USER-STORY.md
│   │   └── TEMPLATE-MEETING-NOTES.md
│   └── scripts/
│       └── SCRIPTS.md
│
└── README.md                   # Este archivo
```

## Quick Start

### Para usar en Trilium:

1. Copia el script que necesites a tu carpeta de scripts de Trilium
2. Crea una nueva nota en Trilium
3. Agrega los labels de configuracion
4. Ejecuta el script

### Configuracion de Asana

Labels requeridos en la nota del script:
```
#asanaToken=tu_token_de_asana
#asanaWorkspaceGid=tu_workspace_id
```

## Reglas del Proyecto

1. **Sin emojis** - texto plano siempre
2. **Idioma** - Espanol para docs, Ingles para codigo
3. **DDD** - Lenguajo Ubicuo por dominio

---

*Last updated: 2026-02-28*
