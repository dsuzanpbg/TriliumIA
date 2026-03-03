# Planning - Proyectos

Este directorio contiene las planeaciones de proyectos en formato YAML.

## Estructura

```
planning/
├── README.md                    # Este archivo
└── projects/                    # Proyectos
    ├── pbg-microservices.yml   # Proyecto PBG Microservices (17 tareas)
    ├── toolkits-ocr.yml        # Proyecto Toolkits OCR (22 tareas)
    └── ejemplo.yml              # Archivo de ejemplo
```

## Estructura YAML

Las tareas usan formato `1.1`, `1.2`, `1.3` (numero.tarea):
- La `section` se convierte en **tarea padre** en Asana
- Las tareas individuales son **subtareas**
- El CLI busca primero en `planning/projects/`

## Proyectos actuales

| Proyecto | Archivo | Tareas | Secciones | Estado |
|---------|--------|--------|------------|--------|
| PBG Microservices | pbg-microservices.yml | 17 | 4 | Importado |
| Toolkits OCR | toolkits-ocr.yml | 22 | 5 | Importado |
| IT Ticket System | it-ticket-system.yml | 18 | 6 | Pendiente |

## Como agregar un nuevo proyecto

1. Crear archivo en `planning/projects/<nombre-proyecto>.yml`
2. Usar la estructura del ejemplo `ejemplo.yml`
3. Importar a Asana usando el CLI

## Importar a Asana

```bash
# Desde la carpeta Scripts/Python
cd Scripts/Python

# Ver proyectos disponibles
python cli.py list

# Analizar (dry-run)
python cli.py asn -y ../planning/projects/pbg-microservices.yml

# Ejecutar import
python cli.py asn -y ../planning/projects/pbg-microservices.yml --execute
```

## Reglas

Ver `.agents/skills/rules/YAML_STRUCTURE.md` para la documentación completa.
