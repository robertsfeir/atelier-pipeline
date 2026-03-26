# Python / FastAPI / SQLAlchemy Reference

Colby reads this when working on backend Python code — routes, services,
models, database, LLM integration.

---

<section id="fastapi-patterns">

## FastAPI Patterns

### Async-First
All route handlers are `async def`. All I/O operations (database, HTTP,
Redis, LLM calls) use async libraries. Never block the event loop.

```python
# GOOD — async all the way
@router.post("/predict")
async def predict(request: StockAnalysisRequest):
    result = await analysis_service.analyze(request)
    return result

# BAD — synchronous DB call blocks the loop
@router.post("/predict")
async def predict(request: StockAnalysisRequest):
    result = db.query(Analysis).filter(...).first()  # blocking!
    return result
```

### Dependency Injection
FastAPI's `Depends()` for session management, auth, config:

```python
from fastapi import Depends
from app.db.session import get_db

@router.get("/{id}")
async def get_analysis(id: str, db: Session = Depends(get_db)):
    ...
```

Dependencies are cached per-request — multiple `Depends(get_db)` in the
same request share the same session.

### Router Organization
One router file per domain in `app/api/routes/`:
- `health.py` — health checks
- `auth.py` — authentication
- `analysis.py` — stock analysis endpoints
- `personas.py` — persona sentiment endpoints

Mount in `main.py` with prefixes:
```python
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
```

### Response Models
Always declare `response_model` on endpoints:
```python
@router.post("/predict", response_model=StockAnalysisResponse)
async def predict(request: StockAnalysisRequest) -> StockAnalysisResponse:
    ...
```
This enforces output shape, filters extra fields, and auto-generates OpenAPI docs.

### Error Handling
Custom exceptions in `app/utils/errors.py` inherit from `MyAppError`.
Global handler in `middleware/error_handler.py` catches and returns JSON:

```python
raise NotFoundError("Analysis")
# → {"error": "Analysis not found", "status_code": 404}
```

Never return raw exception messages to clients. Never catch bare `Exception`
in service code.

</section>

---

<section id="pydantic-v2">

## Pydantic V2 Patterns

### Model Config
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )
    database_url: str = "postgresql://..."
```

### Field Validation
```python
from pydantic import BaseModel, Field, field_validator

class StockAnalysisRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="Ticker")
    timeframe: str = Field(default="1w", pattern=r"^\d+[dwm]$")

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper().strip()
```

### Nullable Types
Use `X | None` (Python 3.10+), not `Optional[X]`:
```python
full_name: str | None = None
```

### Schema Separation
- Request schemas: what the client sends (validated, strict).
- Response schemas: what the API returns (may exclude internal fields).
- DB models: SQLAlchemy ORM (separate from Pydantic).
- Never expose ORM models directly as API responses.

</section>

---

<section id="sqlalchemy-2">

## SQLAlchemy 2.0 + Async Patterns

### Engine & Session
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### Dependency
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Queries (2.0 style)
```python
from sqlalchemy import select

# Single item
stmt = select(Analysis).where(Analysis.id == analysis_id)
result = await db.execute(stmt)
analysis = result.scalar_one_or_none()

# Multiple items
stmt = select(Analysis).where(Analysis.symbol == symbol).order_by(Analysis.created_at.desc())
result = await db.execute(stmt)
analyses = result.scalars().all()
```

### DeclarativeBase (2.0)
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    prediction: Mapped[float] = mapped_column(nullable=False)
```

### Relationship Patterns
```python
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy import ForeignKey

class Analysis(Base):
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="analyses")
    persona_sentiments: Mapped[list["PersonaSentiment"]] = relationship(back_populates="analysis")
```

</section>

---

<section id="alembic-migrations">

## Alembic Migrations

### Commands
```bash
alembic revision --autogenerate -m "add persona columns"  # Generate
alembic upgrade head                                       # Apply all
alembic downgrade -1                                       # Rollback one
alembic history --verbose                                  # View history
alembic current                                            # Current revision
```

### Rules
- Never edit committed migrations that others have applied.
- Always review autogenerated migrations — they can miss renames, data migrations.
- Include both `upgrade()` and `downgrade()` functions.
- Test migrations against a copy of production data shape before deploying.
- For data migrations, use raw SQL in migration files, not ORM models.

</section>

---

<section id="testing-patterns">

## Testing Patterns (Python)

### pytest + httpx for async
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
```

### Fixtures
```python
@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
def mock_llm():
    with patch("app.services.llm_service.LLMService") as mock:
        mock.complete = AsyncMock(return_value="Bullish outlook")
        yield mock
```

### LLM Testing
ALWAYS mock LLM calls. Never hit real APIs in tests:
```python
@pytest.mark.asyncio
async def test_persona_sentiment(mock_llm):
    service = PersonaService(llm=mock_llm)
    result = await service.generate_sentiment(request)
    assert len(result.personas) == 5
    mock_llm.complete.assert_called()
```

</section>

---

<section id="redis-celery-patterns">

## Redis / Celery Patterns

### Cache
```python
import redis.asyncio as redis

client = redis.from_url(settings.redis_url)

async def get_cached(key: str) -> str | None:
    return await client.get(key)

async def set_cached(key: str, value: str, ttl: int = 3600) -> None:
    await client.setex(key, ttl, value)
```

### Celery Tasks (Async Jobs)
For expensive LLM calls that shouldn't block the request:
```python
from celery import Celery

celery_app = Celery("myapp", broker=settings.redis_url)

@celery_app.task
def run_analysis_async(symbol: str, timeframe: str):
    # Long-running LLM analysis
    ...
```

</section>

---

<section id="security-patterns">

## Security Patterns

- Never log API keys, passwords, or PII.
- Parameterized queries only (SQLAlchemy handles this).
- Hash passwords with Argon2id (`argon2-cffi`).
- Rate limit expensive endpoints (LLM calls).
- Validate all input via Pydantic before processing.
- CORS: whitelist specific origins, not `*` in production.
- JWT tokens for auth with short expiry + refresh tokens.

</section>
