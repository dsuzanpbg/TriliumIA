# Planning Obligatorio

## IMPORTANCIA

**Esta regla es obligatoria.** Antes de ejecutar cualquier tarea o código, se debe crear una hoja/ruta de planificación.

---

## Por qué Planificar

1. **Evitar errores costosos** - Un plan bien escrito previene errores de implementación
2. **Identificar dependencias** - Saber qué debe hacerse antes
3. **Evaluar alternativas** - Considerar diferentes enfoques
4. **Estimar esfuerzo** - Saber cuánto tiempo tomara
5. **Documentar decisiones** - Registro de por qué se eligió una aproximación

---

## Pasos de Planificación

### 1. Análisis del Problema
- ¿Qué se necesita resolver?
- ¿Cuáles son los requisitos?
- ¿Qué restricciones existen?

### 2. Investigación
- ¿Qué soluciones existen?
- ¿Qué herramientas están disponibles?
- ¿Qué ya existe en el proyecto?

### 3. Diseño de Solución
- ¿Cómo se resuelve el problema?
- ¿Qué componentes se necesitan?
- ¿Cómo se integran?

### 4. Identificación de Riesgos
- ¿Qué puede fallar?
- ¿Qué dependencias son críticas?
- ¿Qué pasa si algo no funciona?

### 5. Plan de Ejecución
- Pasos específicos a seguir
- Orden de las tareas
- Puntos de verificación

### 6. Verificación
- ¿Cómo se sabe que funciona?
- ¿Qué pruebas se necesitan?
- ¿Cuáles son los criterios de éxito?

---

## Formato de Documento de Planificación

```markdown
# Plan: [Nombre de la tarea]

## Objetivo
[Descripción clara de lo que se quiere lograr]

## Análisis
### Requisitos
- Requisito 1
- Requisito 2

### Restricciones
- Restricción 1
- Restricción 2

## Solución Propuesta
[Descripción de la solución]

### Componentes
- Componente 1
- Componente 2

### Alternativas Consideradas
- Alternativa 1: [Por qué se descarto]
- Alternativa 2: [Por qué se descarto]

## Riesgos
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Riesgo 1 | Alta | Alto | Mitigación |

## Plan de Ejecución
1. [ ] Paso 1
2. [ ] Paso 2
3. [ ] Paso 3

## Verificación
- [ ] Criterio 1
- [ ] Criterio 2

##估计
- Tiempo estimado: X horas
- Complejidad: Alta/Media/Baja
```

---

## Cuándo no Planificar

| Caso | Acción |
|------|--------|
| Bug crítico en producción | Fix rápido y deploy |
| Tarea trivial (< 15 min) | Ejecutar directamente |
| Cambios cosméticos | Ejecutar directamente |

---

## Regla Crítica

**NO EJECUTAR hasta tener el plan escrito.**

Si el plan tiene vacíos o incertidumbres, señalar这些问题 y pedir clarificación antes de proceder.

---

*Last updated: 2026-03-02*
