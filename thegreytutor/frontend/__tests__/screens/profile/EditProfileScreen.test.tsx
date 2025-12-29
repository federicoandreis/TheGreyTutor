import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import EditProfileScreen from '../../../src/screens/profile/EditProfileScreen';
import * as ImagePicker from 'expo-image-picker';

// Mock dependencies
jest.mock('expo-image-picker');
jest.mock('../../../src/store/store-minimal', () => ({
  useAppState: () => ({
    state: {
      user: {
        id: 'test-user-id',
        username: 'testuser',
        email: 'test@example.com',
        displayName: 'Test User',
        avatar: '🧙‍♂️',
      },
    },
    dispatch: jest.fn(),
  }),
}));

describe('EditProfileScreen', () => {
  const mockNavigation = {
    navigate: jest.fn(),
    goBack: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(Alert, 'alert');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders correctly with user data', () => {
    const { getByPlaceholderText, getByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    expect(getByText('Edit Profile')).toBeTruthy();
    expect(getByPlaceholderText('Enter username')).toBeTruthy();
    expect(getByPlaceholderText('Enter email')).toBeTruthy();
    expect(getByPlaceholderText('Enter display name')).toBeTruthy();
    expect(getByText('Change Avatar')).toBeTruthy();
  });

  it('displays current user data in form fields', () => {
    const { getByDisplayValue } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    expect(getByDisplayValue('testuser')).toBeTruthy();
    expect(getByDisplayValue('test@example.com')).toBeTruthy();
    expect(getByDisplayValue('Test User')).toBeTruthy();
  });

  it('updates form fields when user types', () => {
    const { getByPlaceholderText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Enter username');
    fireEvent.changeText(usernameInput, 'newusername');

    expect(usernameInput.props.value).toBe('newusername');
  });

  it('shows error for invalid username', async () => {
    const { getByPlaceholderText, getByText, queryByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Enter username');
    const saveButton = getByText('Save');

    // Clear username
    fireEvent.changeText(usernameInput, '');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(queryByText('Username is required')).toBeTruthy();
    });
  });

  it('shows error for username less than 3 characters', async () => {
    const { getByPlaceholderText, getByText, queryByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Enter username');
    const saveButton = getByText('Save');

    fireEvent.changeText(usernameInput, 'ab');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(queryByText('Username must be at least 3 characters')).toBeTruthy();
    });
  });

  it('shows error for username with invalid characters', async () => {
    const { getByPlaceholderText, getByText, queryByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Enter username');
    const saveButton = getByText('Save');

    fireEvent.changeText(usernameInput, 'invalid user');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(
        queryByText('Username can only contain letters, numbers, underscores, and hyphens')
      ).toBeTruthy();
    });
  });

  it('shows error for invalid email', async () => {
    const { getByPlaceholderText, getByText, queryByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const emailInput = getByPlaceholderText('Enter email');
    const saveButton = getByText('Save');

    fireEvent.changeText(emailInput, 'invalid-email');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(queryByText('Please enter a valid email address')).toBeTruthy();
    });
  });

  it('shows error for empty display name', async () => {
    const { getByPlaceholderText, getByText, queryByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const displayNameInput = getByPlaceholderText('Enter display name');
    const saveButton = getByText('Save');

    fireEvent.changeText(displayNameInput, '');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(queryByText('Display name is required')).toBeTruthy();
    });
  });

  it('clears error when user fixes input', async () => {
    const { getByPlaceholderText, getByText, queryByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Enter username');
    const saveButton = getByText('Save');

    // Trigger error
    fireEvent.changeText(usernameInput, '');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(queryByText('Username is required')).toBeTruthy();
    });

    // Fix input
    fireEvent.changeText(usernameInput, 'validusername');

    await waitFor(() => {
      expect(queryByText('Username is required')).toBeFalsy();
    });
  });

  it('calls image picker when Change Avatar is pressed', async () => {
    const mockImagePicker = ImagePicker as jest.Mocked<typeof ImagePicker>;
    mockImagePicker.requestMediaLibraryPermissionsAsync = jest.fn().mockResolvedValue({
      granted: true,
    });
    mockImagePicker.launchImageLibraryAsync = jest.fn().mockResolvedValue({
      canceled: false,
      assets: [{ uri: 'file://test-avatar.jpg' }],
    });

    const { getByText } = render(<EditProfileScreen navigation={mockNavigation} />);

    const changeAvatarButton = getByText('Change Avatar');
    fireEvent.press(changeAvatarButton);

    await waitFor(() => {
      expect(mockImagePicker.requestMediaLibraryPermissionsAsync).toHaveBeenCalled();
      expect(mockImagePicker.launchImageLibraryAsync).toHaveBeenCalled();
    });
  });

  it('shows alert when permission is denied', async () => {
    const mockImagePicker = ImagePicker as jest.Mocked<typeof ImagePicker>;
    mockImagePicker.requestMediaLibraryPermissionsAsync = jest.fn().mockResolvedValue({
      granted: false,
    });

    const { getByText } = render(<EditProfileScreen navigation={mockNavigation} />);

    const changeAvatarButton = getByText('Change Avatar');
    fireEvent.press(changeAvatarButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Permission Required',
        'Permission to access camera roll is required!'
      );
    });
  });

  it('navigates back on cancel without changes', () => {
    const { getByText } = render(<EditProfileScreen navigation={mockNavigation} />);

    const cancelButton = getByText('Cancel');
    fireEvent.press(cancelButton);

    expect(mockNavigation.goBack).toHaveBeenCalled();
  });

  it('shows confirmation alert when canceling with changes', async () => {
    const { getByPlaceholderText, getByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Enter username');
    fireEvent.changeText(usernameInput, 'changedusername');

    const cancelButton = getByText('Cancel');
    fireEvent.press(cancelButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Discard Changes?',
        'You have unsaved changes. Are you sure you want to discard them?',
        expect.any(Array)
      );
    });
  });

  it('successfully saves valid profile changes', async () => {
    const { getByPlaceholderText, getByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Enter username');
    const emailInput = getByPlaceholderText('Enter email');
    const displayNameInput = getByPlaceholderText('Enter display name');

    fireEvent.changeText(usernameInput, 'newusername');
    fireEvent.changeText(emailInput, 'newemail@example.com');
    fireEvent.changeText(displayNameInput, 'New Display Name');

    const saveButton = getByText('Save');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Success',
        'Profile updated successfully!',
        expect.any(Array)
      );
    });
  });

  it('shows loading indicator while saving', async () => {
    const { getByText, queryByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const saveButton = getByText('Save');
    fireEvent.press(saveButton);

    // The Save button should be replaced with a loading indicator
    await waitFor(() => {
      expect(queryByText('Save')).toBeFalsy();
    });
  });

  it('does not submit form with validation errors', async () => {
    const { getByPlaceholderText, getByText } = render(
      <EditProfileScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Enter username');
    fireEvent.changeText(usernameInput, ''); // Invalid

    const saveButton = getByText('Save');
    fireEvent.press(saveButton);

    await waitFor(() => {
      // Should show error, not success alert
      const alertCalls = (Alert.alert as jest.Mock).mock.calls;
      const successAlertCalled = alertCalls.some(
        (call) => call[0] === 'Success'
      );
      expect(successAlertCalled).toBe(false);
    });
  });

  it('renders info card with privacy message', () => {
    const { getByText } = render(<EditProfileScreen navigation={mockNavigation} />);

    expect(
      getByText(/Your profile information is used to personalize your learning experience/)
    ).toBeTruthy();
  });
});
