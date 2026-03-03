# SKILL: Unit Testing

> **When to use**: Writing unit tests for a PBG microservice
> **CRITICAL**: Always follow docs/UNIT_TESTS.md for full rules

## Coverage Requirements (MANDATORY)

| Service | Min Coverage | Hard Requirement |
|---------|--------------|-------------------|
| pbg-ms-email | **85%** | YES - PR rejected if below |
| pbg-ms-pbgpro | **80%** | YES - PR rejected if below |
| pbg-ms-ord | **80%** | YES - PR rejected if below |
| pbg-ms-shopify | **80%** | YES - PR rejected if below |
| pbg-ms-reports | **80%** | YES - PR rejected if below |
| pbg-ms-utils | **75%** | YES - PR rejected if below |

## Test Structure

```
src/services/<servicio>/tests/
├── __init__.py
├── test_models.py          # Pydantic models
├── test_services.py        # Business logic
├── test_integration.py     # End-to-end flows
└── conftest.py            # Shared fixtures (if needed)
```

## Naming Convention

```python
# ✅ CORRECT
def test_email_request_validation_fails_with_invalid_email():
def test_ord_generator_returns_error_when_template_missing():
def test_health_endpoint_returns_200():

# ❌ WRONG
def test_email():
def test_ord():
def test_failed():
```

## What to Test

### 1. Pydantic Models (ALWAYS)
- Required fields validation
- Optional fields defaults
- Email/Enum validation
- Serialization

```python
def test_email_request_requires_to_field():
    with pytest.raises(ValidationError):
        EmailRequest(subject="Test", body="Body")

def test_email_request_accepts_valid_email():
    request = EmailRequest(to="user@example.com", ...)
    assert request.to == "user@example.com"
```

### 2. Business Logic (ALWAYS)
- Calculations
- Transformations
- Rules

```python
def test_february_has_28_days_in_2023():
    dt = datetime(2023, 2, 1)
    next_month = datetime(2023, 3, 1)
    assert (next_month - dt).days == 28
```

### 3. Events (ALWAYS)
- Event structure
- Routing keys
- Versioning

```python
def test_email_queued_event_has_correct_routing_key():
    event = EmailQueuedV1(...)
    assert event.routing_key == "pbg.email.queued.v1"
```

### 4. API Endpoints (ALWAYS)
- Health checks
- Input validation
- Response codes

```python
def test_health_endpoint_returns_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
```

## What NOT to Test

| ❌ Don't Test | ✅ Instead |
|-------------|-----------|
| FastAPI internals | Mock it |
| RabbitMQ/Redis real connections | Mock it |
| Real SMTP | Mock SMTP client |
| Real files | Mock `open()` or use `tmp_path` |
| External APIs | Mock requests |

```python
# ❌ WRONG - Real dependency
def test_send_email():
    client = SMTPClient()
    result = client.send(...)  # Real email!

# ✅ CORRECT - Mock
@patch("src.services.smtp.SMTPClient.send")
def test_send_email(mock_send):
    mock_send.return_value = {"message_id": "123"}
    result = send_email(...)
    assert result["message_id"] == "123"
```

## Arrange-Act-Assert (MANDATORY)

```python
def test_something():
    # 1. ARRANGE - Prepare data
    request = EmailRequest(to="test@example.com", ...)
    
    # 2. ACT - Execute action
    result = service.process(request)
    
    # 3. ASSERT - Verify
    assert result.success is True
    assert result.email_id is not None
```

## One Concept Per Test

```python
# ❌ WRONG - Multiple assertions
def test_email():
    assert email.to == "a"
    assert email.subject == "b"
    assert email.body == "c"

# ✅ CORRECT - One per test
def test_email_request_stores_recipient():
    assert email.to == "a"

def test_email_request_stores_subject():
    assert email.subject == "b"
```

## Required Fixtures

```python
@pytest.fixture
def valid_email_request():
    return EmailRequest(
        to="test@example.com",
        subject="Test",
        body="Body"
    )

@pytest.fixture
def mock_rabbitmq():
    with patch("src.services.rabbitmq.get_connection") as mock:
        yield mock.return_value
```

## Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-fail-under=80

# Coverage report
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

# Single file
pytest tests/test_models.py -v
```

## Checklist Before Commit

- [ ] All tests pass (`pytest -v`)
- [ ] Coverage >= minimum required
- [ ] No `print()` or debug code
- [ ] Correct naming convention
- [ ] One concept per test
- [ ] External dependencies mocked
- [ ] Tests are deterministic (same result always)

## CI/CD

Tests run automatically via `.github/workflows/tests.yml`. If coverage is below minimum, the build fails.

## Reference

- Full rules: `docs/UNIT_TESTS.md`
- Examples: `src/services/pbg-ms-email/tests/`
- Examples: `src/services/pbg-ms-ord/tests/`
