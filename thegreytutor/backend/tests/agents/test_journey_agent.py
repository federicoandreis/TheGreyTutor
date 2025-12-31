"""
Tests for Journey Agent - Core logic for gamified journey system.
"""
import pytest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.agents.journey_agent import JourneyAgent
from database.models.journey import (
    MiddleEarthRegion,
    JourneyPath,
    UserJourneyProgress,
    UserJourneyState,
    Achievement
)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_neo4j_driver():
    """Create a mock Neo4j driver."""
    return Mock()


@pytest.fixture
def journey_agent(mock_db_session, mock_neo4j_driver):
    """Create JourneyAgent instance with mocked dependencies."""
    return JourneyAgent(db_session=mock_db_session, neo4j_driver=mock_neo4j_driver)


@pytest.fixture
def sample_user_state():
    """Create a sample user journey state."""
    return UserJourneyState(
        user_id="test-user-id",
        current_region="the_shire",
        knowledge_points=150,
        unlocked_regions=["the_shire", "bree"],
        active_paths=[],
        achievement_badges=[],
        mastered_communities=[],
        total_regions_completed=0,
        total_quizzes_taken=5,
        journey_started_at=datetime.utcnow(),
        last_activity=datetime.utcnow()
    )


@pytest.fixture
def sample_region():
    """Create a sample Middle Earth region."""
    return MiddleEarthRegion(
        name="rivendell",
        display_name="Rivendell",
        map_coordinates={"x": 300, "y": 250, "radius": 30},
        difficulty_level="intermediate",
        prerequisite_regions=["bree"],
        knowledge_points_required=150,
        mastered_themes_required=[],
        neo4j_community_tags=["elves", "noldor"],
        available_quiz_themes=["elven_culture", "rivendell_history"],
        lore_depth="deep",
        description="The house of Elrond, a sanctuary of wisdom.",
        gandalf_introduction="Ah, Rivendell! The Last Homely House. Here ancient wisdom dwells.",
        completion_reward="Elven Scroll"
    )


@pytest.fixture
def sample_progress():
    """Create sample user journey progress."""
    return UserJourneyProgress(
        user_id="test-user-id",
        region_name="the_shire",
        visit_count=3,
        completion_percentage=45,
        time_spent_minutes=120,
        quizzes_completed=["quiz-1", "quiz-2"],
        quiz_success_rate=0.85,
        concepts_encountered=["hobbits", "pipeweed"],
        relationships_discovered=[],
        community_mastery={},
        is_unlocked=True,
        is_completed=False,
        first_visited=datetime.utcnow(),
        last_visited=datetime.utcnow()
    )


class TestJourneyAgentGetJourneyState:
    """Tests for get_journey_state method."""

    def test_get_journey_state_existing_user(
        self, journey_agent, mock_db_session, sample_user_state, sample_region, sample_progress
    ):
        """Test fetching journey state for existing user."""
        # Create a list of mock queries that will be called in sequence
        queries_called = []

        def mock_query(model):
            query_mock = Mock()
            queries_called.append(model.__name__)

            if model.__name__ == "UserJourneyState":
                query_mock.filter_by.return_value.first.return_value = sample_user_state
            elif model.__name__ == "MiddleEarthRegion":
                query_mock.all.return_value = [sample_region]
            elif model.__name__ == "UserJourneyProgress":
                # This will be called multiple times
                def mock_filter_by(**kwargs):
                    mock_result = Mock()
                    if kwargs.get("region_name") == "rivendell":
                        mock_result.first.return_value = None
                    else:
                        mock_result.first.return_value = sample_progress
                    return mock_result
                query_mock.filter_by.side_effect = mock_filter_by
            elif model.__name__ == "JourneyPath":
                query_mock.all.return_value = []

            return query_mock

        mock_db_session.query.side_effect = mock_query

        result = journey_agent.get_journey_state("test-user-id")

        assert result["current_region"] == "the_shire"
        assert result["knowledge_points"] == 150
        assert "the_shire" in result["unlocked_regions"]
        assert "bree" in result["unlocked_regions"]
        assert isinstance(result["region_statuses"], list)

    def test_get_journey_state_new_user(self, journey_agent, mock_db_session):
        """Test creating default journey state for new user."""
        # Mock no existing state
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = journey_agent.get_journey_state("new-user-id")

        # Should create new state
        assert mock_db_session.add.called
        assert mock_db_session.commit.called


