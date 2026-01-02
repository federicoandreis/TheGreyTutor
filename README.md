# The Grey Tutor

An interactive Middle Earth-themed chat and quiz app, built with React Native and Expo SDK 54. The Grey Tutor allows users to explore Tolkien lore, ask questions, and test their knowledge with a dynamic quiz mode powered by a Neo4j knowledge graph and LLM-generated questions.

---

## 🚀 Features

- **Journey Map & Gamification:**
  - Interactive SVG-based map of Middle Earth with 8 unlockable regions
  - Gamified progression system: Shire → Bree → Rivendell → Moria → Lothlórien → Rohan → Gondor → Mordor
  - Three journey paths: Fellowship of the Ring, Two Towers, Return of the King
  - Knowledge points earned through quizzes unlock new regions
  - Achievement system with 12 badges from common to legendary rarity
  - Visual progress tracking with completion percentages per region

- **Chat Mode:**
  - Converse with Gandalf about characters, places, events, and lore from Tolkien's world
  - LLM-powered responses with strict adherence to Tolkien lore
  - PathRAG-based knowledge retrieval from the Neo4j graph

- **Quiz Mode:**
  - Adaptive quizzing system that adjusts to student performance
  - Multiple question types: factual, relationship, multiple-choice, synthesis, application
  - Fully LLM-generated immersive questions with Gandalf's narrative voice
  - Student modeling with mastery tracking across topics
  - Quiz completion awards knowledge points and unlocks journey progression

- **Knowledge Graph:**
  - Neo4j-based knowledge graph with Tolkien lore entities and relationships
  - Community detection for topic clustering
  - LLM-assisted deduplication and consolidation

- **Modern UI:**
  - Cross-platform (iOS, Android, Web) with React Native Expo
  - Mobile-friendly, accessible interface with Middle Earth theming
  - Scrollable/zoomable map with region markers and difficulty indicators

---

## 📦 Project Structure

```
thegreytutor/
├── thegreytutor/               # Main application
│   ├── backend/                # FastAPI backend
│   │   └── src/
│   │       ├── main.py         # Application entry point
│   │       ├── api/            # REST API endpoints
│   │       ├── agents/         # Journey Agent & business logic
│   │       ├── services/       # Business logic
│   │       └── core/           # Configuration & utilities
│   └── frontend/               # React Native Expo app
│       └── src/
│           ├── screens/        # UI screens (Chat, Quiz, Journey Map, Profile)
│           ├── components/     # Reusable components (RegionMarker, Map, etc.)
│           ├── store/          # Context-based state management
│           ├── services/       # API clients (journeyApi, authApi)
│           └── navigation/     # React Navigation setup
│
├── src/                        # Root-level React Native components
│   ├── screens/                # Auth, Chat, Learning, Profile screens
│   ├── services/               # API services
│   └── store/                  # Redux slices
│
├── database/                   # PostgreSQL database layer
│   ├── models/                 # SQLAlchemy models (User, Conversation, Journey, Cache)
│   ├── repositories/           # Data access layer
│   ├── migrations/             # Alembic migrations
│   ├── api.py                  # Database API endpoints
│   ├── cli.py                  # Command-line admin tools
│   └── admin.py                # Admin utilities
│
├── kg_queries/                 # Knowledge Graph Querying (GraphRAG)
│   └── scripts/
│       ├── graphrag_retriever.py   # Main retriever with multiple strategies
│       ├── run_pathrag.py          # PathRAG runner with Gandalf LLM
│       ├── cache_manager.py        # Caching system
│       ├── kg_query_utils.py       # Neo4j utilities
│       └── tests/                  # Test suite
│
├── kg_quizzing/                # Adaptive Quizzing System
│   └── scripts/
│       ├── quiz_orchestrator.py    # Quiz session management
│       ├── quiz_session.py         # Session handling
│       ├── question_generation.py  # Question generation engine
│       ├── adaptive_strategy.py    # Adaptive strategy engine
│       ├── llm_question_generation.py  # LLM question generator
│       ├── llm_assessment.py       # LLM answer assessment
│       ├── conversation_history.py # Conversation tracking
│       └── schema_extension.py     # Neo4j schema extensions
│
├── kg_consolidation/           # Knowledge Graph Consolidation
│   └── scripts/
│       ├── import_to_neo4j.py      # Graph import utilities
│       ├── neo4j_fuzzy_duplicates.py   # Duplicate detection
│       ├── llm_group_dedup_decision.py # LLM-based dedup decisions
│       └── llm_node_consolidator.py    # Node consolidation
│
├── docs/                       # Documentation
│   ├── DEVELOPMENT_GUIDE.md    # Development workflow & cache management
│   ├── JOURNEY_INTEGRATION_GUIDE.md  # Journey Agent integration guide
│   └── RESTART_CLEAN.md        # Clean restart procedures
│
├── setup_journey.py            # Initialize journey tables & seed data
├── docker-compose.yml          # Neo4j & PostgreSQL services
├── start_all.ps1               # Windows startup script (with PYTHONPATH config)
├── requirements.txt            # Python dependencies
└── package.json                # Node.js dependencies
```

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker (for Neo4j and PostgreSQL)
- Expo Go app on your mobile device (SDK 54)

### Quick Start

1. **Clone the repo:**
   ```sh
   git clone https://github.com/federicoandreis/TheGreyTutor.git
   cd TheGreyTutor
   ```

2. **Set up environment:**
   ```sh
   cp .env.example .env
   # Edit .env with your configuration (API keys, database credentials)
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   npm install
   ```

