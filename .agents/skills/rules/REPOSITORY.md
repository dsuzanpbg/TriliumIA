# Repository Rules

## Git Submodules

Cada microservicio es un repositorio independiente.

## Estructura de Repos

```
Organizacion/
├── PBGMicroServices/           # Repo principal con submodules
│   ├── src/
│   │   └── services/
│   │       ├── pbg-ms-email/   # Submodule
│   │       └── pbg-ms-xxx/     # Submodule
│   └── .gitmodules
│
└── PBGroup-Tech/               # Organizacion para servicios
    ├── pbg-ms-email.git
    ├── pbg-ms-pbgpro.git
    └── pbg-ms-xxx.git
```

## Comandos

### Clonar con submodules

```bash
git clone --recurse-submodules git@github.com:org/repo.git

# O si ya clonaste
git submodule update --init --recursive
```

### Agregar nuevo servicio

```bash
# 1. Crear repo en GitHub
gh repo create pbg-ms-myservice --public

# 2. Agregar como submodule
git submodule add git@github.com:PBGroup-Tech/pbg-ms-myservice.git src/services/pbg-ms-myservice

# 3. Commit
git add -A
git commit -m "feat: add pbg-ms-myservice as submodule"
```

### Actualizar submodule

```bash
cd src/services/pbg-ms-email
git add -A
git commit -m "fix: bug fix"
git push

# Actualizar referencia en repo principal
cd ../..
git add src/services/pbg-ms-email
git commit -m "chore: update pbg-ms-email submodule"
git push
```

### Pull con submodules

```bash
git pull --recurse-submodules

# O solo submodules
git submodule update --remote
```

## Rama principal

- **main** - Rama principal de producción
- **develop** - Rama de desarrollo (si aplica)

## Convenciones de Commits

Usar conventional commits:

```
feat: nueva funcionalidad
fix: correccion de bug
docs: documentacion
refactor: refactorizacion
test: tests
chore: mantenimiento
```

Ejemplos:
```
feat: add pbg-ms-email service
fix: resolve connection timeout
docs: update API documentation
```

## Protected Branches

- main: requiere PR para merge
- puede requerir 1 approval mínimo

## Code Review

- Todos los PRs deben ser revisados
- Verificar que pasa los tests
- Verificar que tiene coverage adecuado
