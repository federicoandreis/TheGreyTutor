// Jest setup file for Integration Tests (minimal mocks, uses real backend)

// Only mock UI-specific things that can't run in test environment

// Mock expo-image-picker (UI-only)
jest.mock('expo-image-picker', () => ({
  requestMediaLibraryPermissionsAsync: jest.fn(() =>
    Promise.resolve({ status: 'granted', granted: true })
  ),
  launchImageLibraryAsync: jest.fn(() =>
    Promise.resolve({
      canceled: false,
      assets: [{ uri: 'test-image-uri' }],
    })
  ),
  MediaTypeOptions: {
    Images: 'Images',
  },
}));

// Mock expo-secure-store (but with real in-memory storage)
const mockStorage = new Map();

jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn((key) => Promise.resolve(mockStorage.get(key) || null)),
  setItemAsync: jest.fn((key, value) => {
    mockStorage.set(key, value);
    return Promise.resolve();
  }),
  deleteItemAsync: jest.fn((key) => {
    mockStorage.delete(key);
    return Promise.resolve();
  }),
}));

// Mock AsyncStorage with real in-memory implementation
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

// Mock Alert for React Native
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn((title, message, buttons) => {
    // Automatically press first button if provided
    if (buttons && buttons.length > 0 && buttons[0].onPress) {
      buttons[0].onPress();
    }
  }),
}));

// Increase timeout for integration tests (real API calls take time)
jest.setTimeout(30000);

// Set test environment variable
process.env.EXPO_PUBLIC_API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

// Log test start
console.log('🧪 Integration Test Environment');
console.log(`📡 API URL: ${process.env.EXPO_PUBLIC_API_URL}`);
console.log('⏱️  Timeout: 30 seconds');
console.log('');

// Suppress less important console output
global.console = {
  ...console,
  warn: jest.fn(),
  debug: jest.fn(),
};
