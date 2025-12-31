"""
Journey system models for The Grey Tutor database.

This module defines the SQLAlchemy models for the Journey Agent & Gamified Map feature.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text, CheckConstraint
from sqlalchemy.orm import relationship
from database.connection import Base
from database.models.user import User  # Import User model for relationships

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MiddleEarthRegion(Base):
    """Middle Earth region configuration (static data)."""

    __tablename__ = "middle_earth_regions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)

    # Map coordinates
    map_coordinates = Column(JSON, nullable=False)

    # Unlock requirements
    difficulty_level = Column(String, nullable=False)
    prerequisite_regions = Column(JSON, nullable=False, default=list)
    knowledge_points_required = Column(Integer, nullable=False, default=0)
    mastered_themes_required = Column(JSON, nullable=False, default=list)

    # Content configuration
    neo4j_community_tags = Column(JSON, nullable=False, default=list)
    available_quiz_themes = Column(JSON, nullable=False, default=list)
    lore_depth = Column(String, nullable=False, default='surface')

    # Narrative
    description = Column(Text, nullable=True)
    gandalf_introduction = Column(Text, nullable=True)
    completion_reward = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<MiddleEarthRegion(name='{self.name}', difficulty='{self.difficulty_level}')>"


class JourneyPath(Base):
    """Journey path configuration (static data)."""

    __tablename__ = "journey_paths"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Path configuration
    ordered_regions = Column(JSON, nullable=False)
    narrative_theme = Column(String, nullable=True)
    estimated_duration_hours = Column(Integer, nullable=True)

    # Unlock conditions
    unlock_condition = Column(JSON, nullable=False, default=dict)

    # Visual representation
    svg_path_data = Column(Text, nullable=True)
    path_color = Column(String, nullable=False, default='#4A90E2')

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<JourneyPath(name='{self.name}', theme='{self.narrative_theme}')>"


class UserJourneyProgress(Base):
    """User progress in a specific region."""

    __tablename__ = "user_journey_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    region_name = Column(String, nullable=False, index=True)

    # Progress metrics
    visit_count = Column(Integer, nullable=False, default=0)
    completion_percentage = Column(Integer, nullable=False, default=0)
    time_spent_minutes = Column(Integer, nullable=False, default=0)

    # Quiz performance
    quizzes_completed = Column(JSON, nullable=False, default=list)
    quiz_success_rate = Column(Float, nullable=False, default=0.0)

    # Knowledge graph learning
    concepts_encountered = Column(JSON, nullable=False, default=list)
    relationships_discovered = Column(JSON, nullable=False, default=list)
    community_mastery = Column(JSON, nullable=False, default=dict)

    # Status
    is_unlocked = Column(Boolean, nullable=False, default=False)
    is_completed = Column(Boolean, nullable=False, default=False)
    first_visited = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_visited = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        CheckConstraint('completion_percentage >= 0 AND completion_percentage <= 100', name='check_completion_percentage'),
    )

    def __repr__(self):
        return f"<UserJourneyProgress(user_id='{self.user_id}', region='{self.region_name}', {self.completion_percentage}%)>"


class UserJourneyState(Base):
    """Global journey state for a user."""

    __tablename__ = "user_journey_state"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Current state
    current_region = Column(String, nullable=True)
    current_path = Column(String, nullable=True)
    knowledge_points = Column(Integer, nullable=False, default=0)

    # Unlocked content
    unlocked_regions = Column(JSON, nullable=False, default=lambda: ["the_shire"])
    active_paths = Column(JSON, nullable=False, default=list)

    # Achievements
    achievement_badges = Column(JSON, nullable=False, default=list)
    mastered_communities = Column(JSON, nullable=False, default=list)

    # Metadata
    total_regions_completed = Column(Integer, nullable=False, default=0)
    total_quizzes_taken = Column(Integer, nullable=False, default=0)
    journey_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<UserJourneyState(user_id='{self.user_id}', region='{self.current_region}', kp={self.knowledge_points})>"


class Achievement(Base):
    """Achievement definition (static data)."""

    __tablename__ = "achievements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)

    # Unlock conditions
    unlock_criteria = Column(JSON, nullable=False)

    # Visual representation
    icon_name = Column(String, nullable=True)
    badge_color = Column(String, nullable=True)
    rarity = Column(String, nullable=False, default='common')

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Achievement(code='{self.code}', name='{self.name}', rarity='{self.rarity}')>"