4. **Start all services:**
   ```sh
   # Windows PowerShell
   .\start_all.ps1
   
   # Or manually:
   docker-compose up -d                    # Start Neo4j & PostgreSQL
   python -m uvicorn thegreytutor.backend.src.main:app --reload --host 0.0.0.0 --port 8000
   npx expo start
   ```

5. **Scan QR code with Expo Go** to test on your mobile device.

### Database Setup

```sh
# Initialize the database schema
python -m database.cli init

# Create an admin user
python -m database.cli create-user --admin

# Initialize Journey Map with Middle Earth regions
python setup_journey.py

# Import existing data (if available)
python -m database.cli import
```

---

## 🧙 Core Components

### Journey Agent & Gamified Map

- **Journey State Management:** Tracks user progress, knowledge points, and unlocked regions
- **Region Progression System:** 8 Middle Earth regions with prerequisite and knowledge point requirements
- **Achievement System:** 12 achievements from common to legendary rarity
- **Journey Paths:** Three predefined paths (Fellowship, Two Towers, Return of the King)
- **Interactive Map:** SVG-based scrollable/zoomable map with visual progress indicators
- **Region Details:** Modal screens showing unlock requirements, quiz themes, and lore snippets
- **Travel System:** Gandalf-narrated transitions between regions

### Knowledge Graph Querying (kg_queries)

- **PathRAG Implementation:** Path-based retrieval with community detection for comprehensive answers
- **Multiple Retrieval Strategies:** Entity-centric, relationship-aware, hybrid, and path-based
- **Gandalf LLM Integration:** Responses strictly adhere to Tolkien lore with Gandalf's voice
- **Performance Caching:** Both retrieval results and LLM responses are cached

### Adaptive Quizzing System (kg_quizzing)

- **Student Modeling:** Tracks mastery levels, entity familiarity, and question performance
- **Question Strategies:** Adaptive, depth-first, breadth-first, and spiral learning paths
- **LLM Question Generation:** Immersive, narrative-driven questions in Gandalf's voice
- **LLM Assessment:** Evaluates open-ended answers with detailed feedback
- **Conversation History:** Full tracking and export of quiz sessions
- **Journey Integration:** Quiz completion awards knowledge points and unlocks regions

### Knowledge Graph Consolidation (kg_consolidation)

- **Duplicate Detection:** Fuzzy matching on names and aliases
- **Transitive Grouping:** Ensures all related duplicates are merged correctly
- **LLM-Assisted Decisions:** GPT models judge merge decisions as a Tolkien expert
- **Robust Parsing:** Hardened JSON handling with detailed error reporting

### Database Layer (database)

- **User Management:** User accounts, profiles, sessions
- **Journey Tracking:** User journey states, region progress, achievements
- **Conversation Storage:** Full conversation history with parameters
- **Caching:** Response and query caching for performance
- **Migrations:** Alembic-managed schema evolution
- **CLI Tools:** Command-line administration interface

---

## ⚡ Tech Stack

- **Frontend:** React Native + Expo SDK 54, React Navigation v7, Redux Toolkit
- **Backend:** FastAPI + Python, async/await support
- **Databases:** Neo4j (knowledge graph), PostgreSQL (users/conversations)
- **LLM:** OpenAI GPT-4o-mini for question generation, assessment, and chat
- **ORM:** SQLAlchemy with Alembic migrations

---

## ✅ Completed Features

- [x] **Journey Map & Gamification:** Interactive Middle Earth map with 8 regions, 3 paths, and 12 achievements
- [x] **Region Progression:** Knowledge points unlock new regions with prerequisite requirements
- [x] **Adaptive Quizzing:** Full adaptive strategy engine with student modeling
- [x] **LLM Question Generation:** Immersive, narrative-driven questions
- [x] **PathRAG:** Optimized path-based retrieval with community detection
- [x] **Gandalf Persona:** Strict Tolkien lore adherence in all LLM responses
- [x] **Deduplication Pipeline:** Transitive grouping with LLM-assisted decisions
- [x] **Conversation History:** Full tracking, storage, and export capabilities
- [x] **Database Layer:** PostgreSQL with user management, journey tracking, and caching
- [x] **Error Handling:** Hardened JSON parsing and API error reporting
- [x] **Security:** Environment-based secrets, gitignored sensitive data
- [x] **User Authentication:** JWT-based auth with session management

## 🚧 Roadmap

- [ ] **Quiz-Journey Integration:** Connect quiz completion to journey progress and achievements
- [ ] **Leaderboards:** Persistent user scores and rankings
- [ ] **UI/UX Polish:** Animations, transitions, and enhanced theming
- [ ] **Offline Mode:** Local storage for offline learning
- [ ] **Multi-agent System:** Specialized AI agents for different learning aspects
- [ ] **Extended Achievement System:** More achievements, quests, and badges
- [ ] **Neo4j Integration:** Journey Agent integration with knowledge graph communities

---

## 📝 Repo Description

> The Grey Tutor: An interactive Middle Earth chat and quiz app for exploring Tolkien lore. Features a gamified journey map through Middle Earth, Gandalf-themed AI chat with PathRAG knowledge retrieval, adaptive quizzing with LLM-generated questions, and achievement tracking. Built with React Native + Expo, FastAPI, Neo4j, and PostgreSQL.

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request.

---

*"All we have to decide is what to do with the time that is given us."* — Gandalf the Grey

---

## © 2025 Federico Andreis & Contributors
