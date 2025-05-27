import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Provider } from 'react-redux';
import { StatusBar } from 'expo-status-bar';
import { configureStore, createSlice } from '@reduxjs/toolkit';

// Ultra minimal slice
const testSlice = createSlice({
  name: 'test',
  initialState: { value: 0 },
  reducers: {
    increment: (state) => {
      state.value += 1;
    },
  },
});

// Ultra minimal store
const testStore = configureStore({
  reducer: {
    test: testSlice.reducer,
  },
});

export default function App() {
  return (
    <Provider store={testStore}>
      <View style={styles.container}>
        <StatusBar style="light" backgroundColor="#2c3e50" />
        <Text style={styles.title}>The Grey Tutor</Text>
        <Text style={styles.subtitle}>Ultra Minimal Redux Test</Text>
      </View>
    </Provider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#2c3e50',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ecf0f1',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#bdc3c7',
  },
});
