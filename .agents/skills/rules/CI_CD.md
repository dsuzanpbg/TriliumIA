# CI/CD - Integracion y Despliegue continuo

## GitHub Actions

### Estructura de workflows

```
.github/
└── workflows/
    ├── test.yml      # Tests
    ├── build.yml    # Build y push Docker
    └── deploy.yml   # Despliegue
```

### test.yml

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Create venv
        run: python -m venv .venv
        
      - name: Install dependencies
        run: |
          .venv/bin/pip install -r requirements.txt
          .venv/bin/pip install pytest pytest-cov
          
      - name: Run tests
        run: .venv/bin/pytest tests/ -v --cov=src --cov-report=xml --cov-fail-under=80
        
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
```

### build.yml

```yaml
name: Build and Push

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
          
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: myorg/my-service
          tags: |
            latest
            ${{ github.sha }}
            
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=myorg/my-service:buildcache
          cache-to: type=registry,ref=myorg/my-service:buildcache,mode=max
```

### deploy.yml

```yaml
name: Deploy

on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app/my-service
            docker-compose pull
            docker-compose up -d
            docker system prune -f
```

## Pipeline basico

```
Push → Lint → Test → Build → Deploy
```

## Secretos requeridos

| Secret | Descripcion |
|--------|-------------|
| DOCKER_USERNAME | Usuario de Docker Hub |
| DOCKER_PASSWORD | Password de Docker Hub |
| HOST | IP o hostname del servidor |
| SSH_KEY | Clave SSH privada |
| SENTRY_DSN | DSN de Sentry para releases |

## Comandos de deployment

```bash
# Produccion
./deploy.sh production

# Staging
./deploy.sh staging

# Rollback
./rollback.sh production v1.0.0
```

## Checklist CI/CD

- [ ] Tests automaticos
- [ ] Coverage automatico
- [ ] Lint/format check
- [ ] Build de Docker
- [ ] Scan de seguridad
- [ ] Despliegue automatico
- [ ] Notificaciones
- [ ] Rollback procedure
