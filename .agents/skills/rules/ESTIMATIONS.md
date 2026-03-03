# Estimaciones - Guia para estimar esfuerzo

## Por que estimar

- Planificar sprints
- Asignar recursos
- Comunicar expectativas
- Mejorar con el tiempo

## Metodos de estimacion

### 1. T-shirt sizes

| Size | Descripcion | Equivalencia |
|------|-------------|--------------|
| XS | Muy pequeno | 1-2 horas |
| S | Pequeno | 2-4 horas |
| M | Mediano | 4-8 horas |
| L | Grande | 1-2 dias |
| XL | Extra grande | 2-4 dias |

### 2. Fibonacci

Secuencia: 1, 2, 3, 5, 8, 13, 21

Mas facil para debates ("por que 5 y no 8?").

### 3. Puntos de historia

- No es horas reales
- Representa complejidad relativa
- Considera incertidumbre

## Factores a considerar

### Complejidad tecnica

- Codigo nuevo vs existente
- Tests requeridos
- Dependencias externas
- Integraciones
- Base de datos

### Complejidad de negocio

- Reglas de negocio complejas
- Excepciones a manejar
- Validaciones
- Permisos/seguridad

### Incertidumbre

- Investigacion necesaria
- Tecnologias nuevas
-scope creep

## Formula simple

```
Estimacion = (Tiempo base) * (1 + Uncertainty factor)
```

| Nivel incertidumbre | Factor |
|---------------------|--------|
| Bajo (ya lo hice antes) | 1.0 |
| Medio (similar pero no igual) | 1.25 |
| Alto (nueva tecnologia) | 1.5 |
| Muy alto (investigacion) | 2.0 |

## Ejemplos

| Tarea | Base | Factor | Estimacion |
|-------|------|--------|------------|
| CRUD basico | 4h | 1.0 | 4h |
| API con auth | 8h | 1.25 | 10h |
| Integracion nueva | 16h | 1.5 | 24h |
| Investigacion IA | 8h | 2.0 | 16h |

## Estimacion en sprints

Capacidad del equipo = suma de puntos en sprint anterior * factor velocidad

| Semana | Puntos capacidad | Completados |
|--------|-----------------|-------------|
| 1 | 20 | 18 |
| 2 | 20 | 22 |
| 3 | 20 | 19 |

Promedio: 20 puntos/sprint

## Checklist para estimar

- [ ] Entiendo el requerimiento?
- [ ] Hay tareas dependientes?
- [ ] Necesita investigacion?
- [ ] Tiene tests existentes?
- [ ] Requiere DB changes?
- [ ] Hay integraciones?
- [ ] Docs requeridos?
- [ ] Tiempo para review?

## Mejores practicas

1. **No estimar solo** - Discutir en equipo
2. **Comparar con tareas similares** - Anchoring
3. **Considerar todo el ciclo** - Dev + tests + docs + review
4. **Agregar buffer** - 20% para imprevistos
5. **Documentar estimacion** - Para mejorar siguiente vez
6. **No estimar en frio** - Primero investigar si hay dudas

## Estimacion por tipo de tarea

| Tipo | Dificultad tipica |
|------|-------------------|
| Bug fix simple | XS - S |
| Bug fix complejo | M - L |
| Nueva feature simple | S - M |
| Nueva feature compleja | L - XL |
| Refactor | M - L |
| Investigacion | L - XL |
| Documentacion | XS - S |
| Code review | S - M |
