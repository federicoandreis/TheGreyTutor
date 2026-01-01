/**
 * MapScreen - Main screen for the gamified Middle Earth journey map
 *
 * Shows the interactive map with regions, paths, and user progress.
 * Handles journey initialization and navigation to region details.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  SafeAreaView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import { JourneyProvider, useJourneyStore } from '../../store/journeyStore';
import { MiddleEarthMap } from '../../components/journey/MiddleEarthMap';
import { initializeJourney } from '../../store/journeyStore';
import { RootStackParamList } from '../../types';

type MapScreenNavigationProp = StackNavigationProp<RootStackParamList, 'MainTabs'>;

/**
 * Inner component that uses the journey store
 */
const MapScreenContent: React.FC = () => {
  const { state, dispatch } = useJourneyStore();
  const navigation = useNavigation<MapScreenNavigationProp>();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Initialize journey on mount
  useEffect(() => {
    const init = async () => {
      try {
        await initializeJourney(dispatch);
      } catch (error) {
        console.error('Failed to initialize journey:', error);
        Alert.alert(
          'Journey Initialization Failed',
          'Could not load your journey progress. Please try again.',
          [{ text: 'OK' }]
        );
      }
    };

    init();
  }, [dispatch]);

  // Handle region press
  const handleRegionPress = (regionName: string) => {
    console.log('Region pressed:', regionName);

    // Find the region data
    const region = state.journeyState?.journey_progress?.find(
      (r) => r.region_name === regionName
    );

    if (!region) {
      Alert.alert('Error', 'Region data not found');
      return;
    }

    // TODO: Navigate to region detail screen when implemented
    Alert.alert('Region Selected', `You selected ${regionName}`);
    // navigation.navigate('RegionDetail' as never, { regionName } as never);
  };

  // Handle refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await initializeJourney(dispatch);
    } catch (error) {
      console.error('Failed to refresh journey:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Show loading state
  if (state.isLoading && !state.isInitialized) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading your journey...</Text>
      </View>
    );
  }

  // Show error state
  if (state.error && !state.journeyState) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="warning-outline" size={64} color="#FF3B30" />
        <Text style={styles.errorTitle}>Journey Unavailable</Text>
        <Text style={styles.errorMessage}>{state.error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Show empty state (shouldn't happen if backend is working)
  if (!state.journeyState) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="map-outline" size={64} color="#8E8E93" />
        <Text style={styles.emptyTitle}>Journey Not Started</Text>
        <Text style={styles.emptyMessage}>
          Your journey through Middle Earth awaits!
        </Text>
      </View>
    );
  }

  const { journeyState } = state;

  return (
    <View style={styles.container}>
      {/* Header with stats */}
      <View style={styles.header}>
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Ionicons name="star" size={20} color="#FFD700" />
            <Text style={styles.statValue}>{journeyState.total_knowledge_points || 0}</Text>
            <Text style={styles.statLabel}>Knowledge Points</Text>
          </View>

          <View style={styles.statDivider} />

          <View style={styles.statItem}>
            <Ionicons name="location" size={20} color="#007AFF" />
            <Text style={styles.statValue}>{journeyState.unlocked_regions?.length || 0}</Text>
            <Text style={styles.statLabel}>Regions Unlocked</Text>
          </View>

          <View style={styles.statDivider} />

          <View style={styles.statItem}>
            <Ionicons name="checkmark-circle" size={20} color="#34C759" />
            <Text style={styles.statValue}>{journeyState.completed_regions?.length || 0}</Text>
            <Text style={styles.statLabel}>Completed</Text>
          </View>
        </View>
      </View>

      {/* Map */}
      <MiddleEarthMap
        regionStatuses={journeyState.journey_progress || []}
        journeyPaths={[]} // Paths not yet implemented in new API
        currentRegion={journeyState.current_region || null}
        onRegionPress={handleRegionPress}
        activePath={null}
      />

      {/* Current region indicator */}
      {journeyState.current_region && (
        <View style={styles.currentRegionBanner}>
          <Ionicons name="navigate" size={20} color="#FFFFFF" />
          <Text style={styles.currentRegionText}>
            Current Region: {
              journeyState.journey_progress?.find(
                r => r.region_name === journeyState.current_region
              )?.region_name || journeyState.current_region
            }
          </Text>
        </View>
      )}

      {/* Refresh button */}
      <TouchableOpacity
        testID="refresh-button"
        style={styles.refreshButton}
        onPress={handleRefresh}
        disabled={isRefreshing}
      >
        <Ionicons
          name={isRefreshing ? "reload" : "refresh"}
          size={24}
          color="#007AFF"
        />
      </TouchableOpacity>
    </View>
  );
};

/**
 * Main MapScreen component with JourneyProvider
 */
const MapScreen: React.FC = () => {
  return (
    <SafeAreaView style={styles.safeArea}>
      <JourneyProvider>
        <MapScreenContent />
      </JourneyProvider>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  container: {
    flex: 1,
    backgroundColor: '#ECF0F1',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#F2F2F7',
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
  retryButton: {
    marginTop: 24,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  emptyTitle: {
    marginTop: 16,
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1C1C1E',
  },
  emptyMessage: {
    marginTop: 8,
    fontSize: 16,
    color: '#6D6D70',
    textAlign: 'center',
  },
  header: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginTop: 4,
  },
  statLabel: {
    fontSize: 11,
    color: '#6D6D70',
    marginTop: 2,
    textAlign: 'center',
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#E5E5EA',
  },
  currentRegionBanner: {
    position: 'absolute',
    top: 80,
    left: 20,
    right: 20,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  currentRegionText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    flex: 1,
  },
  refreshButton: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    width: 48,
    height: 48,
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
});

export default MapScreen;
