# Roadmap: Integracion Asana <-> GitHub

## Objetivo
Mantener tickets de Asana alineados con commits de GitHub.

---

## Fase 1: Conventional Commits + Pre-commit Hook (IMPLEMENTAR)

### Descripcion
Usar conventional commits en los mensajes de commit y un pre-commit hook que:
1. Parsea el mensaje de commit buscando IDs de Asana
2. Valida el formato del commit
3. Opcional: actualiza Asana con el hash del commit

### Formato de Commits

```
<tipo>(<scope>): <descripcion>

[ASANA-123] - opcional al inicio o final
```

**Tipos validos:**
- `feat` - nueva funcionalidad
- `fix` - bug fix
- `docs` - documentacion
- `style` - formateo
- `refactor` - refactoring
- `test` - tests
- `chore` - tareas varias

**Ejemplos:**
```
feat(api): agregar endpoint de usuarios [ASANA-123]
fix(auth): solve login bug ASANA-456
docs: update README
```

### Formato de Branch
```
feature/ASANA-123-descripcion
fix/ASANA-456-bug-login
```

### Archivos a crear
- `.git/hooks/pre-commit` - hook de validacion
- `.commitlintrc.json` - configuracion de conventional commits

---

## Fase 2: Sync Bidireccional (FUTURO - Opcion 4)

### Descripcion
Sincronizacion completa entre Asana y GitHub:

- Custom fields en Asana (Branch, PR, Commit, Estado)
- GitHub Actions que:
  - En push: actualiza Asana con branch, PR, commit
  - En merge: cambia estado de tarea a "Done"
- Opcional: Webhook de Asana para crear branches automaticamente

### Custom Fields en Asana
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| GitHub Branch | Text | Rama actual |
| GitHub PR | URL | Link al Pull Request |
| Commit Hash | Text | Ultimo commit |
| Ultimo Commit | Date | Fecha del ultimo commit |

### Flujo

```
GitHub Push
    |
    v
GitHub Actions
    |
    +-- Extrae ID de Asana del branch/commits
    +-- Actualiza custom fields
    +-- Agrega comentario con cambios
    +-- Si merge a main -> cambia estado a Done
```

---

## Estado Actual

- [x] Fase 1: Planeado
- [ ] Fase 1: Implementar pre-commit hook
- [ ] Fase 1: Configurar commitlint
- [ ] Fase 2: Pendiente
