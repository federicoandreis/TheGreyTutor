"""
Tests for Journey API routes.
"""
import pytest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from fastapi import FastAPI
from src.api.routes.journey import router
from database.models.user import User
from database.models.journey import (
    MiddleEarthRegion,
    UserJourneyState,
    UserJourneyProgress,
    JourneyPath,
    Achievement
)


# ============================================================================
# Test Setup
# ============================================================================

@pytest.fixture
def app():
    """Create FastAPI app with journey router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    return User(
        id="test-user-id",
        username="testuser",
        email="test@example.com"
    )


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return Mock()


@pytest.fixture
def mock_journey_agent():
    """Create mock journey agent."""
    return Mock()


# ============================================================================
# Test GET /journey/state
# ============================================================================

class TestGetJourneyState:
    """Tests for GET /journey/state endpoint."""

    def test_get_journey_state_success(self, client, mock_user, mock_journey_agent):
        """Test successful journey state retrieval."""
        # Mock the dependencies
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_journey_agent", return_value=mock_journey_agent):

            # Mock agent response
            mock_journey_agent.get_journey_state.return_value = {
                "current_region": "the_shire",
                "current_path": None,
                "knowledge_points": 150,
                "unlocked_regions": ["the_shire", "bree"],
                "active_paths": [],
                "achievement_badges": [],
                "mastered_communities": [],
                "total_regions_completed": 0,
                "total_quizzes_taken": 5,
                "journey_started_at": "2025-01-01T00:00:00",
                "last_activity": "2025-01-10T12:00:00",
                "region_statuses": [],
                "available_paths": []
            }

            response = client.get("/journey/state")

            assert response.status_code == 200
            data = response.json()
            assert data["current_region"] == "the_shire"
            assert data["knowledge_points"] == 150
            assert "the_shire" in data["unlocked_regions"]
            assert "bree" in data["unlocked_regions"]

    def test_get_journey_state_error(self, client, mock_user, mock_journey_agent):
        """Test journey state retrieval with error."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_journey_agent", return_value=mock_journey_agent):

            # Mock agent to raise exception
            mock_journey_agent.get_journey_state.side_effect = Exception("Database error")

            response = client.get("/journey/state")

            assert response.status_code == 500
            assert "Failed to fetch journey state" in response.json()["detail"]


# ============================================================================
# Test POST /journey/travel
# ============================================================================

