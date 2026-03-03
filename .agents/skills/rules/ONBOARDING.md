# Onboarding - Incorporacion de nuevos miembros

## Objetivo

Asegurar que nuevos miembros del equipo puedan configurarse rapidamente y empezar a contribuir.

## Primeros pasos

### 1. Acceso a repositorios

- GitHub: Solicitar acceso a la organizacion
- Repo principal: `PBGMicroServices`
- Repos de servicios: `PBGroup-Tech`

### 2. Herramientas requeridas

| Herramienta | Version minima | Uso |
|------------|---------------|-----|
| Python | 3.11 | Desarrollo |
| Docker | Latest | Containerizacion |
| Git | 2.x | Control de versiones |
| VS Code | Latest | Editor (recomendado) |

### 3. Configuracion del entorno

```bash
# Clonar repositorio
git clone git@github.com:PBGroup-Tech/PBGMicroServices.git
cd PBGMicroServices

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar pre-commit hooks
pre-commit install
```

### 4. Docker

```bash
# Verificar instalacion
docker --version
docker-compose --version

# Levantar infraestructura local
docker-compose -f infra/docker-compose/docker-compose.yml up -d
```

### 5. Configurar IDE

Instalar extensiones recomendadas:
- Python
- Pylance
- Docker
- GitLens

Configurar settings.json:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

## Estructura del proyecto

```
PBGMicroServices/
├── docs/                    # Documentacion
├── src/
│   ├── services/           # Microservicios (submodules)
│   └── templates/          # Plantillas
├── infra/                  # Infraestructura
│   ├── docker-compose/
│   ├── nginx/
│   ├── prometheus/
│   └── grafana/
├── .opencode/              # Configuracion AI
└── .github/               # Workflows
```

## Primer tarea recomendada

1. Leer `docs/NOMENCLATURA.md` para convenciones
2. Leer `docs/ARQUITECTURA.md` para entender el sistema
3. Hacer un cambio menor (fix typo, docs)
4. Crear PR y esperar review

## Checklist de setup

- [ ] Acceso a GitHub
- [ ] Python 3.11+ instalado
- [ ] Docker instalado
- [ ] Clonado el repo
- [ ] Entorno virtual creado
- [ ] Dependencias instaladas
- [ ] Pre-commit instalado
- [ ] Docker compose funciona
- [ ] IDE configurado
- [ ] Acceso a Asana (si aplica)
- [ ] Acceso a Sentry (si aplica)

## Recursos

- Documentacion: `docs/`
- Runbook: `docs/RUNBOOK.md`
- Nomenclatura: `docs/NOMENCLATURA.md`
- Arquitectura: `docs/ARQUITECTURA.md`
