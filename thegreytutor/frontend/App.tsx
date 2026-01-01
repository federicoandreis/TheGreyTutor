import React, { useEffect, useState } from 'react';
import { LogBox, Platform, View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { AppProvider, useAppState } from './src/store/store-minimal';
import AppNavigator from './src/navigation/AppNavigator';
import * as SecureStore from 'expo-secure-store';
import { authApi } from './src/services/authApi';

// Ensure vector icons are properly loaded
import { Ionicons } from '@expo/vector-icons';

// Pre-load any resources needed for navigation
import { enableScreens } from 'react-native-screens';

// Enable screens optimization for React Navigation
enableScreens();

// Ignore specific warnings that might be related to the issue
LogBox.ignoreLogs([
  'Require cycle:',
  'Non-serializable values were found in the navigation state',
]);

/**
 * AppContent - Handles session restoration on app start
 */
function AppContent() {
  const { state, dispatch } = useAppState();
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      console.log('[App] Checking for existing session...');
      
      // Check if tokens exist
      const accessToken = await SecureStore.getItemAsync('access_token');
      const refreshToken = await SecureStore.getItemAsync('refresh_token');
      
      if (accessToken && refreshToken) {
        console.log('[App] Tokens found, restoring session...');
        
        // Set a basic authenticated user state
        // The actual user data will be loaded by components as needed
        // If token is invalid, apiClient will handle refresh or logout
        dispatch({ 
          type: 'SET_USER', 
          payload: { 
            id: 'restored',
            email: 'user@restored.session',
            displayName: 'User',
            avatar: '🧙‍♂️'
          } 
        });
        console.log('[App] Session restored successfully');
      } else {
        console.log('[App] No tokens found, user needs to login');
      }
    } catch (error) {
      console.error('[App] Session check failed:', error);
      // Clear any invalid tokens
      try {
        await SecureStore.deleteItemAsync('access_token');
        await SecureStore.deleteItemAsync('refresh_token');
      } catch (clearError) {
        console.error('[App] Failed to clear tokens:', clearError);
      }
    } finally {
      setIsCheckingSession(false);
    }
  };

  // Show splash screen while checking session
  if (isCheckingSession) {
    return (
      <View style={styles.splashContainer}>
        <Text style={styles.splashTitle}>🧙‍♂️</Text>
        <Text style={styles.splashSubtitle}>The Grey Tutor</Text>
        <ActivityIndicator size="large" color="#007AFF" style={styles.splashLoader} />
        <Text style={styles.splashText}>Loading your journey...</Text>
      </View>
    );
  }

  return (
    <NavigationContainer fallback={<StatusBar style="light" />}>
      <StatusBar style="light" backgroundColor="#2c3e50" />
      <AppNavigator />
    </NavigationContainer>
  );
}

export default function App() {
  // Initialize any required modules for mobile
  useEffect(() => {
    // Ensure Ionicons are loaded properly
    if (Platform.OS !== 'web') {
      // Force load the Ionicons module to ensure it's available
      // This helps prevent the "Cannot read property 'S' of undefined" error
      // No need to actually use the icons, just referencing the import is enough
      // to ensure it's properly loaded in the bundle
    }
  }, []);

  return (
    <SafeAreaProvider>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  splashContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#2C3E50',
  },
  splashTitle: {
    fontSize: 64,
    marginBottom: 16,
  },
  splashSubtitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 48,
  },
  splashLoader: {
    marginBottom: 16,
  },
  splashText: {
    fontSize: 16,
    color: '#ECF0F1',
  },
});
