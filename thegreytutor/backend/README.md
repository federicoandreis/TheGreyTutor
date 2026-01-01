# The Grey Tutor - Backend API

FastAPI backend for The Grey Tutor AI learning platform with Gandalf's wisdom.

---

## 🚀 Quick Start

```powershell
# From project root
cd thegreytutor/backend

# Install dependencies
pip install -r requirements.txt

# Run backend (development)
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or use the root startup script (recommended)
cd ../..
.\start_all.ps1
```

**Backend runs at:** `http://localhost:8000`
**API Docs:** `http://localhost:8000/docs`

---

## 📁 Project Structure

```
backend/
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   └── routes/             # API endpoints
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── chat.py         # Chat endpoints
│   │       ├── session.py      # Quiz session endpoints
│   │       ├── agents.py       # AI agent endpoints
│   │       ├── journey.py      # Journey/gamification endpoints
│   │       ├── health.py       # Health check endpoints
│   │       ├── analytics.py    # Analytics endpoints
│   │       └── cache.py        # Cache management endpoints
│   ├── agents/
│   │   └── journey_agent.py    # Journey Agent implementation
│   ├── services/
│   │   ├── auth_service.py     # Authentication service
│   │   ├── cache.py            # Redis cache service
│   │   └── agent_orchestrator.py  # Multi-agent orchestration
│   ├── core/
│   │   ├── config.py           # Pydantic settings
│   │   └── logging.py          # Structured logging setup
│   ├── database/
│   │   └── connection.py       # Database connection management
│   └── ingestion/
│       └── api_graphrag.py     # GraphRAG ingestion API
│
├── tests/
│   ├── test_auth.py            # ✅ 25/25 tests passing
│   ├── agents/
│   │   ├── test_journey_agent.py
│   │   └── test_journey_agent_simplified.py
│   └── api/
│       └── test_journey_routes.py
│
├── pytest.ini                  # pytest configuration
├── requirements.txt            # Production dependencies
└── README.md                   # This file
```

---

## 🧪 Testing

### Run Tests

```powershell
# All tests
python -m pytest

# With coverage
python -m pytest --cov=src --cov-report=html

# Specific test file
python -m pytest tests/test_auth.py

# Verbose output
python -m pytest -v
```

### Test Status

- ✅ **25/25 backend tests passing**
- ✅ **100% passing rate**
- 📊 Coverage target: 70%+

See [Testing Guide](../../docs/TESTING_GUIDE.md) for detailed information.

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/thegreytutor
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# App Settings
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:8000,http://localhost:19006
```

### Settings Management

Configuration is managed via Pydantic settings in [`src/core/config.py`](src/core/config.py):

```python
from src.core.config import settings

# Access settings
database_url = settings.DATABASE_URL
jwt_secret = settings.JWT_SECRET
```

---

## 📡 API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user
- `PUT /auth/me` - Update user profile
- `PUT /auth/me/password` - Change password

### Journey (`/api/journey`)
- `GET /api/journey/state` - Get user's journey state
- `POST /api/journey/travel` - Travel to a region
- `POST /api/journey/complete-quiz` - Complete quiz in region
- `GET /api/journey/regions` - List all regions
- `GET /api/journey/regions/{name}` - Get region details
- `GET /api/journey/paths` - List journey paths
- `GET /api/journey/achievements` - List achievements

### Quiz Session (`/session`)
- `POST /session` - Create quiz session
- `GET /session/{id}/question` - Get next question
- `POST /session/{id}/answer` - Submit answer
- `GET /session/{id}` - Get session state

### Chat (`/api/chat`)
- `POST /api/chat` - Send chat message (Gandalf AI)

### Health (`/health`)
- `GET /health` - Health check
- `GET /health/db` - Database health
- `GET /health/redis` - Redis health

### Cache (`/cache`)
- `GET /cache/stats` - Get cache statistics
- `DELETE /cache/clear` - Clear cache

**Interactive API Docs:** `http://localhost:8000/docs`

---

## 🏗️ Architecture

### Request Flow

```
Client Request
    ↓
FastAPI App (main.py)
    ↓
API Route (/api/routes/)
    ↓
Service Layer (/services/)
    ↓
Database / External API
```