class TestTravelToRegion:
    """Tests for POST /journey/travel endpoint."""

    def test_travel_success(self, client, mock_user, mock_journey_agent):
        """Test successful travel to unlocked region."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_journey_agent", return_value=mock_journey_agent):

            # Mock successful travel
            mock_journey_agent.travel_to_region.return_value = (
                True,
                "Welcome to Rivendell!",
                {
                    "name": "rivendell",
                    "display_name": "Rivendell",
                    "available_quiz_themes": ["elven_culture"],
                    "lore_snippets": []
                }
            )

            response = client.post("/journey/travel", json={"region_name": "rivendell"})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Rivendell" in data["message"]
            assert data["region_data"] is not None
            assert data["region_data"]["name"] == "rivendell"

    def test_travel_locked_region(self, client, mock_user, mock_journey_agent):
        """Test travel to locked region."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_journey_agent", return_value=mock_journey_agent):

            # Mock failed travel
            mock_journey_agent.travel_to_region.return_value = (
                False,
                "The path to Mordor remains closed, young scholar.",
                None
            )

            response = client.post("/journey/travel", json={"region_name": "mordor"})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "closed" in data["message"].lower()
            assert data["region_data"] is None

    def test_travel_invalid_region(self, client, mock_user, mock_journey_agent):
        """Test travel to non-existent region."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_journey_agent", return_value=mock_journey_agent):

            # Mock region not found
            mock_journey_agent.travel_to_region.return_value = (
                False,
                "Region 'fake_region' does not exist in Middle Earth!",
                None
            )

            response = client.post("/journey/travel", json={"region_name": "fake_region"})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "not exist" in data["message"].lower()


# ============================================================================
# Test POST /journey/complete-quiz
# ============================================================================

class TestCompleteQuiz:
    """Tests for POST /journey/complete-quiz endpoint."""

    def test_complete_quiz_success(self, client, mock_user, mock_journey_agent):
        """Test successful quiz completion."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_journey_agent", return_value=mock_journey_agent):

            # Mock quiz completion
            mock_journey_agent.complete_quiz_in_region.return_value = {
                "knowledge_points_earned": 90,
                "new_completion_percentage": 45,
                "achievements_earned": [],
                "regions_unlocked": []
            }

            request_data = {
                "region_name": "the_shire",
                "quiz_id": "quiz-123",
                "score": 0.9,
                "questions_answered": 10,
                "answers": []
            }

            response = client.post("/journey/complete-quiz", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["knowledge_points_earned"] == 90
            assert data["new_completion_percentage"] == 45
            assert isinstance(data["achievements_earned"], list)
            assert isinstance(data["regions_unlocked"], list)

    def test_complete_quiz_with_achievements(self, client, mock_user, mock_journey_agent):
        """Test quiz completion that unlocks achievements."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_journey_agent", return_value=mock_journey_agent):

            # Mock quiz completion with achievements
            mock_journey_agent.complete_quiz_in_region.return_value = {
                "knowledge_points_earned": 100,
                "new_completion_percentage": 100,
                "achievements_earned": [
                    {
                        "code": "shire_master",
                        "name": "Shire Master",
                        "rarity": "rare"
                    }
                ],
                "regions_unlocked": ["bree"]
            }

            request_data = {
                "region_name": "the_shire",
                "quiz_id": "quiz-final",
                "score": 1.0,
                "questions_answered": 10,
                "answers": []
            }

            response = client.post("/journey/complete-quiz", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["knowledge_points_earned"] == 100
            assert data["new_completion_percentage"] == 100
            assert len(data["achievements_earned"]) == 1
            assert data["achievements_earned"][0]["code"] == "shire_master"
            assert "bree" in data["regions_unlocked"]

    def test_complete_quiz_invalid_score(self, client, mock_user):
        """Test quiz completion with invalid score."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user):

            request_data = {
                "region_name": "the_shire",
                "quiz_id": "quiz-123",
                "score": 1.5,  # Invalid: > 1.0
                "questions_answered": 10,
                "answers": []
            }

            response = client.post("/journey/complete-quiz", json=request_data)

            assert response.status_code == 422  # Validation error


# ============================================================================
# Test GET /journey/regions/{region_name}
# ============================================================================

class TestGetRegionDetails:
    """Tests for GET /journey/regions/{region_name} endpoint."""

    def test_get_region_details_success(self, client, mock_user, mock_db_session):
        """Test successful region details retrieval."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_db_session", return_value=mock_db_session):

            # Mock region
            region = MiddleEarthRegion(
                name="rivendell",
                display_name="Rivendell",
                description="The Last Homely House",
                difficulty_level="intermediate",
                map_coordinates={"x": 300, "y": 250},
                prerequisite_regions=["bree"],
                knowledge_points_required=150,
                available_quiz_themes=["elven_culture"]
            )

            # Mock user state
            state = UserJourneyState(
                user_id="test-user-id",
                unlocked_regions=["the_shire", "bree", "rivendell"]
            )

            # Mock progress
            progress = UserJourneyProgress(
                user_id="test-user-id",
                region_name="rivendell",
                completion_percentage=45
            )

            # Setup database mocks
            def mock_query(model):
                query_mock = Mock()
                if model.__name__ == "MiddleEarthRegion":
                    query_mock.filter_by.return_value.first.return_value = region
                elif model.__name__ == "UserJourneyState":
                    query_mock.filter_by.return_value.first.return_value = state
                elif model.__name__ == "UserJourneyProgress":
                    query_mock.filter_by.return_value.first.return_value = progress
                return query_mock

            mock_db_session.query.side_effect = mock_query

            response = client.get("/journey/regions/rivendell")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "rivendell"
            assert data["display_name"] == "Rivendell"
            assert data["difficulty_level"] == "intermediate"
            assert data["is_unlocked"] is True
            assert data["completion_percentage"] == 45

    def test_get_region_details_not_found(self, client, mock_user, mock_db_session):
        """Test region details for non-existent region."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_db_session", return_value=mock_db_session):

            # Mock region not found
            mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

            response = client.get("/journey/regions/fake_region")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


