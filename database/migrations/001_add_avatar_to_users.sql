-- Migration: Add avatar column to users table
-- Date: 2025-12-29
-- Description: Adds nullable avatar column to store user avatar URLs or emoji

-- Add avatar column
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar VARCHAR(255);

-- Add comment
COMMENT ON COLUMN users.avatar IS 'User avatar URL or emoji character';
