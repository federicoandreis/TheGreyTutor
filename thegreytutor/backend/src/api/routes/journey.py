"""
Journey API Routes - RESTful endpoints for the gamified Middle Earth journey system.

Provides endpoints for:
- Fetching user journey state
- Traveling to regions
- Recording quiz completion
- Getting region details
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db_session
from database.models.user import User
from src.agents.journey_agent import JourneyAgent
from src.api.deps import get_current_user_id

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/journey", tags=["journey"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TravelRequest(BaseModel):
    """Request model for traveling to a region."""
    region_name: str = Field(..., description="Name of the region to travel to")


class TravelResponse(BaseModel):
    """Response model for travel attempt."""
    success: bool = Field(..., description="Whether travel was successful")
    message: str = Field(..., description="Gandalf's narration or error message")
    region_data: Optional[Dict[str, Any]] = Field(None, description="Region information if successful")


class QuizCompletionRequest(BaseModel):
    """Request model for recording quiz completion."""
    region_name: str = Field(..., description="Region where quiz was taken")
    quiz_id: str = Field(..., description="Unique quiz identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Quiz score (0.0 to 1.0)")
    questions_answered: int = Field(..., ge=1, description="Number of questions answered")
    answers: List[Dict[str, Any]] = Field(default_factory=list, description="Array of answer objects with concept tracking")


class QuizCompletionResponse(BaseModel):
    """Response model for quiz completion."""
    knowledge_points_earned: int = Field(..., description="Knowledge points awarded")
    new_completion_percentage: int = Field(..., description="Updated region completion percentage")
    achievements_earned: List[Dict[str, Any]] = Field(default_factory=list, description="Newly unlocked achievements")
    regions_unlocked: List[str] = Field(default_factory=list, description="Newly unlocked region names")


class JourneyStateResponse(BaseModel):
    """Response model for journey state."""
    current_region: Optional[str] = Field(None, description="Current region name")
    current_path: Optional[str] = Field(None, description="Current journey path")
    knowledge_points: int = Field(..., description="Total knowledge points earned")
    unlocked_regions: List[str] = Field(..., description="List of unlocked region names")
    active_paths: List[str] = Field(default_factory=list, description="Active journey paths")
    achievement_badges: List[Dict[str, Any]] = Field(default_factory=list, description="Earned achievement badges")
    mastered_communities: List[str] = Field(default_factory=list, description="Fully mastered communities")
    total_regions_completed: int = Field(..., description="Number of regions completed")
    total_quizzes_taken: int = Field(..., description="Total quizzes taken")
    journey_started_at: Optional[str] = Field(None, description="When journey started (ISO format)")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp (ISO format)")
    region_statuses: List[Dict[str, Any]] = Field(..., description="Detailed progress for each region")
    available_paths: List[Dict[str, Any]] = Field(..., description="Available journey paths")


class RegionDetailResponse(BaseModel):
    """Response model for region details."""
    name: str = Field(..., description="Region name")
    display_name: str = Field(..., description="Human-readable region name")
    description: Optional[str] = Field(None, description="Region description")
    difficulty_level: str = Field(..., description="Difficulty level")
    map_coordinates: Dict[str, Any] = Field(..., description="Map coordinates for visualization")
    prerequisite_regions: List[str] = Field(default_factory=list, description="Required prerequisite regions")
    knowledge_points_required: int = Field(..., description="Knowledge points required to unlock")
    available_quiz_themes: List[str] = Field(default_factory=list, description="Quiz themes available in this region")
    is_unlocked: bool = Field(..., description="Whether user has unlocked this region")
    can_unlock: bool = Field(..., description="Whether user can unlock this region now")
    completion_percentage: int = Field(..., description="User's completion percentage for this region")


# ============================================================================
# Helper Functions
# ============================================================================

def get_journey_agent(db: Session = Depends(get_db_session)) -> JourneyAgent:
    """
    Dependency to create Journey Agent instance.

    Args:
        db: Database session

    Returns:
        JourneyAgent instance
    """
    # TODO: Add Neo4j driver when available
    return JourneyAgent(db_session=db, neo4j_driver=None)


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/state", response_model=JourneyStateResponse)
async def get_journey_state(
    user_id: str = Depends(get_current_user_id),
    agent: JourneyAgent = Depends(get_journey_agent)
) -> JourneyStateResponse:
    """
    Get complete journey state for the current user.

    Returns:
        Complete journey state including:
        - Current region and path
        - Knowledge points earned
        - Unlocked regions
        - Region statuses with completion percentages
        - Available journey paths
        - Earned achievements

    Raises:
        HTTPException: If error occurs fetching journey state
    """
    try:
        logger.info(f"Fetching journey state for user {user_id}")

        state = agent.get_journey_state(user_id)

        return JourneyStateResponse(**state)

    except Exception as e:
        logger.error(f"Error fetching journey state for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch journey state: {str(e)}"
        )


@router.post("/travel", response_model=TravelResponse)
async def travel_to_region(
    request: TravelRequest,
    user_id: str = Depends(get_current_user_id),
    agent: JourneyAgent = Depends(get_journey_agent)
) -> TravelResponse:
    """
    Attempt to travel to a region.

    Args:
        request: Travel request with region name

    Returns:
        Travel response with success status, Gandalf's message, and region data

    Raises:
        HTTPException: If error occurs during travel
    """
    try:
        logger.info(f"User {user_id} attempting to travel to {request.region_name}")

        success, message, region_data = agent.travel_to_region(
            user_id=user_id,
            region_name=request.region_name
        )

        return TravelResponse(
            success=success,
            message=message,
            region_data=region_data
        )

    except Exception as e:
        logger.error(f"Error during travel for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to travel to region: {str(e)}"
        )


@router.post("/complete-quiz", response_model=QuizCompletionResponse)
async def complete_quiz(
    request: QuizCompletionRequest,
    user_id: str = Depends(get_current_user_id),
    agent: JourneyAgent = Depends(get_journey_agent)
) -> QuizCompletionResponse:
    """
    Record quiz completion and award progress.

    Args:
        request: Quiz completion data

    Returns:
        Quiz completion response with:
        - Knowledge points earned
        - New completion percentage
        - Achievements earned
        - Regions unlocked

    Raises:
        HTTPException: If error occurs recording quiz completion
    """
    try:
        logger.info(
            f"User {user_id} completed quiz {request.quiz_id} "
            f"in {request.region_name} with score {request.score}"
        )

        result = agent.complete_quiz_in_region(
            user_id=user_id,
            region_name=request.region_name,
            quiz_id=request.quiz_id,
            score=request.score,
            questions_answered=request.questions_answered,
            answers=request.answers
        )

        return QuizCompletionResponse(**result)

    except Exception as e:
        logger.error(f"Error completing quiz for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record quiz completion: {str(e)}"
        )


@router.get("/regions/{region_name}", response_model=RegionDetailResponse)
async def get_region_details(
    region_name: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
) -> RegionDetailResponse:
    """
    Get detailed information about a specific region.

    Args:
        region_name: Name of the region

    Returns:
        Detailed region information including:
        - Name and description
        - Difficulty level
        - Unlock requirements
        - Available quiz themes
        - User's progress in this region

    Raises:
        HTTPException: If region not found or error occurs
    """
    try:
        from database.models.journey import MiddleEarthRegion, UserJourneyProgress

        logger.info(f"Fetching region details for {region_name}")

        # Get region
        region = db.query(MiddleEarthRegion).filter_by(name=region_name).first()
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Region '{region_name}' not found"
            )

        # Get user progress
        agent = JourneyAgent(db_session=db, neo4j_driver=None)
        can_unlock, requirements = agent._check_unlock_eligibility(user_id, region_name)

        # Get user's journey state to check if unlocked
        from database.models.journey import UserJourneyState
        state = db.query(UserJourneyState).filter_by(user_id=user_id).first()
        is_unlocked = state and region_name in state.unlocked_regions if state else False

        # Get progress
        progress = db.query(UserJourneyProgress).filter_by(
            user_id=user_id,
            region_name=region_name
        ).first()

        completion_percentage = progress.completion_percentage if progress else 0

        return RegionDetailResponse(
            name=region.name,
            display_name=region.display_name,
            description=region.description,
            difficulty_level=region.difficulty_level,
            map_coordinates=region.map_coordinates,
            prerequisite_regions=region.prerequisite_regions,
            knowledge_points_required=region.knowledge_points_required,
            available_quiz_themes=region.available_quiz_themes,
            is_unlocked=is_unlocked,
            can_unlock=can_unlock,
            completion_percentage=completion_percentage
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching region details for {region_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch region details: {str(e)}"
        )


@router.get("/regions", response_model=List[Dict[str, Any]])
async def list_all_regions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get list of all available regions with basic info.

    Returns:
        List of all regions with name, display_name, difficulty, and unlock status

    Raises:
        HTTPException: If error occurs
    """
    try:
        from database.models.journey import MiddleEarthRegion, UserJourneyState

        logger.info(f"Fetching all regions for user {user_id}")

        # Get all regions
        regions = db.query(MiddleEarthRegion).all()

        # Get user state
        state = db.query(UserJourneyState).filter_by(user_id=user_id).first()
        unlocked_regions = state.unlocked_regions if state else []

        result = []
        for region in regions:
            result.append({
                "name": region.name,
                "display_name": region.display_name,
                "difficulty_level": region.difficulty_level,
                "map_coordinates": region.map_coordinates,
                "is_unlocked": region.name in unlocked_regions,
                "knowledge_points_required": region.knowledge_points_required
            })

        return result

    except Exception as e:
        logger.error(f"Error listing regions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list regions: {str(e)}"
        )


