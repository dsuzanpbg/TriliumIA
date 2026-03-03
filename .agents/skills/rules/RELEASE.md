# Release - Proceso de lanzamiento

## Flujo de release

```
develop → PR → code review → merge → testing → staging → production
```

## Ramas

| Rama | Purpose | Protected |
|------|---------|-----------|
| main | Produccion | Si |
| develop | Desarrollo | Si |
| feature/* | Nuevas features | No |
| bugfix/* | Fixes | No |
| release/* | Preparacion de release | No |

## Pasos para crear un release

### 1. Preparacion

```bash
# Actualizar develop
git checkout develop
git pull origin develop

# Crear rama de release
git checkout -b release/v1.2.0
```

### 2. Versionado

Usar Semantic Versioning: `MAJOR.MINOR.PATCH`

- MAJOR: Cambios incompatibles
- MINOR: Nuevas funcionalidades compatibles
- PATCH: Bug fixes

```bash
# Actualizar version en config o pyproject.toml
# Ejemplo: 1.2.0
```

### 3. Testing

Ejecutar tests:
```bash
pytest tests/ -v --cov=src
```

Verificar coverage:
```bash
pytest tests/ --cov=src --cov-fail-under=80
```

### 4. Build

```bash
# Construir Docker
docker build -t pbg-ms-service:v1.2.0 .

# Probar localmente
docker-compose up -d
```

### 5. Merge a main

```bash
# Merge a main
git checkout main
git merge release/v1.2.0

# Tag
git tag -a v1.2.0 -m "Release v1.2.0"

# Push
git push origin main --tags
```

### 6. Deploy

```bash
# Deploy a produccion
# (segun infraestructura)
./deploy.sh production v1.2.0
```

### 7. Merge back a develop

```bash
git checkout develop
git merge main
git push origin develop
```

## Checklist pre-release

- [ ] Tests pasan
- [ ] Coverage >= 80%
- [ ] No hay errores en Sentry
- [ ] Documentacion actualizada
- [ ] Changelog actualizado
- [ ] Version actualizada
- [ ] Build exitoso
- [ ] Tests en staging pasan

## Changelog

Formato:

```markdown
## [1.2.0] - 2026-03-03

### Added
- Nueva funcionalidad X

### Changed
- Optimizacion Y

### Fixed
- Bug en Z

### Removed
- Feature deprecated
```

## Rollback

Si hay problemas en produccion:

```bash
# Revertir a tag anterior
git revert HEAD
git push origin main

# O desplegar version anterior
./deploy.sh production v1.1.0
```

## Comunicacion

- Notificar al equipo
- Actualizar estado en Asana
- Documentar en release notes
