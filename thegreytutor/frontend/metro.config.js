const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Enable Hermes for better performance on mobile
config.transformer.enableHermes = true;

// Add additional resolver options for better compatibility
config.resolver = {
  ...config.resolver,
  sourceExts: ['jsx', 'js', 'ts', 'tsx', 'json'],
  assetExts: [...config.resolver.assetExts, 'db', 'sqlite'],
};

module.exports = config;