@router.get("/paths", response_model=List[Dict[str, Any]])
async def list_journey_paths(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get list of all available journey paths.

    Returns:
        List of journey paths with details

    Raises:
        HTTPException: If error occurs
    """
    try:
        from database.models.journey import JourneyPath

        logger.info(f"Fetching journey paths for user {user_id}")

        paths = db.query(JourneyPath).all()

        result = []
        for path in paths:
            result.append({
                "name": path.name,
                "display_name": path.display_name,
                "description": path.description,
                "ordered_regions": path.ordered_regions,
                "narrative_theme": path.narrative_theme,
                "estimated_duration_hours": path.estimated_duration_hours,
                "path_color": path.path_color
            })

        return result

    except Exception as e:
        logger.error(f"Error listing journey paths: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list journey paths: {str(e)}"
        )


@router.get("/achievements", response_model=List[Dict[str, Any]])
async def list_achievements(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get list of all achievements and user's earned status.

    Returns:
        List of achievements with earned status

    Raises:
        HTTPException: If error occurs
    """
    try:
        from database.models.journey import Achievement, UserJourneyState

        logger.info(f"Fetching achievements for user {user_id}")

        # Get all achievements
        achievements = db.query(Achievement).all()

        # Get user's earned achievements
        state = db.query(UserJourneyState).filter_by(user_id=user_id).first()
        earned_codes = []
        if state and state.achievement_badges:
            earned_codes = [badge.get("code") for badge in state.achievement_badges if isinstance(badge, dict)]

        result = []
        for achievement in achievements:
            result.append({
                "code": achievement.code,
                "name": achievement.name,
                "description": achievement.description,
                "category": achievement.category,
                "rarity": achievement.rarity,
                "icon_name": achievement.icon_name,
                "badge_color": achievement.badge_color,
                "is_earned": achievement.code in earned_codes
            })

        return result

    except Exception as e:
        logger.error(f"Error listing achievements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list achievements: {str(e)}"
        )
