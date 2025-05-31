# The Grey Tutor

An interactive Middle Earth-themed chat and quiz app, built with React Native and Expo. The Grey Tutor allows users to explore Tolkien lore, ask questions, and test their knowledge with a dynamic quiz mode. All responses are powered by a rich, extensible mock database for easy demonstration and testing.

---

## 🚀 Features
- **Chat Mode:**
  - Ask about characters, places, events, and lore from Tolkien's world.
  - Instant answers using regex-powered keyword matching.
- **Quiz Mode:**
  - Toggleable quiz experience with multiple choice questions.
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
1. **Clone the repo:**
   ```sh
   git clone https://github.com/federicoandreis/TheGreyTutor.git
   cd TheGreyTutor/frontend
   ```
2. **Install dependencies:**
   ```sh
   npm install
   ```
3. **Start the app:**
   ```sh
   npx expo start
   ```
4. **Test on device or emulator.**

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

## ⚡ Work in Progress
- The app and backend are in active development.
- **Chat Mode**: Fully functional with a regex-driven mock Q&A database.
- **Quiz Mode**: Demo-ready with scoring.
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
