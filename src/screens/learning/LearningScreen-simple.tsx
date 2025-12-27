import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const LearningScreen: React.FC = () => {
  const learningPaths = [
    {
      id: '1',
      title: 'The Fellowship of the Ring',
      description: 'Begin your journey with the formation of the Fellowship',
      progress: 0,
      totalLessons: 12,
      icon: '🧙‍♂️',
      difficulty: 'Beginner',
      estimatedTime: '2 hours',
    },
    {
      id: '2',
      title: 'The Two Towers',
      description: 'Continue the epic tale of Middle Earth',
      progress: 0,
      totalLessons: 15,
      icon: '🏰',
      difficulty: 'Intermediate',
      estimatedTime: '3 hours',
    },
    {
      id: '3',
      title: 'The Return of the King',
      description: 'Witness the climactic conclusion of the War of the Ring',
      progress: 0,
      totalLessons: 18,
      icon: '👑',
      difficulty: 'Advanced',
      estimatedTime: '4 hours',
    },
    {
      id: '4',
      title: 'The Hobbit',
      description: 'Discover Bilbo\'s unexpected journey',
      progress: 0,
      totalLessons: 10,
      icon: '🏠',
      difficulty: 'Beginner',
      estimatedTime: '1.5 hours',
    },
    {
      id: '5',
      title: 'The Silmarillion',
      description: 'Explore the ancient history of Middle Earth',
      progress: 0,
      totalLessons: 25,
      icon: '💎',
      difficulty: 'Expert',
      estimatedTime: '6 hours',
    },
  ];

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner': return '#34C759';
      case 'Intermediate': return '#FF9500';
      case 'Advanced': return '#FF3B30';
      case 'Expert': return '#AF52DE';
      default: return '#007AFF';
    }
  };

  const handlePathPress = (pathId: string) => {
    console.log('Selected learning path:', pathId);
    // Navigation to specific learning path would go here
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Learning Paths</Text>
            <Text style={styles.subtitle}>
              Choose your journey through Middle Earth
            </Text>
          </View>

          {/* Stats Overview */}
          <View style={styles.statsContainer}>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>0</Text>
              <Text style={styles.statLabel}>Paths Completed</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>0</Text>
              <Text style={styles.statLabel}>Total Lessons</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>0h</Text>
              <Text style={styles.statLabel}>Time Spent</Text>
            </View>
          </View>

          {/* Learning Paths */}
          <View style={styles.pathsSection}>
            <Text style={styles.sectionTitle}>Available Paths</Text>
            {learningPaths.map((path) => (
              <TouchableOpacity
                key={path.id}
                style={styles.pathCard}
                onPress={() => handlePathPress(path.id)}
              >
                <View style={styles.pathHeader}>
                  <View style={styles.pathIcon}>
                    <Text style={styles.pathEmoji}>{path.icon}</Text>
                  </View>
                  <View style={styles.pathInfo}>
                    <Text style={styles.pathTitle}>{path.title}</Text>
                    <Text style={styles.pathDescription}>{path.description}</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color="#C7C7CC" />
                </View>

                <View style={styles.pathDetails}>
                  <View style={styles.pathMeta}>
                    <View style={[styles.difficultyBadge, { backgroundColor: getDifficultyColor(path.difficulty) }]}>
                      <Text style={styles.difficultyText}>{path.difficulty}</Text>
                    </View>
                    <Text style={styles.pathTime}>
                      <Ionicons name="time-outline" size={14} color="#8E8E93" /> {path.estimatedTime}
                    </Text>
                    <Text style={styles.pathLessons}>
                      <Ionicons name="book-outline" size={14} color="#8E8E93" /> {path.totalLessons} lessons
                    </Text>
                  </View>

                  {/* Progress Bar */}
                  <View style={styles.progressContainer}>
                    <View style={styles.progressBar}>
                      <View 
                        style={[
                          styles.progressFill, 
                          { width: `${(path.progress / path.totalLessons) * 100}%` }
                        ]} 
                      />
                    </View>
                    <Text style={styles.progressText}>
                      {path.progress}/{path.totalLessons}
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>

          {/* Quick Actions */}
          <View style={styles.actionsSection}>
            <Text style={styles.sectionTitle}>Quick Actions</Text>
            <TouchableOpacity style={styles.actionCard}>
              <Ionicons name="trophy-outline" size={24} color="#FF9500" />
              <View style={styles.actionInfo}>
                <Text style={styles.actionTitle}>View Achievements</Text>
                <Text style={styles.actionDescription}>See your progress and unlocked badges</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#C7C7CC" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionCard}>
              <Ionicons name="map-outline" size={24} color="#007AFF" />
              <View style={styles.actionInfo}>
                <Text style={styles.actionTitle}>Middle Earth Map</Text>
                <Text style={styles.actionDescription}>Explore locations and their stories</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#C7C7CC" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionCard}>
              <Ionicons name="library-outline" size={24} color="#34C759" />
              <View style={styles.actionInfo}>
                <Text style={styles.actionTitle}>Character Guide</Text>
                <Text style={styles.actionDescription}>Learn about key characters and their roles</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#C7C7CC" />
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6D6D70',
  },
  statsContainer: {
    flexDirection: 'row',
    marginBottom: 32,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#6D6D70',
    textAlign: 'center',
  },
  pathsSection: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  pathCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  pathHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  pathIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#F2F2F7',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  pathEmoji: {
    fontSize: 24,
  },
  pathInfo: {
    flex: 1,
  },
  pathTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  pathDescription: {
    fontSize: 14,
    color: '#6D6D70',
    lineHeight: 20,
  },
  pathDetails: {
    marginTop: 8,
  },
  pathMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  difficultyText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  pathTime: {
    fontSize: 12,
    color: '#8E8E93',
  },
  pathLessons: {
    fontSize: 12,
    color: '#8E8E93',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  progressBar: {
    flex: 1,
    height: 6,
    backgroundColor: '#E5E5EA',
    borderRadius: 3,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '500',
  },
  actionsSection: {
    marginBottom: 20,
  },
  actionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  actionInfo: {
    flex: 1,
    marginLeft: 12,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  actionDescription: {
    fontSize: 14,
    color: '#6D6D70',
  },
});

export default LearningScreen;
