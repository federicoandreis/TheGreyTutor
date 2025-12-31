"""
Simplified tests for Journey Agent - focused on core logic validation.
"""
import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from src.agents.journey_agent import JourneyAgent
from database.models.journey import (
    MiddleEarthRegion,
    JourneyPath,
    UserJourneyProgress,
    UserJourneyState,
    Achievement
)


class TestJourneyAgentInitialization:
    """Tests for JourneyAgent initialization."""

    def test_init_with_db_session(self):
        """Test initialization with database session."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        assert agent.db == mock_session
        assert agent.neo4j is None

    def test_init_with_neo4j(self):
        """Test initialization with Neo4j driver."""
        mock_session = Mock(spec=Session)
        mock_neo4j = Mock()
        agent = JourneyAgent(db_session=mock_session, neo4j_driver=mock_neo4j)

        assert agent.db == mock_session
        assert agent.neo4j == mock_neo4j


class TestUnlockEligibilityLogic:
    """Tests for unlock eligibility checking."""

    def test_check_unlock_all_requirements_met(self):
        """Test unlock when all requirements are met."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        # Setup region with requirements
        region = MiddleEarthRegion(
            name="rivendell",
            knowledge_points_required=100,
            prerequisite_regions=["the_shire", "bree"],
            mastered_themes_required=[]
        )

        # Setup user state that meets requirements
        state = UserJourneyState(
            user_id="test-user",
            knowledge_points=150,
            unlocked_regions=["the_shire", "bree", "other"],
            mastered_communities=[]
        )

        # Mock database queries
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            region, state
        ]

        can_unlock, requirements = agent._check_unlock_eligibility("test-user", "rivendell")

        assert can_unlock is True
        assert requirements["knowledge_points"] is True
        assert requirements["prerequisite_regions"] is True

    def test_check_unlock_insufficient_knowledge_points(self):
        """Test unlock blocked by insufficient knowledge points."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        region = MiddleEarthRegion(
            name="mordor",
            knowledge_points_required=1000,
            prerequisite_regions=[],
            mastered_themes_required=[]
        )

        state = UserJourneyState(
            user_id="test-user",
            knowledge_points=500,
            unlocked_regions=["the_shire"],
            mastered_communities=[]
        )

        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            region, state
        ]

        can_unlock, requirements = agent._check_unlock_eligibility("test-user", "mordor")

        assert can_unlock is False
        assert requirements["knowledge_points"] is False

    def test_check_unlock_missing_prerequisites(self):
        """Test unlock blocked by missing prerequisite regions."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        region = MiddleEarthRegion(
            name="gondor",
            knowledge_points_required=100,
            prerequisite_regions=["rohan", "helm's_deep"],
            mastered_themes_required=[]
        )

        state = UserJourneyState(
            user_id="test-user",
            knowledge_points=200,
            unlocked_regions=["the_shire", "rohan"],  # Missing helm's_deep
            mastered_communities=[]
        )

        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            region, state
        ]

        can_unlock, requirements = agent._check_unlock_eligibility("test-user", "gondor")

        assert can_unlock is False
        assert requirements["prerequisite_regions"] is False

    def test_check_unlock_with_mastered_themes(self):
        """Test unlock with mastered themes requirement."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        region = MiddleEarthRegion(
            name="lothlorien",
            knowledge_points_required=200,
            prerequisite_regions=["rivendell"],
            mastered_themes_required=["elves"]
        )

        state = UserJourneyState(
            user_id="test-user",
            knowledge_points=250,
            unlocked_regions=["the_shire", "rivendell"],
            mastered_communities=["elves", "noldor"]
        )

        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            region, state
        ]

        can_unlock, requirements = agent._check_unlock_eligibility("test-user", "lothlorien")

        assert can_unlock is True
        assert requirements["mastered_themes"] is True


class TestKnowledgePointCalculation:
    """Tests for knowledge point calculation in quiz completion."""

    def test_knowledge_points_beginner_region(self):
        """Test KP calculation for beginner region."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        # Base: 100 * 0.9 = 90 points
        # Beginner multiplier: 1.0
        # Expected: 90 points

        progress = UserJourneyProgress(
            user_id="test-user",
            region_name="the_shire",
            quizzes_completed=[],
            quiz_success_rate=0.0,
            concepts_encountered=[],
            is_completed=False
        )

        region = MiddleEarthRegion(
            name="the_shire",
            difficulty_level="beginner"
        )

        state = UserJourneyState(
            user_id="test-user",
            knowledge_points=0,
            total_quizzes_taken=0,
            total_regions_completed=0,
            achievement_badges=[],
            unlocked_regions=["the_shire"]
        )

        # Create a cyclic list of responses
        def mock_filter_by(**kwargs):
            mock_result = Mock()
            # For progress queries
            if kwargs.get("region_name"):
                mock_result.first.return_value = progress
            # For state queries
            elif kwargs.get("user_id"):
                mock_result.first.return_value = state
            return mock_result

        mock_session.query.return_value.filter_by.side_effect = mock_filter_by
        mock_session.query.return_value.all.return_value = []  # No achievements

        result = agent.complete_quiz_in_region(
            user_id="test-user",
            region_name="the_shire",
            quiz_id="quiz-1",
            score=0.9,
            questions_answered=10,
            answers=[]
        )

        assert result["knowledge_points_earned"] == 90

    def test_knowledge_points_expert_region(self):
        """Test KP calculation with expert difficulty multiplier."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        # Base: 100 * 0.8 = 80 points
        # Expert multiplier: 2.5
        # Expected: 200 points

        progress = UserJourneyProgress(
            user_id="test-user",
            region_name="mordor",
            quizzes_completed=[],
            quiz_success_rate=0.0,
            concepts_encountered=[],
            is_completed=False
        )

        region = MiddleEarthRegion(
            name="mordor",
            difficulty_level="expert"
        )

        state = UserJourneyState(
            user_id="test-user",
            knowledge_points=500,
            total_quizzes_taken=0,
            total_regions_completed=0,
            achievement_badges=[],
            unlocked_regions=["the_shire", "mordor"]
        )

        # Create a flexible mock that handles multiple query patterns
        def mock_query(model):
            query_mock = Mock()
            if model.__name__ == "UserJourneyProgress":
                query_mock.filter_by.return_value.first.return_value = progress
                query_mock.all.return_value = []
            elif model.__name__ == "MiddleEarthRegion":
                query_mock.filter_by.return_value.first.return_value = region
                query_mock.all.return_value = []  # No regions to auto-unlock
            elif model.__name__ == "UserJourneyState":
                query_mock.filter_by.return_value.first.return_value = state
                query_mock.all.return_value = []
            elif model.__name__ == "Achievement":
                query_mock.all.return_value = []
            else:
                query_mock.filter_by.return_value.first.return_value = None
                query_mock.all.return_value = []
            return query_mock

        mock_session.query.side_effect = mock_query

        result = agent.complete_quiz_in_region(
            user_id="test-user",
            region_name="mordor",
            quiz_id="quiz-hard",
            score=0.8,
            questions_answered=10,
            answers=[]
        )

        assert result["knowledge_points_earned"] == 200


class TestAchievementCriteria:
    """Tests for achievement unlock criteria checking."""

    def test_achievement_visit_region(self):
        """Test achievement for visiting a region."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        achievement = Achievement(
            code="shire_visitor",
            unlock_criteria={"type": "visit_region", "region": "the_shire"}
        )

        state = UserJourneyState(
            user_id="test-user",
            unlocked_regions=["the_shire", "bree"]
        )

        mock_session.query.return_value.filter_by.return_value.first.return_value = state

        result = agent._meets_achievement_criteria("test-user", achievement)

        assert result is True

    def test_achievement_knowledge_points(self):
        """Test achievement for reaching knowledge points threshold."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        achievement = Achievement(
            code="knowledge_seeker",
            unlock_criteria={"type": "knowledge_points", "amount": 500}
        )

        state = UserJourneyState(
            user_id="test-user",
            knowledge_points=600
        )

        mock_session.query.return_value.filter_by.return_value.first.return_value = state

        result = agent._meets_achievement_criteria("test-user", achievement)

        assert result is True

    def test_achievement_knowledge_points_not_met(self):
        """Test achievement not unlocked when KP threshold not met."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        achievement = Achievement(
            code="scholar",
            unlock_criteria={"type": "knowledge_points", "amount": 1000}
        )

        state = UserJourneyState(
            user_id="test-user",
            knowledge_points=500
        )

        mock_session.query.return_value.filter_by.return_value.first.return_value = state

        result = agent._meets_achievement_criteria("test-user", achievement)

        assert result is False

    def test_achievement_complete_region(self):
        """Test achievement for completing a specific region."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        achievement = Achievement(
            code="shire_master",
            unlock_criteria={"type": "complete_region", "region": "the_shire"}
        )

        state = UserJourneyState(user_id="test-user")
        progress = UserJourneyProgress(
            user_id="test-user",
            region_name="the_shire",
            is_completed=True
        )

        def mock_query(model):
            query_mock = Mock()
            if model.__name__ == "UserJourneyState":
                query_mock.filter_by.return_value.first.return_value = state
            elif model.__name__ == "UserJourneyProgress":
                query_mock.filter_by.return_value.first.return_value = progress
            return query_mock

        mock_session.query.side_effect = mock_query

        result = agent._meets_achievement_criteria("test-user", achievement)

        assert result is True


class TestRegionQuizThemes:
    """Tests for getting quiz themes for a region."""

    def test_get_region_quiz_themes(self):
        """Test retrieving quiz themes for a region."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        region = MiddleEarthRegion(
            name="rivendell",
            available_quiz_themes=["elven_culture", "rivendell_history", "noldor_lore"]
        )

        mock_session.query.return_value.filter_by.return_value.first.return_value = region

        themes = agent._get_region_quiz_themes("rivendell")

        assert len(themes) == 3
        assert "elven_culture" in themes
        assert "rivendell_history" in themes
        assert "noldor_lore" in themes

    def test_get_region_quiz_themes_not_found(self):
        """Test retrieving quiz themes for non-existent region."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        themes = agent._get_region_quiz_themes("nonexistent")

        assert themes == []


class TestLockedMessage:
    """Tests for generating locked region messages."""

    def test_locked_message_knowledge_points(self):
        """Test message when knowledge points requirement not met."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        region = MiddleEarthRegion(
            name="Gondor",
            display_name="Gondor",
            knowledge_points_required=500
        )

        requirements = {
            "knowledge_points": False,
            "prerequisite_regions": True,
            "mastered_themes": True
        }

        message = agent._generate_locked_message(region, requirements)

        assert "Gondor" in message
        assert "500" in message
        assert "wisdom" in message.lower() or "knowledge" in message.lower()

    def test_locked_message_prerequisites(self):
        """Test message when prerequisite regions not met."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session)

        region = MiddleEarthRegion(
            name="Mordor",
            display_name="Mordor",
            knowledge_points_required=0,
            prerequisite_regions=["gondor", "rohan"]
        )

        requirements = {
            "knowledge_points": True,
            "prerequisite_regions": False,
            "mastered_themes": True
        }

        message = agent._generate_locked_message(region, requirements)

        assert "Mordor" in message
        assert "gondor" in message.lower() or "rohan" in message.lower()


class TestLoreFetching:
    """Tests for Neo4j lore fetching."""

    def test_fetch_lore_no_neo4j(self):
        """Test lore fetching when Neo4j is not available."""
        mock_session = Mock(spec=Session)
        agent = JourneyAgent(db_session=mock_session, neo4j_driver=None)

        lore = agent._fetch_region_lore("rivendell", ["elves"])

        assert lore == []

    def test_fetch_lore_success(self):
        """Test successful lore fetching from Neo4j."""
        mock_session = Mock(spec=Session)
        mock_neo4j = MagicMock()
        agent = JourneyAgent(db_session=mock_session, neo4j_driver=mock_neo4j)

        # Mock Neo4j session and results
        mock_neo4j_session = MagicMock()
        mock_neo4j.session.return_value.__enter__.return_value = mock_neo4j_session

        mock_records = [
            {"concept": "Elrond", "description": "Half-elven lord"},
            {"concept": "Vilya", "description": "Mightiest of the Three Rings"}
        ]
        mock_neo4j_session.run.return_value = mock_records

        lore = agent._fetch_region_lore("rivendell", ["elves", "noldor"])

        assert len(lore) == 2
        assert lore[0]["concept"] == "Elrond"
        assert lore[1]["concept"] == "Vilya"

    def test_fetch_lore_handles_errors(self):
        """Test that lore fetching handles Neo4j errors gracefully."""
        mock_session = Mock(spec=Session)
        mock_neo4j = MagicMock()
        agent = JourneyAgent(db_session=mock_session, neo4j_driver=mock_neo4j)

        # Mock Neo4j to raise an exception
        mock_neo4j.session.side_effect = Exception("Connection error")

        lore = agent._fetch_region_lore("rivendell", ["elves"])

        # Should return empty list instead of crashing
        assert lore == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
