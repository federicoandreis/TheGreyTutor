# The Grey Tutor - Frontend Mobile App

React Native + Expo cross-platform mobile app for learning Middle Earth lore with Gandalf.

---

## 🚀 Quick Start

```powershell
# From project root
cd thegreytutor/frontend

# Install dependencies
npm install --legacy-peer-deps

# Start Expo dev server
npx expo start

# Or use the root startup script (recommended)
cd ../..
.\start_all.ps1
```

**Expo Dev Server:** `http://localhost:19006`
**Scan QR code** with Expo Go app on your mobile device

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── screens/              # Screen components
│   │   ├── auth/             # Login, Register
│   │   ├── chat/             # Chat with Gandalf
│   │   ├── learning/         # Learning paths
│   │   ├── journey/          # Journey Map, Region Details
│   │   ├── quiz/             # Dedicated Quiz Screen
│   │   └── profile/          # User profile, Settings
│   │
│   ├── components/           # Reusable components
│   │   ├── journey/          # RegionMarker, Map
│   │   ├── quiz/             # Question cards
│   │   └── ui/               # Buttons, Inputs, etc.
│   │
│   ├── navigation/           # React Navigation setup
│   │   └── AppNavigator.tsx  # Tab + Stack navigation
│   │
│   ├── services/             # API clients
│   │   ├── authApi.ts        # Authentication API
│   │   ├── journeyApi.ts     # Journey/gamification API
│   │   ├── quizApi.ts        # Quiz API
│   │   └── mock*.ts          # Mock databases
│   │
│   ├── store/                # State management
│   │   └── store-minimal.tsx # Context API state
│   │
│   └── types/                # TypeScript types
│
├── __tests__/                # Test files
│   ├── components/
│   │   └── journey/
│   │       └── RegionMarker.test.tsx  ✅ 10/10 passing
│   ├── screens/
│   │   ├── journey/
│   │   │   └── MapScreen.test.tsx     ✅ 7/7 passing
│   │   ├── quiz/
│   │   │   └── QuizScreen.test.tsx    ✅ 5/5 passing (new)
│   │   └── profile/
│   │       └── EditProfileScreen.test.tsx  ⚠️ 3/10 passing
│   └── services/
│       └── journeyApi.test.ts         ⚠️ 0/10 failing
│
├── assets/                   # Images, fonts
├── App.tsx                   # App entry point
├── app.json                  # Expo configuration
├── package.json              # Dependencies
├── jest.config.js            # Jest configuration
├── jest.setup.js             # Test setup & mocks
└── README.md                 # This file
```

---

## 🧪 Testing

### Dual Testing Strategy

This project uses **two types of tests**:

**1. Unit Tests (Fast, Mocked)**
- Test individual components and functions in isolation
- Use mocked dependencies (authApi, etc.)
- Run in <10 seconds

**2. Integration Tests (Real Backend)**
- Test API integration with real backend
- Require backend running at `http://localhost:8000`
- 30 second timeout per test

### Run Tests

```powershell
# Unit tests only (fast, default)
npm run test:unit

# Integration tests only (requires backend)
npm run test:integration

# All tests (unit + integration)
npm run test:all

# Unit tests in watch mode
npm run test:watch

# Unit tests with coverage
npm run test:coverage

# Specific test file
npm run test:unit -- journeyApi.unit.test.ts
npm run test:integration -- journeyApi.integration.test.ts
```

### Test Status

**Unit Tests:**
- ✅ `RegionMarker.test.tsx` - 10/10 passing
- ✅ `MapScreen.test.tsx` - 7/7 passing
- ✅ `journeyApi.unit.test.ts` - 14/14 passing
- ⚠️ `EditProfileScreen.test.tsx` - 3/10 passing (needs update)

**Integration Tests:**
- ✅ `journeyApi.integration.test.ts` - Ready (requires backend)

**Overall:** 31/41 unit tests passing (75.6%) - Target: 70%+ ✅

See [Testing Guide](../../docs/TESTING_GUIDE.md) for detailed information.

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in this directory:

```env
EXPO_PUBLIC_API_URL=http://localhost:8000
```

For testing on mobile device (same WiFi):
```env
EXPO_PUBLIC_API_URL=http://192.168.0.225:8000
```