# ============================================================================
# Test GET /journey/regions
# ============================================================================

class TestListAllRegions:
    """Tests for GET /journey/regions endpoint."""

    def test_list_regions_success(self, client, mock_user, mock_db_session):
        """Test successful listing of all regions."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_db_session", return_value=mock_db_session):

            # Mock regions
            regions = [
                MiddleEarthRegion(
                    name="the_shire",
                    display_name="The Shire",
                    difficulty_level="beginner",
                    map_coordinates={"x": 150, "y": 200},
                    knowledge_points_required=0
                ),
                MiddleEarthRegion(
                    name="rivendell",
                    display_name="Rivendell",
                    difficulty_level="intermediate",
                    map_coordinates={"x": 300, "y": 250},
                    knowledge_points_required=150
                )
            ]

            # Mock user state
            state = UserJourneyState(
                user_id="test-user-id",
                unlocked_regions=["the_shire"]
            )

            # Setup database mocks
            def mock_query(model):
                query_mock = Mock()
                if model.__name__ == "MiddleEarthRegion":
                    query_mock.all.return_value = regions
                elif model.__name__ == "UserJourneyState":
                    query_mock.filter_by.return_value.first.return_value = state
                return query_mock

            mock_db_session.query.side_effect = mock_query

            response = client.get("/journey/regions")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "the_shire"
            assert data[0]["is_unlocked"] is True
            assert data[1]["name"] == "rivendell"
            assert data[1]["is_unlocked"] is False


# ============================================================================
# Test GET /journey/paths
# ============================================================================

class TestListJourneyPaths:
    """Tests for GET /journey/paths endpoint."""

    def test_list_paths_success(self, client, mock_user, mock_db_session):
        """Test successful listing of journey paths."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_db_session", return_value=mock_db_session):

            # Mock paths
            paths = [
                JourneyPath(
                    name="fellowship_path",
                    display_name="The Fellowship Path",
                    description="Follow the journey of the Fellowship",
                    ordered_regions=["the_shire", "bree", "rivendell"],
                    narrative_theme="fellowship",
                    estimated_duration_hours=20,
                    path_color="#4A90E2"
                )
            ]

            mock_db_session.query.return_value.all.return_value = paths

            response = client.get("/journey/paths")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "fellowship_path"
            assert data[0]["display_name"] == "The Fellowship Path"
            assert len(data[0]["ordered_regions"]) == 3


# ============================================================================
# Test GET /journey/achievements
# ============================================================================

class TestListAchievements:
    """Tests for GET /journey/achievements endpoint."""

    def test_list_achievements_success(self, client, mock_user, mock_db_session):
        """Test successful listing of achievements."""
        with patch("src.api.routes.journey.get_current_user", return_value=mock_user), \
             patch("src.api.routes.journey.get_db_session", return_value=mock_db_session):

            # Mock achievements
            achievements = [
                Achievement(
                    code="first_steps",
                    name="First Steps",
                    description="Visit The Shire",
                    category="region",
                    rarity="common",
                    icon_name="footprints",
                    badge_color="#8B4513",
                    unlock_criteria={"type": "visit_region", "region": "the_shire"}
                ),
                Achievement(
                    code="knowledge_seeker",
                    name="Knowledge Seeker",
                    description="Earn 100 knowledge points",
                    category="knowledge",
                    rarity="rare",
                    icon_name="scroll",
                    badge_color="#FFD700",
                    unlock_criteria={"type": "knowledge_points", "amount": 100}
                )
            ]

            # Mock user state with one earned achievement
            state = UserJourneyState(
                user_id="test-user-id",
                achievement_badges=[{"code": "first_steps"}]
            )

            # Setup database mocks
            def mock_query(model):
                query_mock = Mock()
                if model.__name__ == "Achievement":
                    query_mock.all.return_value = achievements
                elif model.__name__ == "UserJourneyState":
                    query_mock.filter_by.return_value.first.return_value = state
                return query_mock

            mock_db_session.query.side_effect = mock_query

            response = client.get("/journey/achievements")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["code"] == "first_steps"
            assert data[0]["is_earned"] is True
            assert data[1]["code"] == "knowledge_seeker"
            assert data[1]["is_earned"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
