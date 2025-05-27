# The Grey Tutor

A comprehensive learning application that takes users on an educational journey through Middle Earth with Gandalf as their AI tutor. Built with a Python FastAPI backend and React Native Expo frontend.

## Project Overview

The Grey Tutor is an innovative educational platform that combines AI-powered tutoring with gamified learning experiences set in Tolkien's Middle Earth. Users can chat with Gandalf, explore iconic locations, complete quests, and track their learning progress through an immersive fantasy interface.

## Architecture

### Backend (Python FastAPI)
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI Integration**: Multi-agent system with specialized AI tutors
- **Authentication**: JWT-based with secure session management
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Monitoring**: Comprehensive logging and health checks

### Frontend (React Native Expo)
- **Framework**: React Native with Expo for cross-platform development
- **State Management**: Redux Toolkit with RTK Query
- **Navigation**: React Navigation v6
- **UI**: Custom themed components with Middle Earth aesthetics
- **TypeScript**: Full type safety throughout the application

## Project Structure

```
thegreytutor/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── core/              # Core configuration and utilities
│   │   │   ├── config.py      # Environment configuration
│   │   │   ├── database.py    # Database connection and models
│   │   │   ├── security.py    # Authentication and security
│   │   │   └── logging.py     # Logging configuration
│   │   ├── api/               # API route handlers
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── chat.py        # Chat and messaging endpoints
│   │   │   ├── users.py       # User management endpoints
│   │   │   ├── learning.py    # Learning progress endpoints
│   │   │   └── agents.py      # AI agent management endpoints
│   │   ├── models/            # SQLAlchemy database models
│   │   │   ├── user.py        # User and authentication models
│   │   │   ├── chat.py        # Chat and message models
│   │   │   ├── learning.py    # Learning progress models
│   │   │   └── content.py     # Content and quest models
│   │   ├── services/          # Business logic services
│   │   │   ├── auth_service.py      # Authentication logic
│   │   │   ├── chat_service.py      # Chat processing logic
│   │   │   ├── ai_service.py        # AI agent coordination
│   │   │   ├── learning_service.py  # Learning progress tracking
│   │   │   └── content_service.py   # Content management
│   │   ├── agents/            # AI agent implementations
│   │   │   ├── base_agent.py        # Base agent class
│   │   │   ├── grey_tutor.py        # Main Gandalf tutor agent
│   │   │   ├── knowledge_agent.py   # Knowledge retrieval agent
│   │   │   ├── assessment_agent.py  # Quiz and assessment agent
│   │   │   ├── journey_agent.py     # Learning path agent
│   │   │   └── analytics_agent.py   # Progress analytics agent
│   │   └── utils/             # Utility functions
│   │       ├── middleware.py  # Custom middleware
│   │       ├── exceptions.py  # Custom exception handlers
│   │       └── validators.py  # Input validation utilities
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment variables template
│   └── package.json          # Node.js dependencies (if needed)
│
├── frontend/                  # React Native Expo frontend
│   ├── src/
│   │   ├── types/             # TypeScript type definitions
│   │   │   └── index.ts       # Main type exports
│   │   ├── store/             # Redux store configuration
│   │   │   ├── store.ts       # Store setup and configuration
│   │   │   ├── hooks.ts       # Typed Redux hooks
│   │   │   └── slices/        # Redux slices
│   │   │       ├── authSlice.ts     # Authentication state
│   │   │       ├── chatSlice.ts     # Chat and messaging state
│   │   │       ├── learningSlice.ts # Learning progress state
│   │   │       └── uiSlice.ts       # UI and app state
│   │   ├── navigation/        # Navigation configuration
│   │   │   └── AppNavigator.tsx     # Main navigation setup
│   │   ├── screens/           # Screen components
│   │   │   ├── auth/          # Authentication screens
│   │   │   │   ├── LoginScreen.tsx
│   │   │   │   └── RegisterScreen.tsx
│   │   │   ├── chat/          # Chat interface screens
│   │   │   │   └── ChatScreen.tsx
│   │   │   ├── learning/      # Learning journey screens
│   │   │   │   └── LearningScreen.tsx
│   │   │   └── profile/       # User profile screens
│   │   │       └── ProfileScreen.tsx
│   │   ├── components/        # Reusable UI components
│   │   │   ├── common/        # Common UI components
│   │   │   ├── chat/          # Chat-specific components
│   │   │   └── learning/      # Learning-specific components
│   │   ├── services/          # API and external services
│   │   │   ├── api/           # API client configuration
│   │   │   └── storage/       # Local storage utilities
│   │   ├── hooks/             # Custom React hooks
│   │   └── utils/             # Utility functions
│   │       ├── constants.ts   # App constants
│   │       └── helpers.ts     # Helper functions
│   ├── App.tsx               # Main application component
│   ├── index.ts              # Application entry point
│   ├── app.json              # Expo configuration
│   ├── package.json          # Dependencies and scripts
│   └── tsconfig.json         # TypeScript configuration
│
└── README.md                 # This file
```

