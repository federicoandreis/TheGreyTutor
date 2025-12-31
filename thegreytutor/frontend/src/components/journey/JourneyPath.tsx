/**
 * JourneyPath Component
 *
 * Visual representation of a journey path connecting multiple regions.
 */

import React from 'react';
import { StyleSheet } from 'react-native';
import Svg, { Path as SvgPath, Defs, LinearGradient, Stop } from 'react-native-svg';
import { JourneyPath as JourneyPathType, RegionStatus } from '../../services/journeyApi';

interface JourneyPathProps {
  path: JourneyPathType;
  regionStatuses: RegionStatus[];
  isActive?: boolean;
}

export const JourneyPath: React.FC<JourneyPathProps> = ({
  path,
  regionStatuses,
  isActive = false,
}) => {
  // Generate SVG path data connecting regions
  const generatePathData = (): string => {
    const regions = path.ordered_regions
      .map((regionName) => regionStatuses.find((r) => r.name === regionName))
      .filter((r): r is RegionStatus => r !== undefined);

    if (regions.length < 2) {
      return '';
    }

    let pathData = `M ${regions[0].map_coordinates.x} ${regions[0].map_coordinates.y}`;

    for (let i = 1; i < regions.length; i++) {
      const prev = regions[i - 1];
      const current = regions[i];

      // Use quadratic bezier curve for smoother paths
      const controlX = (prev.map_coordinates.x + current.map_coordinates.x) / 2;
      const controlY = Math.min(prev.map_coordinates.y, current.map_coordinates.y) - 30;

      pathData += ` Q ${controlX} ${controlY}, ${current.map_coordinates.x} ${current.map_coordinates.y}`;
    }

    return pathData;
  };

  const pathData = generatePathData();

  if (!pathData) {
    return null;
  }

  // Determine path opacity based on unlock status
  const getPathOpacity = (): number => {
    const unlockedCount = path.ordered_regions.filter((regionName) =>
      regionStatuses.find((r) => r.name === regionName && r.is_unlocked)
    ).length;

    // More regions unlocked = more opaque
    return 0.3 + (unlockedCount / path.ordered_regions.length) * 0.7;
  };

  return (
    <Svg width="100%" height="100%" style={StyleSheet.absoluteFill}>
      <Defs>
        <LinearGradient id={`gradient-${path.name}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <Stop offset="0%" stopColor={path.path_color} stopOpacity={getPathOpacity()} />
          <Stop offset="100%" stopColor={path.path_color} stopOpacity={getPathOpacity() * 0.6} />
        </LinearGradient>
      </Defs>

      <SvgPath
        d={pathData}
        stroke={`url(#gradient-${path.name})`}
        strokeWidth={isActive ? 4 : 3}
        fill="none"
        strokeDasharray={isActive ? undefined : '10,5'}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
};
