// Jest setup file for Unit Tests (with mocks)

// Mock expo-image-picker
jest.mock('expo-image-picker', () => ({
  requestMediaLibraryPermissionsAsync: jest.fn(() =>
    Promise.resolve({ status: 'granted', granted: true })
  ),
  launchImageLibraryAsync: jest.fn(() =>
    Promise.resolve({
      canceled: false,
      assets: [{ uri: 'mock-image-uri' }],
    })
  ),
  MediaTypeOptions: {
    Images: 'Images',
  },
}));

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(() => Promise.resolve('mock-token')),
  setItemAsync: jest.fn(() => Promise.resolve()),
  deleteItemAsync: jest.fn(() => Promise.resolve()),
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});

// Mock @react-navigation/native
jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => ({
    navigate: jest.fn(),
    goBack: jest.fn(),
    setOptions: jest.fn(),
  }),
  useRoute: () => ({
    params: {},
  }),
}));

// Mock authApi for unit tests
jest.mock('./src/services/authApi', () => ({
  authApi: {
    authenticatedFetch: jest.fn((url, options) =>
      Promise.resolve({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => ({}),
      })
    ),
    login: jest.fn((credentials) =>
      Promise.resolve({
        success: true,
        message: 'Login successful',
        user: {
          id: 'mock-user-id',
          username: credentials.email.split('@')[0],
          email: credentials.email,
          name: 'Mock User',
          role: 'user',
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString(),
        },
        tokens: {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'Bearer',
          expires_in: 900,
          refresh_expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
      })
    ),
    register: jest.fn((data) =>
      Promise.resolve({
        success: true,
        message: 'Registration successful',
        user: {
          id: 'mock-user-id',
          username: data.username,
          email: data.email,
          name: data.name || null,
          role: 'user',
          created_at: new Date().toISOString(),
          last_login: null,
        },
        tokens: {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'Bearer',
          expires_in: 900,
          refresh_expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
      })
    ),
    logout: jest.fn(() => Promise.resolve()),
    getCurrentUser: jest.fn(() =>
      Promise.resolve({
        id: 'mock-user-id',
        username: 'testuser',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        created_at: new Date().toISOString(),
        last_login: new Date().toISOString(),
      })
    ),
    changePassword: jest.fn(() => Promise.resolve()),
    isAuthenticated: jest.fn(() => true),
    getAccessToken: jest.fn(() => 'mock-access-token'),
    initialize: jest.fn(() => Promise.resolve(true)),
  },
}));

// Mock global fetch for any non-API calls
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => ({}),
  })
);

// Suppress console warnings during tests
global.console = {
  ...console,
  warn: jest.fn(),
  error: jest.fn(),
};

// Mock Alert for React Native
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));
