/**
 * MiddleEarthMap Component
 *
 * Interactive SVG map of Middle Earth showing regions and journey paths.
 * Supports pan and zoom gestures.
 */

import React, { useState, useRef } from 'react';
import { View, StyleSheet, Dimensions, ScrollView } from 'react-native';
import Svg, { Rect, Image as SvgImage } from 'react-native-svg';
import { RegionMarker } from './RegionMarker';
import { JourneyPath } from './JourneyPath';
import { RegionStatus, JourneyPath as JourneyPathType } from '../../services/journeyApi';

interface MiddleEarthMapProps {
  regionStatuses: RegionStatus[];
  journeyPaths: JourneyPathType[];
  currentRegion: string | null;
  onRegionPress: (regionName: string) => void;
  activePath?: string | null;
}

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Map dimensions (can be adjusted based on design)
const MAP_WIDTH = 800;
const MAP_HEIGHT = 1000;

export const MiddleEarthMap: React.FC<MiddleEarthMapProps> = ({
  regionStatuses,
  journeyPaths,
  currentRegion,
  onRegionPress,
  activePath = null,
}) => {
  const [scale, setScale] = useState(1);
  const scrollViewRef = useRef<ScrollView>(null);

  return (
    <View style={styles.container}>
      <ScrollView
        ref={scrollViewRef}
        horizontal
        showsHorizontalScrollIndicator={false}
        showsVerticalScrollIndicator={false}
        maximumZoomScale={3}
        minimumZoomScale={0.5}
        scrollEnabled={true}
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
      >
        <ScrollView
          showsHorizontalScrollIndicator={false}
          showsVerticalScrollIndicator={false}
          scrollEnabled={true}
          contentContainerStyle={styles.scrollContent}
        >
          <View
            style={[
              styles.mapContainer,
              {
                width: MAP_WIDTH,
                height: MAP_HEIGHT,
              },
            ]}
          >
            {/* Background */}
            <Svg width={MAP_WIDTH} height={MAP_HEIGHT} style={StyleSheet.absoluteFill}>
              {/* Map background - parchment color */}
              <Rect width={MAP_WIDTH} height={MAP_HEIGHT} fill="#F5E6D3" />

              {/* Optional: Add map background image here if available */}
              {/* <SvgImage
                href={require('../../assets/middle-earth-map.png')}
                width={MAP_WIDTH}
                height={MAP_HEIGHT}
              /> */}
            </Svg>

            {/* Journey paths (rendered below markers) */}
            {journeyPaths.map((path) => (
              <JourneyPath
                key={path.name}
                path={path}
                regionStatuses={regionStatuses}
                isActive={activePath === path.name}
              />
            ))}

            {/* Region markers */}
            {regionStatuses.map((region) => (
              <RegionMarker
                key={region.name}
                region={region}
                onPress={onRegionPress}
                isCurrentRegion={currentRegion === region.name}
              />
            ))}
          </View>
        </ScrollView>
      </ScrollView>

      {/* Map legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: '#2ECC71' }]} />
          <Text style={styles.legendText}>Completed</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: '#3498DB' }]} />
          <Text style={styles.legendText}>Unlocked</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: '#F39C12' }]} />
          <Text style={styles.legendText}>Can Unlock</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: '#95A5A6', opacity: 0.5 }]} />
          <Text style={styles.legendText}>Locked</Text>
        </View>
      </View>
    </View>
  );
};

// Import Text from react-native
import { Text } from 'react-native';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ECF0F1',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  mapContainer: {
    position: 'relative',
    backgroundColor: '#F5E6D3',
  },
  legend: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    padding: 12,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  legendColor: {
    width: 16,
    height: 16,
    borderRadius: 8,
    marginRight: 8,
  },
  legendText: {
    fontSize: 12,
    color: '#2C3E50',
    fontWeight: '500',
  },
});
