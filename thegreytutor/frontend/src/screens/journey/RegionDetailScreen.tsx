/**
 * RegionDetailScreen - Shows detailed information about a Middle Earth region
 *
 * Displays region description, unlock requirements, available quizzes,
 * and allows the user to travel to the region or start a quiz.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import { useJourneyStore, travelToRegion } from '../../store/journeyStore';
import { journeyApi, RegionDetail } from '../../services/journeyApi';
import { RootStackParamList } from '../../types';

type RegionDetailRouteProp = RouteProp<
  RootStackParamList & { RegionDetail: { regionName: string } },
  'RegionDetail'
>;

type RegionDetailNavigationProp = StackNavigationProp<RootStackParamList>;

const RegionDetailScreen: React.FC = () => {
  const route = useRoute<RegionDetailRouteProp>();
  const navigation = useNavigation<RegionDetailNavigationProp>();
  const { state, dispatch } = useJourneyStore();

  const [regionDetail, setRegionDetail] = useState<RegionDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTraveling, setIsTraveling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const regionName = route.params?.regionName;

  // Load region details
  useEffect(() => {
    const loadRegionDetails = async () => {
      if (!regionName) {
        setError('Region name not provided');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const details = await journeyApi.getRegionDetails(regionName);
        setRegionDetail(details);
      } catch (err: any) {
        console.error('Failed to load region details:', err);
        setError(err.message || 'Failed to load region details');
      } finally {
        setIsLoading(false);
      }
    };

    loadRegionDetails();
  }, [regionName]);

  // Handle travel to region
  const handleTravel = async () => {
    if (!regionDetail) return;

    setIsTraveling(true);
    try {
      const response = await travelToRegion(dispatch, regionDetail.name);

      if (response.success) {
        Alert.alert(
          'Journey Continues',
          response.message,
          [
            {
              text: 'OK',
              onPress: () => navigation.goBack(),
            },
          ]
        );
      } else {
        Alert.alert('Cannot Travel', response.message);
      }
    } catch (err: any) {
      console.error('Travel failed:', err);
      Alert.alert('Travel Failed', err.message || 'Failed to travel to region');
    } finally {
      setIsTraveling(false);
    }
  };

  // Get difficulty color
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return '#27AE60';
      case 'intermediate': return '#F39C12';
      case 'advanced': return '#E67E22';
      case 'expert': return '#C0392B';
      default: return '#95A5A6';
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading region details...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Show error state
  if (error || !regionDetail) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <Ionicons name="warning-outline" size={64} color="#FF3B30" />
          <Text style={styles.errorTitle}>Error</Text>
          <Text style={styles.errorMessage}>{error || 'Region not found'}</Text>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const isCurrentRegion = state.journeyState?.current_region === regionDetail.name;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.closeButton}
            onPress={() => navigation.goBack()}
          >
            <Ionicons name="close" size={28} color="#1C1C1E" />
          </TouchableOpacity>

          <Text style={styles.regionName}>{regionDetail.display_name}</Text>

          <View style={styles.headerRight}>
            {isCurrentRegion && (
              <View style={styles.currentBadge}>
                <Ionicons name="navigate" size={16} color="#FFFFFF" />
                <Text style={styles.currentBadgeText}>Current</Text>
              </View>
            )}
          </View>
        </View>

        {/* Content */}
        <View style={styles.content}>
          {/* Status Card */}
          <View style={styles.statusCard}>
            <View style={styles.statusRow}>
              <View style={styles.statusItem}>
                <Ionicons
                  name={regionDetail.is_unlocked ? 'lock-open' : 'lock-closed'}
                  size={24}
                  color={regionDetail.is_unlocked ? '#34C759' : '#FF3B30'}
                />
                <Text style={styles.statusLabel}>
                  {regionDetail.is_unlocked ? 'Unlocked' : 'Locked'}
                </Text>
              </View>

              <View style={styles.statusDivider} />

              <View style={styles.statusItem}>
                <View
                  style={[
                    styles.difficultyBadge,
                    { backgroundColor: getDifficultyColor(regionDetail.difficulty_level) },
                  ]}
                >
                  <Text style={styles.difficultyText}>
                    {regionDetail.difficulty_level.toUpperCase()}
                  </Text>
                </View>
              </View>

              <View style={styles.statusDivider} />

              <View style={styles.statusItem}>
                <Text style={styles.completionValue}>
                  {regionDetail.completion_percentage}%
                </Text>
                <Text style={styles.statusLabel}>Complete</Text>
              </View>
            </View>

            {/* Progress bar */}
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${regionDetail.completion_percentage}%` },
                ]}
              />
            </View>
          </View>

          {/* Description */}
          {regionDetail.description && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>About This Region</Text>
              <Text style={styles.description}>{regionDetail.description}</Text>
            </View>
          )}

          {/* Unlock Requirements */}
          {!regionDetail.is_unlocked && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Unlock Requirements</Text>
              <View style={styles.requirementsList}>
                <View style={styles.requirementItem}>
                  <Ionicons
                    name={regionDetail.can_unlock ? 'checkmark-circle' : 'close-circle'}
                    size={20}
                    color={regionDetail.can_unlock ? '#34C759' : '#FF3B30'}
                  />
                  <Text style={styles.requirementText}>
                    {regionDetail.knowledge_points_required} Knowledge Points Required
                  </Text>
                </View>

                {regionDetail.prerequisite_regions.length > 0 && (
                  <View style={styles.requirementItem}>
                    <Ionicons name="map-outline" size={20} color="#007AFF" />
                    <Text style={styles.requirementText}>
                      Complete: {regionDetail.prerequisite_regions.join(', ')}
                    </Text>
                  </View>
                )}
              </View>
            </View>
          )}

          {/* Available Quizzes */}
          {regionDetail.is_unlocked && regionDetail.available_quiz_themes.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Available Quiz Themes</Text>
              {regionDetail.available_quiz_themes.map((theme, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.quizThemeCard}
                  onPress={() => {
                    // TODO: Navigate to quiz screen with this theme
                    Alert.alert('Quiz', `Start quiz on: ${theme}`);
                  }}
                >
                  <Ionicons name="book-outline" size={24} color="#007AFF" />
                  <Text style={styles.quizThemeName}>{theme}</Text>
                  <Ionicons name="chevron-forward" size={20} color="#C7C7CC" />
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Map Location */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Map Coordinates</Text>
            <View style={styles.coordinatesCard}>
              <Ionicons name="location" size={24} color="#007AFF" />
              <Text style={styles.coordinatesText}>
                X: {regionDetail.map_coordinates.x}, Y: {regionDetail.map_coordinates.y}
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* Action Button */}
      {!isCurrentRegion && (
        <View style={styles.actionContainer}>
          {regionDetail.is_unlocked ? (
            <TouchableOpacity
              style={[styles.travelButton, isTraveling && styles.travelButtonDisabled]}
              onPress={handleTravel}
              disabled={isTraveling}
            >
              {isTraveling ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <>
                  <Ionicons name="navigate" size={20} color="#FFFFFF" />
                  <Text style={styles.travelButtonText}>Travel to This Region</Text>
                </>
              )}
            </TouchableOpacity>
          ) : (
            <View style={styles.lockedButton}>
              <Ionicons name="lock-closed" size={20} color="#6D6D70" />
              <Text style={styles.lockedButtonText}>
                {regionDetail.can_unlock
                  ? 'Complete prerequisites to unlock'
                  : 'Not yet accessible'}
              </Text>
            </View>
          )}
        </View>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6D6D70',
  },
  errorTitle: {
    marginTop: 16,
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1C1C1E',
  },
  errorMessage: {
    marginTop: 8,
    fontSize: 16,
    color: '#6D6D70',
    textAlign: 'center',
  },
  backButton: {
    marginTop: 24,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  closeButton: {
    padding: 4,
  },
  regionName: {
    flex: 1,
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1C1C1E',
    textAlign: 'center',
    marginHorizontal: 12,
  },
  headerRight: {
    minWidth: 36,
    alignItems: 'flex-end',
  },
  currentBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  currentBadgeText: {
    marginLeft: 4,
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  content: {
    padding: 20,
  },
  statusCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 16,
  },
  statusItem: {
    flex: 1,
    alignItems: 'center',
  },
  statusLabel: {
    marginTop: 4,
    fontSize: 12,
    color: '#6D6D70',
  },
  statusDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#E5E5EA',
  },
  difficultyBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  difficultyText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  completionValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1C1C1E',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  description: {
    fontSize: 16,
    color: '#3C3C43',
    lineHeight: 24,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  requirementsList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  requirementItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  requirementText: {
    marginLeft: 12,
    fontSize: 14,
    color: '#3C3C43',
    flex: 1,
  },
  quizThemeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  quizThemeName: {
    flex: 1,
    marginLeft: 12,
    fontSize: 16,
    fontWeight: '500',
    color: '#1C1C1E',
  },
  coordinatesCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  coordinatesText: {
    marginLeft: 12,
    fontSize: 14,
    color: '#3C3C43',
    fontFamily: 'monospace',
  },
  actionContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  travelButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 16,
  },
  travelButtonDisabled: {
    backgroundColor: '#8E8E93',
  },
  travelButtonText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  lockedButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E5E5EA',
    borderRadius: 12,
    paddingVertical: 16,
  },
  lockedButtonText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
    color: '#6D6D70',
  },
});

export default RegionDetailScreen;