class TestJourneyAgentTravelToRegion:
    """Tests for travel_to_region method."""

    def test_travel_to_unlocked_region_success(
        self, journey_agent, mock_db_session, sample_user_state, sample_region, sample_progress
    ):
        """Test successful travel to already unlocked region."""
        sample_user_state.unlocked_regions = ["the_shire", "bree", "rivendell"]

        # Mock queries
        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_region,  # Region query
            sample_user_state,  # State query
            sample_progress  # Progress query
        ]

        success, message, region_data = journey_agent.travel_to_region("test-user-id", "rivendell")

        assert success is True
        assert "Rivendell" in message
        assert region_data is not None
        assert region_data["name"] == "rivendell"
        assert "available_quiz_themes" in region_data
        assert mock_db_session.commit.called

    def test_travel_to_locked_region_failure(
        self, journey_agent, mock_db_session, sample_user_state, sample_region
    ):
        """Test traveling to locked region fails with message."""
        sample_user_state.unlocked_regions = ["the_shire"]
        sample_user_state.knowledge_points = 50  # Not enough

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_region,  # Region query
            sample_user_state  # State query
        ]

        success, message, region_data = journey_agent.travel_to_region("test-user-id", "rivendell")

        assert success is False
        assert "closed" in message.lower() or "locked" in message.lower()
        assert region_data is None

    def test_travel_to_nonexistent_region(self, journey_agent, mock_db_session):
        """Test traveling to non-existent region."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        success, message, region_data = journey_agent.travel_to_region("test-user-id", "fake_region")

        assert success is False
        assert "not exist" in message.lower()
        assert region_data is None

    def test_travel_increments_visit_count(
        self, journey_agent, mock_db_session, sample_user_state, sample_region, sample_progress
    ):
        """Test that traveling increments visit count."""
        sample_user_state.unlocked_regions = ["the_shire", "rivendell"]
        initial_visits = sample_progress.visit_count

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_region,
            sample_user_state,
            sample_progress
        ]

        journey_agent.travel_to_region("test-user-id", "rivendell")

        assert sample_progress.visit_count == initial_visits + 1

    def test_travel_creates_progress_if_not_exists(
        self, journey_agent, mock_db_session, sample_user_state, sample_region
    ):
        """Test that traveling creates progress record if it doesn't exist."""
        sample_user_state.unlocked_regions = ["the_shire", "rivendell"]

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_region,
            sample_user_state,
            None  # No existing progress
        ]

        journey_agent.travel_to_region("test-user-id", "rivendell")

        assert mock_db_session.add.called