### Expo Configuration

Configuration in [`app.json`](app.json):

```json
{
  "expo": {
    "name": "The Grey Tutor",
    "slug": "thegreytutor",
    "version": "1.0.0",
    "sdkVersion": "54.0.0",
    "platforms": ["ios", "android", "web"]
  }
}
```

---

## 📱 Screens

### Authentication
- **Login** (`src/screens/auth/LoginScreen.tsx`)
  - Email/password login
  - JWT token management
  - Secure token storage (expo-secure-store)

- **Register** (`src/screens/auth/RegisterScreen.tsx`)
  - User registration
  - Form validation
  - Automatic login after registration

### Main App
- **Chat** (`src/screens/chat/ChatScreen.tsx`)
  - Conversational AI with Gandalf
  - Message history
  - Quiz mode toggle
  - PathRAG-powered responses

- **Journey Map** (`src/screens/journey/MapScreen.tsx`)
  - Interactive SVG map of Middle Earth
  - 8 unlockable regions
  - Progress tracking
  - Region details modal

- **Learning** (`src/screens/learning/LearningScreen.tsx`)
  - Three journey paths
  - Quiz interface
  - Progress tracking

- **Profile** (`src/screens/profile/ProfileScreen.tsx`)
  - User information
  - Achievement showcase
  - Statistics dashboard
  - Settings

---

## 🎨 UI Components

### Journey Components
- **RegionMarker** - Interactive region markers on map
- **Map** - Scrollable/zoomable Middle Earth SVG map
- **AchievementBadge** - Achievement display cards

### Quiz Components
- **QuestionCard** - Quiz question display
- **AnswerOptions** - Multiple choice options
- **FeedbackDisplay** - Answer feedback from Gandalf

### UI Components
- **Button** - Styled button component
- **Input** - Form input component
- **Card** - Content card wrapper
- **Modal** - Dialog/modal component

---

## 🔌 API Integration

### API Clients

**Auth API** (`src/services/authApi.ts`)
```typescript
import { authApi } from './services/authApi';

// Register
await authApi.register({ username, email, password });

// Login
await authApi.login({ email, password });

// Get current user
const user = await authApi.getCurrentUser();

// Logout
await authApi.logout();
```

**Journey API** (`src/services/journeyApi.ts`)
```typescript
import { journeyApi } from './services/journeyApi';

// Get journey state
const state = await journeyApi.getJourneyState();

// Travel to region
const result = await journeyApi.travelToRegion('rivendell');

// Complete quiz
await journeyApi.completeQuiz({
  region_name: 'shire',
  quiz_id: '123',
  score: 8,
  questions_answered: 10,
  answers: [...]
});
```

---

## 🗺️ Navigation

### Navigation Structure

```
App
├── Auth Stack (Not logged in)
│   ├── Login
│   └── Register
│
└── Main Tabs (Logged in)
    ├── Chat Tab
    ├── Learning Tab
    ├── Journey Tab
    └── Profile Tab
```

### Navigation Setup

Using React Navigation v6:

```typescript
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();
```

---

## 🎯 State Management

Currently using **Context API** for global state:

```typescript
// src/store/store-minimal.tsx
import { AppProvider, useAppContext } from './store/store-minimal';

// In App.tsx
<AppProvider>
  <NavigationContainer>
    <AppNavigator />
  </NavigationContainer>
</AppProvider>

// In components
const { user, setUser } = useAppContext();
```

**Future:** Migrate to TanStack Query + Zustand (see Production Guide)

---

## 📦 Dependencies

### Core
- `expo@^54.0.0` - Expo framework
- `react@19.1.0` - React library
- `react-native@0.81.5` - React Native

### Navigation
- `@react-navigation/native@^6.1.9` - Navigation core
- `@react-navigation/bottom-tabs@^6.5.11` - Tab navigation
- `@react-navigation/stack@^6.3.20` - Stack navigation

### UI
- `@expo/vector-icons@^15.0.3` - Icon library
- `react-native-svg@^15.15.1` - SVG support
- `react-native-reanimated@~4.1.1` - Animations

### Storage & State
- `expo-secure-store@~15.0.8` - Secure token storage
- `@supabase/supabase-js@^2.38.4` - Future Supabase integration

