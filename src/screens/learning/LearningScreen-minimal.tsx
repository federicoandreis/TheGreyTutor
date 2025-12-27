import React from 'react';
import { View, Text, StyleSheet, SafeAreaView } from 'react-native';

const LearningScreen: React.FC = () => {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>📚</Text>
        <Text style={styles.heading}>Learning Paths</Text>
        <Text style={styles.subtitle}>Learning modules coming soon</Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 64,
    marginBottom: 16,
  },
  heading: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6D6D70',
    textAlign: 'center',
  },
});

export default LearningScreen;
