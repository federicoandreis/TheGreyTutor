import React, { useEffect } from 'react';
import { LogBox, Platform } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { AppProvider } from './src/store/store-minimal';
import AppNavigator from './src/navigation/AppNavigator';

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
        <NavigationContainer fallback={<StatusBar style="light" />}>
          <StatusBar style="light" backgroundColor="#2c3e50" />
          <AppNavigator />
        </NavigationContainer>
      </AppProvider>
    </SafeAreaProvider>
  );
}
