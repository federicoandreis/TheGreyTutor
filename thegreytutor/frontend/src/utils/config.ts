/**
 * Configuration utility for accessing environment variables
 * 
 * Centralizes access to Expo environment variables with type safety and defaults.
 */

/**
 * Get an environment variable value with optional default
 * @param key - Environment variable key (must start with EXPO_PUBLIC_)
 * @param defaultValue - Optional default value if env var is not set
 * @returns The environment variable value or default
 */
export const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = process.env[key];
  
  if (!value && !defaultValue) {
    console.warn(`Environment variable ${key} is not set and no default provided`);
    return '';
  }
  
  return value || defaultValue || '';
};

/**
 * Environment configuration object
 */
export const config = {
  // API Configuration
  apiUrl: getEnvVar('EXPO_PUBLIC_API_URL', 'http://localhost:8000'),
  neo4jUri: getEnvVar('EXPO_PUBLIC_NEO4J_URI', 'bolt://localhost:7687'),
  
  // Environment
  environment: getEnvVar('EXPO_PUBLIC_ENVIRONMENT', 'development'),
  
  // Feature Flags (can be added as needed)
  enableLogging: getEnvVar('EXPO_PUBLIC_ENABLE_LOGGING', 'true') === 'true',
} as const;

/**
 * Validate required environment variables
 * Call this at app startup to ensure critical vars are set
 */
export const validateConfig = (): boolean => {
  const required = ['EXPO_PUBLIC_API_URL'];
  const missing = required.filter(key => !process.env[key]);
  
  if (missing.length > 0) {
    console.error('Missing required environment variables:', missing);
    console.error('Please check your .env file');
    return false;
  }
  
  return true;
};
