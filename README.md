# The Grey Tutor

An interactive Middle Earth-themed chat and quiz app, built with React Native and Expo SDK 54. The Grey Tutor allows users to explore Tolkien lore, ask questions, and test their knowledge with a dynamic quiz mode powered by a Neo4j knowledge graph and LLM-generated questions.

---

## 🚀 Features
- **Chat Mode:**
  - Ask about characters, places, events, and lore from Tolkien's world.
  - Instant answers using regex-powered keyword matching.
- **Quiz Mode:**
  - Toggleable quiz experience with multiple choice and free-text questions.
  - LLM-generated questions from Neo4j knowledge graph.
  - Tracks score and provides instant feedback.
- **Modern UI:**
  - Mobile-friendly, clean, and accessible interface.
  - Smooth transitions between chat and quiz.
- **Easy to Extend:**
  - Expand mock Q&A and quiz datasets in `src/services/`.

---

## 📦 Project Structure
```
frontend/
├── src/
│   ├── screens/
│   │   └── chat/ChatScreen-simple.tsx
│   ├── services/
│   │   ├── mockChatDatabase.ts
│   │   └── mockQuizDatabase.ts
│   └── navigation/
│       └── AppNavigator.tsx
├── App.tsx
├── package.json
├── app.json
└── ...
```

---

## 🛠️ Getting Started

### Prerequisites
- Node.js 18+
- Docker (for Neo4j)
- Expo Go app on your mobile device (SDK 54)

### Quick Start
1. **Clone the repo:**
   ```sh
   git clone https://github.com/federicoandreis/TheGreyTutor.git
   cd TheGreyTutor
   ```
2. **Install dependencies:**
   ```sh
   npm install
   ```
3. **Start all services:**
   ```sh
   # Windows PowerShell
   .\start_all.ps1
   
   # Or manually:
   docker-compose up -d                    # Start Neo4j
   python -m uvicorn thegreytutor.backend.src.main:app --reload --host 0.0.0.0 --port 8000
   npx expo start
   ```
4. **Scan QR code with Expo Go** to test on your mobile device.

---

## 🧙 Knowledge Graph & Backend Progress

This repo now includes powerful backend components for knowledge graph management, querying, and deduplication, focused on Tolkien lore. Major improvements include:

### Knowledge Graph Querying (GraphRAG)
- **Optimized PathRAG Implementation:**
  - Path-based retrieval with community detection for comprehensive answers
  - Gandalf-themed LLM integration with strict adherence to Tolkien lore
  - Organized codebase with dedicated test directory and clear documentation
  - Caching for both retrieval results and LLM responses

### Knowledge Graph Deduplication
- **Advanced Deduplication Logic:**
  - Merges suspected duplicate nodes using both names and aliases, with robust handling of lists and strings
  - Transitive closure logic ensures all related duplicates are grouped correctly
- **LLM Integration:**
  - Uses OpenAI's GPT models to judge whether groups of nodes should be merged or kept separate
  - Strict prompt engineering: The LLM is instructed to act as a Tolkien expert and avoid over-merging (e.g., never merges Frodo and Bilbo Baggins)
  - JSON parsing is hardened for reliability, with detailed error reporting
- **Security & Reliability:**
  - All secrets (API keys, etc.) are loaded from environment variables
  - Sensitive and generated data in `input/` and `output/` folders are gitignored
  - Improved error handling for LLM/API failures

---

## ⚡ Tech Stack
- **Frontend:** React Native + Expo SDK 54, React Navigation v7
- **Backend:** FastAPI + Python
- **Database:** Neo4j (knowledge graph), PostgreSQL (users)
- **LLM:** OpenAI GPT-4o-mini for question generation and assessment

## ⚡ Work in Progress
- The app and backend are in active development.
- **Chat Mode**: Fully functional with Gandalf-themed LLM responses.
- **Quiz Mode**: LLM-generated questions from knowledge graph with mixed question types.
- **Knowledge Graph Deduplication**: Robust, LLM-assisted, and production-grade.
- Simple, accessible, and mobile-first UI.

### Roadmap / What’s Next
- [x] **Deduplication pipeline:** Transitive duplicate grouping, robust LLM integration, and strict Tolkien expert prompting.
- [x] **Error handling:** Hardened JSON parsing and API error reporting.
- [x] **Security:** .env and data folder gitignore improvements.
- [x] **GraphRAG organization:** Moved test scripts to dedicated directory, updated documentation, marked deprecated code.
- [x] **Gandalf prompt enhancement:** Updated system prompt to strictly enforce Tolkien lore responses.
- [ ] **Post-LLM validation:** (Optional) Add canonical name checks to block merges of distinct entities.
- [ ] **User-facing backend API:** Expose graph and deduplication endpoints for frontend integration.
- [ ] **Persistent user scores and leaderboards.**
- [ ] **Production LLM backend for dynamic responses.**
- [ ] **UI/UX polish and animations.**
- [ ] **Expanded Q&A and quiz coverage.**
- [ ] **User authentication and profiles.**

---

## 📝 Repo Description
> The Grey Tutor: An interactive Middle Earth chat and quiz app for exploring Tolkien lore. Features both freeform chat and quiz modes, powered by a mock database and a robust knowledge graph deduplication backend. Built with React Native + Expo. **Work in progress.**

---

## 🤝 Contributing
Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request.

---

## © 2025 Federico Andreis & Contributors
