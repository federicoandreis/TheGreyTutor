import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import LearningScreen from '../../../src/screens/learning/LearningScreen-simple';

describe('LearningScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders correctly with header', () => {
    const { getByText } = render(<LearningScreen />);

    expect(getByText('Learning Paths')).toBeTruthy();
    expect(getByText('Choose your journey through Middle Earth')).toBeTruthy();
  });

  it('displays stats overview', () => {
    const { getAllByText, getByText } = render(<LearningScreen />);

    expect(getAllByText('0').length).toBeGreaterThan(0);
    expect(getByText('Paths Completed')).toBeTruthy();
    expect(getByText('Total Lessons')).toBeTruthy();
    expect(getByText('Time Spent')).toBeTruthy();
  });

  it('renders all learning paths', () => {
    const { getByText } = render(<LearningScreen />);

    // All 5 learning paths should be present
    expect(getByText('The Fellowship of the Ring')).toBeTruthy();
    expect(getByText('The Two Towers')).toBeTruthy();
    expect(getByText('The Return of the King')).toBeTruthy();
    expect(getByText('The Hobbit')).toBeTruthy();
    expect(getByText('The Silmarillion')).toBeTruthy();
  });

  it('displays learning path descriptions', () => {
    const { getByText } = render(<LearningScreen />);

    expect(getByText(/Begin your journey with the formation of the Fellowship/)).toBeTruthy();
    expect(getByText(/Continue the epic tale of Middle Earth/)).toBeTruthy();
    expect(getByText(/Discover Bilbo's unexpected journey/)).toBeTruthy();
  });

  it('displays difficulty levels for each path', () => {
    const { getAllByText } = render(<LearningScreen />);

    expect(getAllByText('Beginner').length).toBe(2); // Fellowship and Hobbit
    expect(getAllByText('Intermediate').length).toBe(1); // Two Towers
    expect(getAllByText('Advanced').length).toBe(1); // Return of the King
    expect(getAllByText('Expert').length).toBe(1); // Silmarillion
  });

  it('displays estimated time for each path', () => {
    const { getByText } = render(<LearningScreen />);

    expect(getByText(/2 hours/)).toBeTruthy();
    expect(getByText(/3 hours/)).toBeTruthy();
    expect(getByText(/4 hours/)).toBeTruthy();
    expect(getByText(/1\.5 hours/)).toBeTruthy();
    expect(getByText(/6 hours/)).toBeTruthy();
  });

  it('displays total lessons for each path', () => {
    const { getByText } = render(<LearningScreen />);

    expect(getByText(/12\s+lessons/)).toBeTruthy();
    expect(getByText(/15\s+lessons/)).toBeTruthy();
    expect(getByText(/18\s+lessons/)).toBeTruthy();
    expect(getByText(/10\s+lessons/)).toBeTruthy();
    expect(getByText(/25\s+lessons/)).toBeTruthy();
  });

  it('displays emojis for each learning path', () => {
    const { getByText } = render(<LearningScreen />);

    expect(getByText('🧙‍♂️')).toBeTruthy();
    expect(getByText('🏰')).toBeTruthy();
    expect(getByText('👑')).toBeTruthy();
    expect(getByText('🏠')).toBeTruthy();
    expect(getByText('💎')).toBeTruthy();
  });

  it('calls console.log when a learning path is pressed', () => {
    const consoleLogSpy = jest.spyOn(console, 'log');
    const { getByText } = render(<LearningScreen />);

    const pathCard = getByText('The Fellowship of the Ring');
    fireEvent.press(pathCard);

    expect(consoleLogSpy).toHaveBeenCalledWith('Selected learning path:', '1');
  });

  it('displays progress for each path', () => {
    const { getAllByText } = render(<LearningScreen />);

    // All paths start at 0/totalLessons progress
    const progressText = getAllByText(/0\//);
    expect(progressText.length).toBe(5); // One for each path
  });

  it('displays quick actions section', () => {
    const { getByText } = render(<LearningScreen />);

    expect(getByText('Quick Actions')).toBeTruthy();
    expect(getByText('View Achievements')).toBeTruthy();
    expect(getByText('Middle Earth Map')).toBeTruthy();
    expect(getByText('Character Guide')).toBeTruthy();
  });

  it('displays section titles', () => {
    const { getByText } = render(<LearningScreen />);

    expect(getByText('Available Paths')).toBeTruthy();
    expect(getByText('Quick Actions')).toBeTruthy();
  });
});
