# Database

## ORM

Usar SQLAlchemy o Tortoise ORM.

## Modelos

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## Pydantic Models

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

## Migraciones

```bash
# Crear migracion
alembic revision --autogenerate -m "add users table"

# Migrar
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Conexion

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:pass@localhost:5432/db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Transacciones

```python
def create_user(db: Session, user: UserCreate):
    db_user = User(email=user.email, name=user.name)
    db.add(db_user)
    db.commit()  # Atomico
    db.refresh(db_user)
    return db_user
```

## Indices

```python
# Para busquedas frecuentes
email = Column(String(255), index=True)

# Para uniques
email = Column(String(255), unique=True, index=True)

# Compuesto
__table_args__ = (
    Index('idx_user_email_status', 'email', 'status'),
)
```
