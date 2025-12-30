/**
 * RegionMarker Component
 *
 * Visual marker for a region on the Middle Earth map.
 * Shows unlock status, completion percentage, and difficulty.
 */

import React from 'react';
import { TouchableOpacity, StyleSheet } from 'react-native';
import { Text, View } from 'react-native';
import Svg, { Circle, G } from 'react-native-svg';
import { RegionStatus } from '../../services/journeyApi';

interface RegionMarkerProps {
  region: RegionStatus;
  onPress: (regionName: string) => void;
  isCurrentRegion?: boolean;
}

export const RegionMarker: React.FC<RegionMarkerProps> = ({
  region,
  onPress,
  isCurrentRegion = false,
}) => {
  // Determine marker color based on status
  const getMarkerColor = (): string => {
    if (region.is_completed) return '#2ECC71'; // Green
    if (region.is_unlocked) return '#3498DB'; // Blue
    if (region.can_unlock) return '#F39C12'; // Orange
    return '#95A5A6'; // Gray (locked)
  };

  // Get difficulty color
  const getDifficultyColor = (): string => {
    switch (region.difficulty_level) {
      case 'beginner':
        return '#27AE60';
      case 'intermediate':
        return '#F39C12';
      case 'advanced':
        return '#E67E22';
      case 'expert':
        return '#C0392B';
      default:
        return '#95A5A6';
    }
  };

  const markerColor = getMarkerColor();
  const difficultyColor = getDifficultyColor();

  return (
    <TouchableOpacity
      testID={`region-marker-${region.name}`}
      style={[
        styles.container,
        {
          left: region.map_coordinates.x,
          top: region.map_coordinates.y,
        },
      ]}
      onPress={() => onPress(region.name)}
      activeOpacity={0.7}
    >
      <Svg width={region.map_coordinates.radius * 2 + 10} height={region.map_coordinates.radius * 2 + 10}>
        <G>
          {/* Outer ring for current region */}
          {isCurrentRegion && (
            <Circle
              cx={(region.map_coordinates.radius * 2 + 10) / 2}
              cy={(region.map_coordinates.radius * 2 + 10) / 2}
              r={region.map_coordinates.radius + 3}
              stroke="#FFD700"
              strokeWidth={2}
              fill="none"
            />
          )}

          {/* Main region circle */}
          <Circle
            cx={(region.map_coordinates.radius * 2 + 10) / 2}
            cy={(region.map_coordinates.radius * 2 + 10) / 2}
            r={region.map_coordinates.radius}
            fill={markerColor}
            opacity={region.is_unlocked ? 1.0 : 0.5}
          />

          {/* Difficulty indicator ring */}
          <Circle
            cx={(region.map_coordinates.radius * 2 + 10) / 2}
            cy={(region.map_coordinates.radius * 2 + 10) / 2}
            r={region.map_coordinates.radius - 3}
            stroke={difficultyColor}
            strokeWidth={2}
            fill="none"
          />

          {/* Completion arc (if partially completed) */}
          {region.completion_percentage > 0 && region.completion_percentage < 100 && (
            <Circle
              cx={(region.map_coordinates.radius * 2 + 10) / 2}
              cy={(region.map_coordinates.radius * 2 + 10) / 2}
              r={region.map_coordinates.radius - 6}
              stroke="#2ECC71"
              strokeWidth={3}
              fill="none"
              strokeDasharray={`${(region.completion_percentage / 100) * (Math.PI * 2 * (region.map_coordinates.radius - 6))} ${Math.PI * 2 * (region.map_coordinates.radius - 6)}`}
            />
          )}
        </G>
      </Svg>

      {/* Region label */}
      <View style={styles.labelContainer}>
        <Text
          style={[
            styles.label,
            { color: region.is_unlocked ? '#2C3E50' : '#7F8C8D' },
          ]}
          numberOfLines={2}
        >
          {region.display_name}
        </Text>

        {/* Completion percentage */}
        {region.is_unlocked && region.completion_percentage > 0 && (
          <Text style={styles.completionText}>{region.completion_percentage}%</Text>
        )}

        {/* Lock icon indicator */}
        {!region.is_unlocked && (
          <Text style={styles.lockIcon}>🔒</Text>
        )}

        {/* Completed checkmark */}
        {region.is_completed && (
          <Text style={styles.completedIcon}>✓</Text>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  labelContainer: {
    marginTop: 5,
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    minWidth: 60,
    maxWidth: 120,
  },
  label: {
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
  },
  completionText: {
    fontSize: 10,
    color: '#27AE60',
    fontWeight: '700',
    marginTop: 2,
  },
  lockIcon: {
    fontSize: 14,
    marginTop: 2,
  },
  completedIcon: {
    fontSize: 16,
    color: '#2ECC71',
    fontWeight: '900',
    marginTop: 2,
  },
});
