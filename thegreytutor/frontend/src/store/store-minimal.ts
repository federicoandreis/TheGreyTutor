import React, { createContext, useContext, useReducer, ReactNode, useEffect } from 'react';
import { authApi, AuthUser, AuthResponse } from '../services/authApi';

// User interface matching backend response
interface User {
  id: string;
  email: string;
  displayName: string;
  username?: string;
  role?: string;
}

interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
}

type AppAction = 
  | { type: 'SET_USER'; payload: User }
  | { type: 'CLEAR_USER' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_INITIALIZED'; payload: boolean };

const initialState: AppState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  isInitialized: false,
  error: null,
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        error: null,
      };
    case 'CLEAR_USER':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        error: null,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };
    case 'SET_INITIALIZED':
      return {
        ...state,
        isInitialized: action.payload,
      };
    default:
      return state;
  }
}

const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  return React.createElement(
    AppContext.Provider,
    { value: { state, dispatch } },
    children
  );
}

export function useAppState() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppState must be used within AppProvider');
  }
  return context;
}

// Helper to convert AuthUser to User
function authUserToUser(authUser: AuthUser): User {
  return {
    id: authUser.id,
    email: authUser.email,
    displayName: authUser.name || authUser.username,
    username: authUser.username,
    role: authUser.role,
  };
}

// Login function using real auth API
export async function loginUser(email: string, password: string): Promise<User> {
  const response = await authApi.login({ email, password });
  return authUserToUser(response.user);
}

// Register function using real auth API
export async function registerUser(
  username: string,
  email: string,
  password: string,
  name?: string
): Promise<User> {
  const response = await authApi.register({ username, email, password, name });
  return authUserToUser(response.user);
}

// Logout function
export async function logoutUser(): Promise<void> {
  await authApi.logout();
}

// Initialize auth state (check for existing session)
export async function initializeAuth(): Promise<User | null> {
  const hasToken = await authApi.initialize();
  if (hasToken) {
    try {
      const authUser = await authApi.getCurrentUser();
      return authUserToUser(authUser);
    } catch (error) {
      console.error('Failed to restore session:', error);
      return null;
    }
  }
  return null;
}