### Testing
- `jest@^29.2.1` - Test framework
- `jest-expo` - Expo-specific Jest preset
- `@testing-library/react-native@^13.3.3` - Testing utilities
- `react-native-worklets` - Reanimated test support

---

## 🐛 Debugging

### Enable Debug Mode

```typescript
// In App.tsx
import { LogBox } from 'react-native';

// Ignore specific warnings
LogBox.ignoreLogs([
  'Require cycle:',
  'Non-serializable values were found in the navigation state',
]);
```

### Expo Dev Tools

```powershell
# Open Expo dev tools
npx expo start

# Then press:
# m - Toggle menu
# r - Reload app
# Shift+r - Reload and clear cache
# c - Clear Metro bundler cache
```

### React Native Debugger

```powershell
# Install React Native Debugger
# Download from: https://github.com/jhen0409/react-native-debugger/releases

# Enable debugging in Expo
# Shake device → Debug Remote JS
```

---

## 🔍 Type Checking

```powershell
# Run TypeScript type checking
npm run type-check

# Fix type errors before committing
```

---

## 🎨 Styling

### Theme Colors (Middle Earth Palette)

```typescript
const theme = {
  colors: {
    primary: '#8B4513',      // Saddle Brown (Gandalf's staff)
    secondary: '#2F4F4F',    // Dark Slate Gray (Middle Earth)
    background: '#1C1C1C',   // Dark background
    text: '#F5F5DC',         // Beige (parchment)
    success: '#228B22',      // Forest Green (Shire)
    error: '#8B0000',        // Dark Red (Mordor)
    warning: '#DAA520',      // Goldenrod (Ring)
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
};
```

### Component Styling

```typescript
import { StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1C1C1C',
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#F5F5DC',
  },
});
```

---

## 📱 Platform-Specific Code

```typescript
import { Platform } from 'react-native';

const styles = StyleSheet.create({
  container: {
    ...Platform.select({
      ios: {
        paddingTop: 44, // iOS status bar
      },
      android: {
        paddingTop: 24, // Android status bar
      },
      web: {
        maxWidth: 800,
        alignSelf: 'center',
      },
    }),
  },
});
```

---

## 🚀 Building for Production

### Development Build

```powershell
# Install Expo CLI globally
npm install -g expo-cli

# Start development server
npx expo start
```

### Production Build (EAS Build - Future)

```powershell
# Install EAS CLI
npm install -g eas-cli

# Configure EAS
eas build:configure

# Build for Android
eas build --platform android

# Build for iOS
eas build --platform ios

# Build for both
eas build --platform all
```

---

## 🤝 Contributing

### Adding a New Screen

1. Create screen component in `src/screens/`
2. Add route to navigator in `src/navigation/AppNavigator.tsx`
3. Write tests in `__tests__/screens/`
4. Update this README
5. Run tests: `npm test`
6. Submit PR to `dev` branch

### Adding a New Component

1. Create component in `src/components/`
2. Add TypeScript types
3. Write tests in `__tests__/components/`
4. Export from component directory
5. Document usage

### Code Style

- Follow React/TypeScript best practices
- Use functional components with hooks
- Use TypeScript types (no `any`)
- Keep components small and focused
- Test all new components

---

## 📚 Related Documentation

- [Testing Guide](../../docs/TESTING_GUIDE.md) - Comprehensive testing documentation
- [Development Guide](../../docs/DEVELOPMENT_GUIDE.md) - Daily development workflow
- [Production Build Guide](../../docs/PRODUCTION_BUILD_GUIDE.md) - Production deployment
- [Codebase Assessment](../../docs/CODEBASE_ASSESSMENT_2025.md) - Project overview

---

## 🐛 Common Issues

### "Unable to resolve module"
```powershell
# Clear cache and reinstall
rm -r -Force node_modules
npm install --legacy-peer-deps
npx expo start --clear
```

### "Invariant Violation: "main" has not been registered"
```powershell
# Restart Metro bundler
# Press 'r' in Expo terminal to reload
```

### "Network request failed"
```powershell
# Check API URL in .env
# Ensure backend is running
# Check firewall settings
```

---

## © 2025 The Grey Tutor Team
