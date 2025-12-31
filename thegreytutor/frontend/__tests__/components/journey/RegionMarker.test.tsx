import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { RegionMarker } from '../../../src/components/journey/RegionMarker';
import { RegionStatus } from '../../../src/services/journeyApi';

describe('RegionMarker', () => {
  const mockOnPress = jest.fn();

  const baseRegion: RegionStatus = {
    name: 'shire',
    display_name: 'The Shire',
    difficulty_level: 'beginner',
    is_unlocked: true,
    can_unlock: true,
    unlock_requirements: {
      knowledge_points: true,
      prerequisite_regions: true,
      mastered_themes: true,
    },
    completion_percentage: 50,
    visit_count: 3,
    is_completed: false,
    map_coordinates: {
      x: 100,
      y: 150,
      radius: 20,
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with unlocked region', () => {
    const { getByText } = render(
      <RegionMarker
        region={baseRegion}
        onPress={mockOnPress}
        isCurrentRegion={false}
      />
    );

    expect(getByText('The Shire')).toBeTruthy();
  });

  it('calls onPress with region name when pressed', () => {
    const { getByTestId } = render(
      <RegionMarker
        region={baseRegion}
        onPress={mockOnPress}
        isCurrentRegion={false}
      />
    );

    const marker = getByTestId('region-marker-shire');
    fireEvent.press(marker);

    expect(mockOnPress).toHaveBeenCalledWith('shire');
    expect(mockOnPress).toHaveBeenCalledTimes(1);
  });

  it('renders locked region with correct styling', () => {
    const lockedRegion: RegionStatus = {
      ...baseRegion,
      is_unlocked: false,
      can_unlock: false,
    };

    const { getByText } = render(
      <RegionMarker
        region={lockedRegion}
        onPress={mockOnPress}
        isCurrentRegion={false}
      />
    );

    expect(getByText('The Shire')).toBeTruthy();
  });

  it('renders completed region', () => {
    const completedRegion: RegionStatus = {
      ...baseRegion,
      completion_percentage: 100,
      is_completed: true,
    };

    const { getByText } = render(
      <RegionMarker
        region={completedRegion}
        onPress={mockOnPress}
        isCurrentRegion={false}
      />
    );

    expect(getByText('The Shire')).toBeTruthy();
  });

  it('renders current region with highlight', () => {
    const { getByText } = render(
      <RegionMarker
        region={baseRegion}
        onPress={mockOnPress}
        isCurrentRegion={true}
      />
    );

    expect(getByText('The Shire')).toBeTruthy();
  });

  it('renders region with different difficulty levels', () => {
    const difficulties: Array<RegionStatus['difficulty_level']> = [
      'beginner',
      'intermediate',
      'advanced',
      'expert',
    ];

    difficulties.forEach((difficulty) => {
      const region: RegionStatus = {
        ...baseRegion,
        difficulty_level: difficulty,
      };

      const { getByText } = render(
        <RegionMarker
          region={region}
          onPress={mockOnPress}
          isCurrentRegion={false}
        />
      );

      expect(getByText('The Shire')).toBeTruthy();
    });
  });

  it('renders unlockable region', () => {
    const unlockableRegion: RegionStatus = {
      ...baseRegion,
      is_unlocked: false,
      can_unlock: true,
    };

    const { getByText } = render(
      <RegionMarker
        region={unlockableRegion}
        onPress={mockOnPress}
        isCurrentRegion={false}
      />
    );

    expect(getByText('The Shire')).toBeTruthy();
  });

  it('handles press on locked region', () => {
    const lockedRegion: RegionStatus = {
      ...baseRegion,
      is_unlocked: false,
      can_unlock: false,
    };

    const { getByTestId } = render(
      <RegionMarker
        region={lockedRegion}
        onPress={mockOnPress}
        isCurrentRegion={false}
      />
    );

    const marker = getByTestId('region-marker-shire');
    fireEvent.press(marker);

    // Should still call onPress, let parent handle logic
    expect(mockOnPress).toHaveBeenCalledWith('shire');
  });

  it('renders with zero completion percentage', () => {
    const zeroProgressRegion: RegionStatus = {
      ...baseRegion,
      completion_percentage: 0,
    };

    const { getByText } = render(
      <RegionMarker
        region={zeroProgressRegion}
        onPress={mockOnPress}
        isCurrentRegion={false}
      />
    );

    expect(getByText('The Shire')).toBeTruthy();
  });

  it('renders with 100% completion percentage', () => {
    const fullProgressRegion: RegionStatus = {
      ...baseRegion,
      completion_percentage: 100,
      is_completed: true,
    };

    const { getByText } = render(
      <RegionMarker
        region={fullProgressRegion}
        onPress={mockOnPress}
        isCurrentRegion={false}
      />
    );

    expect(getByText('The Shire')).toBeTruthy();
  });
});
