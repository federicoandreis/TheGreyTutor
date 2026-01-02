/**
 * MiddleEarthMap Component
 *
 * Interactive SVG map of Middle Earth showing regions and journey paths.
 * Supports pan and zoom gestures.
 */

import React, { useState, useRef } from 'react';
import { View, StyleSheet, Dimensions, ScrollView, Text } from 'react-native';
import Svg, { Rect, Image as SvgImage } from 'react-native-svg';
import { RegionMarker } from './RegionMarker';
import { JourneyPath } from './JourneyPath';
import { RegionProgress } from '../../services/api/journey';

// Type for journey paths (simplified for now)
interface JourneyPathType {
  name: string;
  points: Array<{ x: number; y: number }>;
}

interface MiddleEarthMapProps {
  regionStatuses: RegionProgress[];
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

            {/* Journey paths (rendered below markers) - TODO: Update JourneyPath component */}
            {/* {journeyPaths.map((path) => (
              <JourneyPath
                key={path.name}
                path={path}
                regionStatuses={regionStatuses}
                isActive={activePath === path.name}
              />
            ))} */}

            {/* Region markers - Simple implementation for Phase 1 */}
            {regionStatuses.map((region, index) => {
              // Simple grid layout for now
              const col = index % 3;
              const row = Math.floor(index / 3);
              const left = 100 + col * 200;
              const top = 150 + row * 150;
              
              // Determine color based on status
              let backgroundColor = '#95A5A6'; // Locked (default)
              if (region.is_completed) {
                backgroundColor = '#2ECC71'; // Completed (green)
              } else if (region.is_unlocked) {
                backgroundColor = '#3498DB'; // Unlocked (blue)
              }
              // Locked regions stay gray
              
              return (
                <View
                  key={region.region_name}
                  style={{
                    position: 'absolute',
                    left,
                    top,
                    alignItems: 'center',
                  }}
                  onTouchEnd={() => onRegionPress(region.region_name)}
                >
                  <View
                    style={{
                      width: 60,
                      height: 60,
                      borderRadius: 30,
                      backgroundColor,
                      justifyContent: 'center',
                      alignItems: 'center',
                      borderWidth: region.region_name === currentRegion ? 3 : 0,
                      borderColor: '#FFD700',
                      shadowColor: '#000',
                      shadowOffset: { width: 0, height: 2 },
                      shadowOpacity: 0.3,
                      shadowRadius: 4,
                      elevation: 4,
                    }}
                  >
                    <Text style={{ fontSize: 24 }}>📍</Text>
                  </View>
                  <Text
                    style={{
                      marginTop: 4,
                      fontSize: 10,
                      fontWeight: 'bold',
                      color: '#2C3E50',
                      textAlign: 'center',
                      maxWidth: 80,
                    }}
                    numberOfLines={2}
                  >
                    {region.region_name}
                  </Text>
                </View>
              );
            })}
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

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#2C3E50',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  mapContainer: {
    position: 'relative',
    backgroundColor: '#F5E6D3',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
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
