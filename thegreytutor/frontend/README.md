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

## ⚡ Work in Progress
- The app is currently in active development.
- **Chat Mode** is fully functional with an extensive, regex-driven mock Q&A database.
- **Quiz Mode** is implemented and demo-ready, featuring multiple-choice questions and scoring.
- The UI is simple, accessible, and mobile-first.

### What’s Next
- Add persistent user scores and leaderboards.
- Integrate real AI/LLM backend for dynamic responses.
- Polish UI/UX and add animations.
- Expand Q&A and quiz coverage.
- Add user authentication and profiles.

---

## 📝 Repo Description
> The Grey Tutor: An interactive Middle Earth chat and quiz app for exploring Tolkien lore. Features both freeform chat and quiz modes, powered by a mock database. Built with React Native + Expo. **Work in progress.**

---

## 🤝 Contributing
Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request.

---

## © 2025 Federico Andreis & Contributors
