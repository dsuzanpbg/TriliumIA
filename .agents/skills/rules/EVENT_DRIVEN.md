# Event-Driven Architecture

## Eventos

### Estructura

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BaseEvent(BaseModel):
    event_id: str
    event_type: str
    routing_key: str
    timestamp: datetime
    version: str = "v1"

class OrderCreatedEvent(BaseEvent):
    event_type: str = "order.created"
    order_id: str
    customer_id: str
    total: float
    items: list
```

### Routing key

```
pbg.<domain>.<event>.<version>
```

Ejemplos:
```
pbg.order.created.v1
pbg.email.queued.v1
pbg.payment.completed.v1
```

## RabbitMQ

### Publisher

```python
import pika
import json

class RabbitMQPublisher:
    def __init__(self, host: str, queue: str):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host)
        )
        self.channel = self.connection.channel()
        self.exchange = 'pbg.ex.topic'
        
    def publish(self, routing_key: str, event: dict):
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=json.dumps(event),
            properties=pika.BasicProperties(
                content_type='application/json',
                delivery_mode=2  # Persistent
            )
        )
```

### Consumer

```python
import pika

class RabbitMQConsumer:
    def __init__(self, queue: str, callback):
        self.queue = queue
        self.callback = callback
        
    def start(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue,
            on_message_callback=self._on_message
        )
        self.channel.start_consuming()
        
    def _on_message(self, channel, method, properties, body):
        event = json.loads(body)
        try:
            self.callback(event)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
```

## Dead Letter Queue

```python
# Configurar DLQ en el consumer
dlq = 'pbg.dlq.order.created'

# Cuando falla, va a DLQ
```

## Patron CQRS (opcional)

```
Commands (Write) -> Event Store -> Projections (Read)
```

## Mejores practicas

- Siempre versionar eventos
- No mutar eventos
- Usar idempotencia
- Manejar failures con DLQ
- Logging de eventos