class TestJourneyAgentCompleteQuiz:
    """Tests for complete_quiz_in_region method."""

    def test_complete_quiz_awards_knowledge_points(
        self, journey_agent, mock_db_session, sample_user_state, sample_region, sample_progress
    ):
        """Test that completing quiz awards knowledge points."""
        initial_kp = sample_user_state.knowledge_points

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_progress,  # Progress query
            sample_region,  # Region query
            sample_user_state  # State query
        ]

        result = journey_agent.complete_quiz_in_region(
            user_id="test-user-id",
            region_name="the_shire",
            quiz_id="quiz-3",
            score=0.9,
            questions_answered=10,
            answers=[]
        )

        assert result["knowledge_points_earned"] > 0
        assert sample_user_state.knowledge_points > initial_kp
        assert mock_db_session.commit.called

    def test_complete_quiz_difficulty_multiplier(
        self, journey_agent, mock_db_session, sample_user_state, sample_progress
    ):
        """Test that quiz completion uses difficulty multiplier."""
        # Expert region
        expert_region = MiddleEarthRegion(
            name="mordor",
            difficulty_level="expert"
        )

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_progress,
            expert_region,
            sample_user_state
        ]

        result = journey_agent.complete_quiz_in_region(
            user_id="test-user-id",
            region_name="mordor",
            quiz_id="quiz-hard",
            score=0.8,
            questions_answered=10,
            answers=[]
        )

        # Expert multiplier is 2.5, so 100 * 0.8 * 2.5 = 200
        assert result["knowledge_points_earned"] == 200

    def test_complete_quiz_updates_completion_percentage(
        self, journey_agent, mock_db_session, sample_user_state, sample_region, sample_progress
    ):
        """Test that quiz completion updates completion percentage."""
        initial_percentage = sample_progress.completion_percentage

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_progress,
            sample_region,
            sample_user_state
        ]

        result = journey_agent.complete_quiz_in_region(
            user_id="test-user-id",
            region_name="the_shire",
            quiz_id="quiz-3",
            score=0.95,
            questions_answered=10,
            answers=[]
        )

        assert result["new_completion_percentage"] >= initial_percentage

    def test_complete_quiz_tracks_concepts(
        self, journey_agent, mock_db_session, sample_user_state, sample_region, sample_progress
    ):
        """Test that quiz completion tracks encountered concepts."""
        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_progress,
            sample_region,
            sample_user_state
        ]

        answers = [
            {"concepts": ["gandalf", "frodo"]},
            {"concepts": ["bilbo"]}
        ]

        journey_agent.complete_quiz_in_region(
            user_id="test-user-id",
            region_name="the_shire",
            quiz_id="quiz-3",
            score=0.85,
            questions_answered=10,
            answers=answers
        )

        assert "gandalf" in sample_progress.concepts_encountered
        assert "frodo" in sample_progress.concepts_encountered
        assert "bilbo" in sample_progress.concepts_encountered

    def test_complete_quiz_marks_region_completed(
        self, journey_agent, mock_db_session, sample_user_state, sample_region, sample_progress
    ):
        """Test that 100% completion marks region as completed."""
        # Simulate already having 9 quizzes completed with high success rate
        sample_progress.quizzes_completed = [f"quiz-{i}" for i in range(9)]
        sample_progress.quiz_success_rate = 0.95

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_progress,
            sample_region,
            sample_user_state
        ]

        journey_agent.complete_quiz_in_region(
            user_id="test-user-id",
            region_name="the_shire",
            quiz_id="quiz-10",
            score=1.0,
            questions_answered=10,
            answers=[]
        )

        assert sample_progress.is_completed is True
        assert sample_progress.completed_at is not None

    def test_complete_quiz_no_progress_record(
        self, journey_agent, mock_db_session
    ):
        """Test quiz completion when no progress record exists."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = journey_agent.complete_quiz_in_region(
            user_id="test-user-id",
            region_name="the_shire",
            quiz_id="quiz-1",
            score=0.8,
            questions_answered=10,
            answers=[]
        )

        assert result["knowledge_points_earned"] == 0
        assert result["new_completion_percentage"] == 0


class TestJourneyAgentUnlockEligibility:
    """Tests for _check_unlock_eligibility method."""

    def test_unlock_eligibility_all_requirements_met(
        self, journey_agent, mock_db_session, sample_user_state, sample_region
    ):
        """Test unlock eligibility when all requirements are met."""
        sample_user_state.knowledge_points = 200
        sample_user_state.unlocked_regions = ["the_shire", "bree"]

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_region,
            sample_user_state
        ]

        can_unlock, requirements = journey_agent._check_unlock_eligibility(
            "test-user-id", "rivendell"
        )

        assert can_unlock is True
        assert requirements["knowledge_points"] is True
        assert requirements["prerequisite_regions"] is True

    def test_unlock_eligibility_insufficient_knowledge_points(
        self, journey_agent, mock_db_session, sample_user_state, sample_region
    ):
        """Test unlock eligibility with insufficient knowledge points."""
        sample_user_state.knowledge_points = 50
        sample_user_state.unlocked_regions = ["the_shire", "bree"]

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_region,
            sample_user_state
        ]

        can_unlock, requirements = journey_agent._check_unlock_eligibility(
            "test-user-id", "rivendell"
        )

        assert can_unlock is False
        assert requirements["knowledge_points"] is False

    def test_unlock_eligibility_missing_prerequisites(
        self, journey_agent, mock_db_session, sample_user_state, sample_region
    ):
        """Test unlock eligibility with missing prerequisite regions."""
        sample_user_state.knowledge_points = 200
        sample_user_state.unlocked_regions = ["the_shire"]  # Missing "bree"

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_region,
            sample_user_state
        ]

        can_unlock, requirements = journey_agent._check_unlock_eligibility(
            "test-user-id", "rivendell"
        )

        assert can_unlock is False
        assert requirements["prerequisite_regions"] is False

    def test_unlock_eligibility_with_mastered_themes(
        self, journey_agent, mock_db_session, sample_user_state, sample_region
    ):
        """Test unlock eligibility with mastered themes requirement."""
        sample_region.mastered_themes_required = ["elves"]
        sample_user_state.knowledge_points = 200
        sample_user_state.unlocked_regions = ["the_shire", "bree"]
        sample_user_state.mastered_communities = ["elves"]

        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_region,
            sample_user_state
        ]

        can_unlock, requirements = journey_agent._check_unlock_eligibility(
            "test-user-id", "rivendell"
        )

        assert can_unlock is True
        assert requirements["mastered_themes"] is True


class TestJourneyAgentAchievements:
    """Tests for achievement checking functionality."""

    def test_check_achievements_visit_region(
        self, journey_agent, mock_db_session, sample_user_state
    ):
        """Test achievement unlocked by visiting a region."""
        achievement = Achievement(
            code="first_steps",
            name="First Steps",
            description="Visit The Shire",
            category="region",
            unlock_criteria={"type": "visit_region", "region": "the_shire"},
            rarity="common"
        )

        sample_user_state.achievement_badges = []

        mock_db_session.query.return_value.filter_by.return_value.first.return_value = sample_user_state
        mock_db_session.query.return_value.all.return_value = [achievement]

        newly_earned = journey_agent._check_achievements("test-user-id")

        assert len(newly_earned) == 1
        assert newly_earned[0]["code"] == "first_steps"

    def test_check_achievements_knowledge_points(
        self, journey_agent, mock_db_session, sample_user_state
    ):
        """Test achievement unlocked by reaching knowledge points threshold."""
        achievement = Achievement(
            code="knowledge_seeker",
            name="Knowledge Seeker",
            description="Earn 100 knowledge points",
            category="knowledge",
            unlock_criteria={"type": "knowledge_points", "amount": 100},
            rarity="common"
        )

        sample_user_state.knowledge_points = 150
        sample_user_state.achievement_badges = []

        mock_db_session.query.return_value.filter_by.return_value.first.return_value = sample_user_state
        mock_db_session.query.return_value.all.return_value = [achievement]

        newly_earned = journey_agent._check_achievements("test-user-id")

        assert len(newly_earned) == 1
        assert newly_earned[0]["code"] == "knowledge_seeker"

    def test_check_achievements_already_earned(
        self, journey_agent, mock_db_session, sample_user_state
    ):
        """Test that already earned achievements are not awarded again."""
        achievement = Achievement(
            code="first_steps",
            name="First Steps",
            description="Visit The Shire",
            category="region",
            unlock_criteria={"type": "visit_region", "region": "the_shire"},
            rarity="common"
        )

        sample_user_state.achievement_badges = [{"code": "first_steps"}]

        mock_db_session.query.return_value.filter_by.return_value.first.return_value = sample_user_state
        mock_db_session.query.return_value.all.return_value = [achievement]

        newly_earned = journey_agent._check_achievements("test-user-id")

        assert len(newly_earned) == 0


class TestJourneyAgentRegionUnlocks:
    """Tests for region unlock checking."""

    def test_check_region_unlocks_new_region(
        self, journey_agent, mock_db_session, sample_user_state
    ):
        """Test that new regions are unlocked when requirements are met."""
        rivendell = MiddleEarthRegion(
            name="rivendell",
            prerequisite_regions=["bree"],
            knowledge_points_required=100,
            mastered_themes_required=[]
        )

        sample_user_state.knowledge_points = 200
        sample_user_state.unlocked_regions = ["the_shire", "bree"]

        mock_db_session.query.return_value.filter_by.return_value.first.return_value = sample_user_state
        mock_db_session.query.return_value.all.return_value = [rivendell]

        newly_unlocked = journey_agent._check_region_unlocks("test-user-id")

        assert "rivendell" in newly_unlocked
        assert "rivendell" in sample_user_state.unlocked_regions
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    def test_check_region_unlocks_no_new_regions(
        self, journey_agent, mock_db_session, sample_user_state
    ):
        """Test when no new regions can be unlocked."""
        rivendell = MiddleEarthRegion(
            name="rivendell",
            prerequisite_regions=["bree"],
            knowledge_points_required=500,  # Too high
            mastered_themes_required=[]
        )

        sample_user_state.knowledge_points = 150
        sample_user_state.unlocked_regions = ["the_shire", "bree"]

        mock_db_session.query.return_value.filter_by.return_value.first.return_value = sample_user_state
        mock_db_session.query.return_value.all.return_value = [rivendell]

        newly_unlocked = journey_agent._check_region_unlocks("test-user-id")

        assert len(newly_unlocked) == 0


class TestJourneyAgentLoreFetching:
    """Tests for Neo4j lore fetching."""

    def test_fetch_region_lore_success(self, journey_agent, mock_neo4j_driver):
        """Test successful lore fetching from Neo4j."""
        mock_session = MagicMock()
        mock_neo4j_driver.session.return_value.__enter__.return_value = mock_session

        mock_result = [
            {"concept": "Elrond", "description": "Half-elven lord of Rivendell"},
            {"concept": "Vilya", "description": "The mightiest of the Three Rings"}
        ]
        mock_session.run.return_value = mock_result

        lore_snippets = journey_agent._fetch_region_lore(
            "rivendell",
            ["elves", "noldor"]
        )

        assert len(lore_snippets) == 2
        assert lore_snippets[0]["concept"] == "Elrond"

    def test_fetch_region_lore_no_neo4j(self, mock_db_session):
        """Test lore fetching when Neo4j is not available."""
        agent = JourneyAgent(db_session=mock_db_session, neo4j_driver=None)

        lore_snippets = agent._fetch_region_lore("rivendell", ["elves"])

        assert len(lore_snippets) == 0

    def test_fetch_region_lore_error_handling(self, journey_agent, mock_neo4j_driver):
        """Test lore fetching handles Neo4j errors gracefully."""
        mock_session = MagicMock()
        mock_neo4j_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.side_effect = Exception("Neo4j connection error")

        lore_snippets = journey_agent._fetch_region_lore("rivendell", ["elves"])

        # Should return empty list instead of crashing
        assert len(lore_snippets) == 0
