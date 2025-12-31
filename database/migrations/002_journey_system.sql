-- Migration: Journey System
-- Date: 2025-12-30
-- Description: Creates tables for the Journey Agent & Gamified Middle Earth Map feature

-- ============================================================================
-- MIDDLE EARTH REGIONS (Static configuration data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS middle_earth_regions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR NOT NULL UNIQUE,
    display_name VARCHAR NOT NULL,

    -- Map coordinates for frontend visualization
    map_coordinates JSON NOT NULL, -- {x: 150, y: 200, radius: 25}

    -- Unlock requirements
    difficulty_level VARCHAR NOT NULL CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    prerequisite_regions JSON DEFAULT '[]'::json, -- Array of region names
    knowledge_points_required INTEGER DEFAULT 0,
    mastered_themes_required JSON DEFAULT '[]'::json, -- ['elves', 'fellowship']

    -- Learning content configuration
    neo4j_community_tags JSON DEFAULT '[]'::json, -- Maps to graph communities
    available_quiz_themes JSON DEFAULT '[]'::json,
    lore_depth VARCHAR DEFAULT 'surface' CHECK (lore_depth IN ('surface', 'deep', 'expert')),

    -- Narrative elements
    description TEXT,
    gandalf_introduction TEXT, -- What Gandalf says when you arrive
    completion_reward VARCHAR,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_regions_difficulty ON middle_earth_regions(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_regions_name ON middle_earth_regions(name);

COMMENT ON TABLE middle_earth_regions IS 'Defines all Middle Earth regions available in the journey system';
COMMENT ON COLUMN middle_earth_regions.map_coordinates IS 'SVG coordinates for map visualization: {x, y, radius}';
COMMENT ON COLUMN middle_earth_regions.neo4j_community_tags IS 'Community tags in Neo4j graph that map to this region';

-- ============================================================================
-- JOURNEY PATHS (Pre-defined learning sequences)
-- ============================================================================
CREATE TABLE IF NOT EXISTS journey_paths (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR NOT NULL UNIQUE,
    display_name VARCHAR NOT NULL,
    description TEXT,

    -- Path configuration
    ordered_regions JSON NOT NULL, -- Ordered array of region names
    narrative_theme VARCHAR, -- 'fellowship', 'silmarillion', 'hobbit', 'custom'
    estimated_duration_hours INTEGER,

    -- Unlock conditions
    unlock_condition JSON DEFAULT '{}'::json, -- {type: 'default'} or specific requirements

    -- Visual representation
    svg_path_data TEXT, -- SVG path for map visualization
    path_color VARCHAR DEFAULT '#4A90E2',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_paths_name ON journey_paths(name);

COMMENT ON TABLE journey_paths IS 'Predefined journey paths through Middle Earth';
COMMENT ON COLUMN journey_paths.ordered_regions IS 'Array of region names in journey order';

-- ============================================================================
-- USER JOURNEY PROGRESS (Per-user, per-region tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_journey_progress (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    region_name VARCHAR NOT NULL,

    -- Progress metrics
    visit_count INTEGER DEFAULT 0,
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    time_spent_minutes INTEGER DEFAULT 0,

    -- Quiz performance in this region
    quizzes_completed JSON DEFAULT '[]'::json, -- Array of quiz IDs
    quiz_success_rate FLOAT DEFAULT 0.0,

    -- Knowledge graph learning
    concepts_encountered JSON DEFAULT '[]'::json, -- Neo4j node names
    relationships_discovered JSON DEFAULT '[]'::json, -- Relationship types learned
    community_mastery JSON DEFAULT '{}'::json, -- {community_name: mastery_score}

    -- Status tracking
    is_unlocked BOOLEAN DEFAULT FALSE,
    is_completed BOOLEAN DEFAULT FALSE,
    first_visited TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_visited TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    UNIQUE(user_id, region_name)
);

CREATE INDEX IF NOT EXISTS idx_journey_progress_user ON user_journey_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_journey_progress_region ON user_journey_progress(region_name);
CREATE INDEX IF NOT EXISTS idx_journey_progress_user_region ON user_journey_progress(user_id, region_name);
CREATE INDEX IF NOT EXISTS idx_journey_progress_unlocked ON user_journey_progress(user_id, is_unlocked);

COMMENT ON TABLE user_journey_progress IS 'Tracks individual user progress in each region';
COMMENT ON COLUMN user_journey_progress.completion_percentage IS '0-100, based on quizzes completed and mastery achieved';

-- ============================================================================
-- USER GLOBAL JOURNEY STATE (Overall progress tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_journey_state (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,

    -- Current state
    current_region VARCHAR,
    current_path VARCHAR,
    knowledge_points INTEGER DEFAULT 0,

    -- Unlocked content
    unlocked_regions JSON DEFAULT '["the_shire"]'::json, -- Start with Shire
    active_paths JSON DEFAULT '[]'::json,

    -- Achievements
    achievement_badges JSON DEFAULT '[]'::json, -- Array of badge objects
    mastered_communities JSON DEFAULT '[]'::json, -- Communities fully mastered

    -- Journey metadata
    total_regions_completed INTEGER DEFAULT 0,
    total_quizzes_taken INTEGER DEFAULT 0,
    journey_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_journey_state_user ON user_journey_state(user_id);
CREATE INDEX IF NOT EXISTS idx_journey_state_region ON user_journey_state(current_region);

COMMENT ON TABLE user_journey_state IS 'Global journey state for each user';
COMMENT ON COLUMN user_journey_state.knowledge_points IS 'Total knowledge points earned across all regions';
COMMENT ON COLUMN user_journey_state.unlocked_regions IS 'Array of region names unlocked by this user';

-- ============================================================================
-- ACHIEVEMENTS (Static configuration)
-- ============================================================================
CREATE TABLE IF NOT EXISTS achievements (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    code VARCHAR NOT NULL UNIQUE,
    name VARCHAR NOT NULL,
    description TEXT,
    category VARCHAR NOT NULL CHECK (category IN ('region', 'quiz', 'knowledge', 'special')),

    -- Unlock conditions
    unlock_criteria JSON NOT NULL,

    -- Visual representation
    icon_name VARCHAR,
    badge_color VARCHAR,
    rarity VARCHAR DEFAULT 'common' CHECK (rarity IN ('common', 'rare', 'epic', 'legendary')),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_achievements_code ON achievements(code);
CREATE INDEX IF NOT EXISTS idx_achievements_category ON achievements(category);

COMMENT ON TABLE achievements IS 'Achievement definitions - static configuration';
COMMENT ON COLUMN achievements.unlock_criteria IS 'JSON criteria for unlocking: {type: "visit_region", region: "the_shire"}';

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to automatically create journey state for new users
CREATE OR REPLACE FUNCTION create_user_journey_state()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_journey_state (user_id, knowledge_points, unlocked_regions)
    VALUES (NEW.id, 0, '["the_shire"]'::json)
    ON CONFLICT (user_id) DO NOTHING;

    -- Also create initial progress for The Shire
    INSERT INTO user_journey_progress (user_id, region_name, is_unlocked, visit_count)
    VALUES (NEW.id, 'the_shire', TRUE, 0)
    ON CONFLICT (user_id, region_name) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to create journey state when user is created
DROP TRIGGER IF EXISTS trigger_create_journey_state ON users;
CREATE TRIGGER trigger_create_journey_state
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION create_user_journey_state();

-- Function to update last_activity timestamp
CREATE OR REPLACE FUNCTION update_journey_last_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update last_activity
DROP TRIGGER IF EXISTS trigger_update_journey_activity ON user_journey_state;
CREATE TRIGGER trigger_update_journey_activity
    BEFORE UPDATE ON user_journey_state
    FOR EACH ROW
    EXECUTE FUNCTION update_journey_last_activity();

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Additional composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_progress_user_completed ON user_journey_progress(user_id, is_completed);
CREATE INDEX IF NOT EXISTS idx_progress_completion_pct ON user_journey_progress(user_id, completion_percentage);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMENT ON SCHEMA public IS 'Journey system migration 002 completed - 2025-12-30';