## Features

### Core Features
- **AI-Powered Chat**: Conversation with Gandalf using advanced language models
- **Multi-Agent System**: Specialized AI agents for different learning aspects
- **Gamified Learning**: Quest system with achievements and progress tracking
- **Middle Earth Journey**: Explore iconic locations from Tolkien's world
- **Personalized Experience**: Adaptive learning paths based on user progress

### Technical Features
- **Cross-Platform**: Runs on iOS, Android, and web
- **Real-time Communication**: WebSocket support for live chat
- **Offline Capability**: Local storage for offline learning
- **Security**: JWT authentication with refresh tokens
- **Scalability**: Microservices-ready architecture
- **Monitoring**: Comprehensive logging and analytics

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Expo CLI
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd thegreytutor/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   # Create PostgreSQL database
   createdb thegreytutor
   
   # Run migrations (when implemented)
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   python src/main.py
   ```

   The API will be available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd thegreytutor/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

4. **Run on specific platforms**
   ```bash
   npm run ios     # iOS simulator
   npm run android # Android emulator
   npm run web     # Web browser
   ```

## Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/thegreytutor
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=thegreytutor
DATABASE_USER=your_user
DATABASE_PASSWORD=your_password

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Application
APP_NAME=The Grey Tutor
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:19006
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token

### Chat
- `POST /api/chat/send` - Send message to AI tutor
- `GET /api/chat/sessions` - Get user's chat sessions
- `POST /api/chat/sessions` - Create new chat session
- `GET /api/chat/sessions/{id}` - Get specific chat session

### Learning
- `GET /api/learning/progress` - Get user's learning progress
- `POST /api/learning/progress` - Update learning progress
- `GET /api/learning/locations` - Get available locations
- `GET /api/learning/achievements` - Get user's achievements

### Users
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update user profile
- `GET /api/users/stats` - Get user statistics

## Development Guidelines

### Code Style
- **Python**: Follow PEP 8, use Black for formatting
- **TypeScript**: Follow ESLint rules, use Prettier for formatting
- **Git**: Use conventional commits (feat:, fix:, docs:, etc.)

### Testing
- **Backend**: pytest with coverage reporting
- **Frontend**: Jest and React Testing Library
- **E2E**: Detox for mobile testing

### Security Best Practices
- Never commit secrets or API keys
- Use environment variables for configuration
- Implement proper input validation
- Follow OWASP security guidelines
- Regular dependency updates

## Deployment

### Backend Deployment
- **Production**: Docker containers with Kubernetes
- **Staging**: Docker Compose setup
- **Database**: PostgreSQL with connection pooling
- **Monitoring**: Prometheus and Grafana

### Frontend Deployment
- **Mobile**: Expo Application Services (EAS)
- **Web**: Vercel or Netlify
- **CI/CD**: GitHub Actions for automated builds

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- J.R.R. Tolkien for the inspiration of Middle Earth
- The open-source community for the amazing tools and libraries
- All contributors who help make this project better

## Support

For support, email support@thegreytutor.com or join our Discord community.

---

*"All we have to decide is what to do with the time that is given us."* - Gandalf the Grey
