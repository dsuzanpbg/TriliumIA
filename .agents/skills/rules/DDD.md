# Domain-Driven Design (DDD)

## Overview

Este proyecto utiliza Domain-Driven Design (DDD) para estructurar el código y la arquitectura.

## Regla Principal: Lenguaje Ubícuo

**Regla**: Usar términos consistentes y específicos dentro de cada dominio/contexto.

### Ejemplo de Lenguaje Ubícuo

| Contexto/Dominio | Termino | Significado |
|------------------|---------|-------------|
| Planeación | OP | Orden de Proceso de Planificación |
| Producción | OP | Orden de Proceso de Fabricación |
| Ventas | OP | Orden de Proceso de Pedido |
| Finanzas | OP | Orden de Proceso de Comprobante |

## Conceptos DDD

### Contexto Delimitado (Bounded Context)

Cada dominio tiene límites claros donde los términos tienen significado específico.

```
+------------------+------------------+------------------+
|    Dominio A     |    Dominio B     |    Dominio C     |
|   (Ventas)      |   (Produccion)  |   (Finanzas)    |
+------------------+------------------+------------------+
| - Pedido        | - Orden          | - Transaccion   |
| - Cliente       | - Maquina        | - Cuenta        |
| - Precio        | - Material       | - Balance       |
+------------------+------------------+------------------+
```

### Entidades vs Value Objects

#### Entidad
- Tiene identidad única
- Se diferencia por su ID
- Ejemplo: Usuario, Pedido, Producto

#### Value Object
- No tiene identidad
- Se define por sus atributos
- Ejemplo: Direccion, Dinero, Fecha

### Agregados (Aggregates)

Grupo de objetos relacionados que se tratan como una unidad.

```
         [Raiz de Agregado]
              (Pedido)
                   |
    +--------------+--------------+
    |              |              |
 [Linea]       [Linea]       [Cliente]
 (Entidad)    (Entidad)     (Entidad)
```

## Estructura de Proyecto DDD

```
src/
├── domain/
│   ├── planeacion/
│   │   ├── entities/
│   │   ├── value-objects/
│   │   ├── services/
│   │   └── repositories/
│   ├── produccion/
│   │   ├── entities/
│   │   ├── value-objects/
│   │   ├── services/
│   │   └── repositories/
│   └── common/
│       ├── entities/
│       ├── value-objects/
│       └── services/
├── application/
│   ├── use-cases/
│   └── dto/
├── infrastructure/
│   ├── persistence/
│   └── external-services/
└── presentation/
    ├── api/
    └── ui/
```

## Aplicacion en Este Proyecto

### Como Usar DDD

1. **Identificar el Dominio**: Determinar a qué contexto pertenece la funcionalidad
2. **Usar Lenguaje Ubícuo**: Definir términos claros para ese dominio
3. **Crear Entidades**: Si tiene identidad única
4. **Crear Value Objects**: Si solo importa sus atributos
5. **Definir Agregados**: Agrupar entidades relacionadas

### Ejemplo Practico

#### Dominio: Ventas
```typescript
// Entity: tiene ID único
interface Pedido {
  id: string;
  cliente: Cliente;
  items: LineaPedido[];
  fecha: Date;
}

// Value Object: sin ID, definidos por atributos
interface Direccion {
  calle: string;
  ciudad: string;
  pais: string;
}

interface Dinero {
  monto: number;
  moneda: string;
}
```

#### Dominio: Produccion
```typescript
// Mismo nombre "Orden" pero diferente significado
interface OrdenFabricacion {
  id: string;
  producto: Producto;
  cantidad: number;
  prioridad: Prioridad;
}
```

## Beneficios

- Comunicación clara entre equipos
- Código organizado por dominio
- Facilita el mantenimiento
- Escalabilidad
- Separación de responsabilidades

---

*Last updated: 2026-02-28*