### Key Components

**Journey Agent** (`agents/journey_agent.py`)
- Manages user progression through Middle Earth
- Calculates knowledge points
- Unlocks regions and achievements
- Provides Gandalf-narrated transitions

**Auth Service** (`services/auth_service.py`)
- JWT token generation and validation
- Password hashing with Argon2
- Refresh token management

**Cache Service** (`services/cache.py`)
- Redis-based caching
- LLM response caching
- Query result caching

**Agent Orchestrator** (`services/agent_orchestrator.py`)
- Coordinates multiple AI agents
- Manages context between agents
- (Currently stub - needs implementation)

---

## 🔐 Security

### Authentication Flow

1. User registers → Password hashed with Argon2
2. User logs in → JWT access token (15 min) + refresh token (7 days)
3. Protected endpoints → Bearer token validation
4. Token expires → Refresh using refresh token
5. Logout → Token invalidated

### Security Features

- ✅ Argon2 password hashing
- ✅ JWT with short expiration
- ✅ Refresh token rotation
- ✅ CORS configuration
- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ⏳ Rate limiting (TODO)
- ⏳ API versioning (TODO)

---

## 📊 Database

### Migrations

```powershell
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Database Models

Located in `../../database/models/`:

- `User` - User accounts and profiles
- `MiddleEarthRegion` - Journey map regions
- `JourneyPath` - Predefined journey paths
- `UserJourneyProgress` - Per-region progress tracking
- `UserJourneyState` - Global journey state
- `Achievement` - Achievement definitions
- `Conversation` - Chat history
- `Cache` - Response caching

---

## 🧩 Dependencies

### Core
- `fastapi==0.115.6` - Web framework
- `uvicorn==0.34.0` - ASGI server
- `pydantic==2.10.4` - Data validation
- `pydantic-settings==2.7.1` - Settings management

### Database
- `sqlalchemy==2.0+` - ORM
- `asyncpg==0.30.0` - PostgreSQL driver
- `alembic==1.14.0` - Migrations
- `redis==5.2.0` - Cache

### AI/LLM
- `openai==1.58.1` - OpenAI API
- `langchain==0.3.15` - LLM orchestration
- `tiktoken==0.8.0` - Token counting

### Security
- `passlib==1.7.4` - Password hashing
- `python-jose==3.3.0` - JWT handling
- `cryptography==46.0.0` - Cryptographic functions

### Testing
- `pytest==8.3.4` - Test framework
- `pytest-cov==7.0.0` - Coverage reports
- `pytest-asyncio==1.3.0` - Async test support

---

## 🐛 Debugging

### Enable Debug Logging

```python
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

### View Logs

```powershell
# Backend logs are output to console
# Structured JSON logs when DEBUG=false
```

### Common Issues

**Backend won't start:**
```powershell
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F
```

**Database connection errors:**
```powershell
# Check Docker containers are running
docker ps

# Restart PostgreSQL
docker-compose restart postgres
```

**Import errors:**
```powershell
# Ensure PYTHONPATH is set (start_all.ps1 does this)
$env:PYTHONPATH="F:\Varia\2025\thegreytutor"
python -m uvicorn thegreytutor.backend.src.main:app --reload
```

---

## 📚 Related Documentation

- [Testing Guide](../../docs/TESTING_GUIDE.md) - Comprehensive testing documentation
- [Development Guide](../../docs/DEVELOPMENT_GUIDE.md) - Daily development workflow
- [Journey Integration Guide](../../docs/JOURNEY_INTEGRATION_GUIDE.md) - Journey Agent details
- [Production Build Guide](../../docs/PRODUCTION_BUILD_GUIDE.md) - Production deployment
- [Codebase Assessment](../../docs/CODEBASE_ASSESSMENT_2025.md) - Project overview

---

## 🤝 Contributing

### Adding a New Endpoint

1. Create route in `src/api/routes/`
2. Add business logic to `src/services/`
3. Write tests in `tests/`
4. Update this README
5. Run tests: `python -m pytest`
6. Submit PR to `dev` branch

### Code Style

- Follow PEP 8
- Use type hints
- Document with docstrings
- Keep functions small and focused

---

## © 2025 The Grey Tutor Team
