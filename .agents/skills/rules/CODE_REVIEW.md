# Code Review

## Proposito

- Mantener calidad de codigo
- Compartir conocimiento
- Prevenir bugs
- Estandarizar

## Checklist para reviewer

### General

- [ ] Codigo compila sin errores
- [ ] Tests pasan
- [ ] Coverage no decreased
- [ ] No hay print() o debug
- [ ] No hay secrets hardcodeados

### Estilo

- [ ] Sigue convenciones del proyecto
- [ ] Nombres claros y descriptivos
- [ ] Funciones pequenas (< 50 lines)
- [ ] DRY - No duplicar codigo
- [ ] Comentarios cuando necessario

### Seguridad

- [ ] Input validado
- [ ] SQL injection prevvenido
- [ ] Secrets no en codigo
- [ ] Autenticacion/Authorization correcta

### Testing

- [ ] Tests para nueva funcionalidad
- [ ] Coverage adequate (> 80%)
- [ ] Tests siguen naming convention
- [ ] Arrange-Act-Assert

### Documentacion

- [ ] Docstrings en funciones publicas
- [ ] README actualizado si es necesario
- [ ] Comments para logica compleja

## Feedback

### Bueno

- Preguntas en lugar de demandas
- Sugerencias con ejemplo
- Agradecer buen trabajo

```python
# Ejemplo de buen feedback
"Buena idea usar cache aqui. 
Que te parece usar Redis en vez de in-memory?"
```

### Evitar

- Comentarios personales
- Críticas a la persona
- Ordenes sin explicación

## Para el autor

- Responder a todos los comentarios
- Explicar si no estas de acuerdo
- Agradecer los reviews
- No tomar personal
