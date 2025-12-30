"""
Journey Agent - Core logic for the gamified Middle Earth map journey system.

This agent manages:
- Region unlock eligibility and progression
- Knowledge point calculation and awarding
- Achievement checking and unlocking
- User journey state tracking
- Integration with Neo4j for content discovery
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models.journey import (
    MiddleEarthRegion,
    JourneyPath,
    UserJourneyProgress,
    UserJourneyState,
    Achievement
)
from database.models.user import User

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JourneyAgent:
    """
    Journey Agent manages the gamified progression through Middle Earth.

    Responsibilities:
    - Check region unlock eligibility
    - Award knowledge points for quiz completion
    - Track user progress per region
    - Manage achievement unlocking
    - Provide region-specific content recommendations
    """

    def __init__(self, db_session: Session, neo4j_driver=None):
        """
        Initialize Journey Agent.

        Args:
            db_session: SQLAlchemy database session
            neo4j_driver: Optional Neo4j driver for content discovery
        """
        self.db = db_session
        self.neo4j = neo4j_driver
        logger.info("Journey Agent initialized")

    def get_journey_state(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete journey state for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            Dictionary containing:
            - current_region: Current region name
            - knowledge_points: Total knowledge points earned
            - unlocked_regions: List of unlocked region names
            - region_statuses: Detailed progress for each region
            - available_paths: Journey paths the user can follow
            - achievements: List of earned achievements
        """
        logger.info(f"Fetching journey state for user {user_id}")

        # Get or create user journey state
        state = self.db.query(UserJourneyState).filter_by(user_id=user_id).first()
        if not state:
            logger.warning(f"No journey state found for user {user_id}, creating default state")
            state = UserJourneyState(
                user_id=user_id,
                knowledge_points=0,
                unlocked_regions=["the_shire"],
                current_region="the_shire"
            )
            self.db.add(state)
            self.db.commit()

        # Get all regions with unlock status
        all_regions = self.db.query(MiddleEarthRegion).all()
        region_statuses = []

        for region in all_regions:
            progress = self.db.query(UserJourneyProgress).filter_by(
                user_id=user_id,
                region_name=region.name
            ).first()

            is_unlocked = region.name in state.unlocked_regions
            can_unlock, requirements = self._check_unlock_eligibility(user_id, region.name)

            region_statuses.append({
                "name": region.name,
                "display_name": region.display_name,
                "difficulty_level": region.difficulty_level,
                "is_unlocked": is_unlocked,
                "can_unlock": can_unlock,
                "unlock_requirements": requirements,
                "completion_percentage": progress.completion_percentage if progress else 0,
                "visit_count": progress.visit_count if progress else 0,
                "is_completed": progress.is_completed if progress else False,
                "map_coordinates": region.map_coordinates
            })

        # Get available paths
        all_paths = self.db.query(JourneyPath).all()
        available_paths = [
            {
                "name": path.name,
                "display_name": path.display_name,
                "description": path.description,
                "ordered_regions": path.ordered_regions,
                "narrative_theme": path.narrative_theme,
                "estimated_duration_hours": path.estimated_duration_hours,
                "path_color": path.path_color
            }
            for path in all_paths
        ]

        return {
            "current_region": state.current_region,
            "current_path": state.current_path,
            "knowledge_points": state.knowledge_points,
            "unlocked_regions": state.unlocked_regions,
            "active_paths": state.active_paths,
            "achievement_badges": state.achievement_badges,
            "mastered_communities": state.mastered_communities,
            "total_regions_completed": state.total_regions_completed,
            "total_quizzes_taken": state.total_quizzes_taken,
            "journey_started_at": state.journey_started_at.isoformat() if state.journey_started_at else None,
            "last_activity": state.last_activity.isoformat() if state.last_activity else None,
            "region_statuses": region_statuses,
            "available_paths": available_paths
        }

    def travel_to_region(self, user_id: str, region_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Attempt to travel to a region.

        Args:
            user_id: User's unique identifier
            region_name: Name of the region to travel to

        Returns:
            Tuple of (success, message, region_data)
            - success: Whether travel was successful
            - message: Gandalf's narration or error message
            - region_data: Region information if successful, None otherwise
        """
        logger.info(f"User {user_id} attempting to travel to {region_name}")

        # Get region
        region = self.db.query(MiddleEarthRegion).filter_by(name=region_name).first()
        if not region:
            logger.error(f"Region {region_name} not found")
            return False, f"Region '{region_name}' does not exist in Middle Earth!", None

        # Check if unlocked
        state = self.db.query(UserJourneyState).filter_by(user_id=user_id).first()
        if region_name not in state.unlocked_regions:
            # Check if can unlock
            can_unlock, requirements = self._check_unlock_eligibility(user_id, region_name)
            if not can_unlock:
                unmet_reqs = [k for k, v in requirements.items() if not v]
                logger.warning(f"User {user_id} cannot unlock {region_name}. Unmet: {unmet_reqs}")
                return False, self._generate_locked_message(region, requirements), None

        # Get or create progress record
        progress = self.db.query(UserJourneyProgress).filter_by(
            user_id=user_id,
            region_name=region_name
        ).first()

        if not progress:
            progress = UserJourneyProgress(
                user_id=user_id,
                region_name=region_name,
                is_unlocked=True,
                visit_count=0
            )
            self.db.add(progress)

        # Update progress
        progress.visit_count += 1
        progress.last_visited = datetime.utcnow()
        if progress.visit_count == 1:
            progress.first_visited = datetime.utcnow()

        # Update user state
        state.current_region = region_name
        state.last_activity = datetime.utcnow()

        # Ensure region is in unlocked list
        if region_name not in state.unlocked_regions:
            unlocked_list = state.unlocked_regions.copy() if isinstance(state.unlocked_regions, list) else []
            unlocked_list.append(region_name)
            state.unlocked_regions = unlocked_list
            progress.is_unlocked = True

        self.db.commit()

        # Get quiz themes for this region
        quiz_themes = self._get_region_quiz_themes(region_name)

        # Get lore snippets from Neo4j if available
        lore_snippets = []
        if self.neo4j:
            lore_snippets = self._fetch_region_lore(region_name, region.neo4j_community_tags)

        region_data = {
            "name": region.name,
            "display_name": region.display_name,
            "description": region.description,
            "difficulty_level": region.difficulty_level,
            "lore_depth": region.lore_depth,
            "available_quiz_themes": quiz_themes,
            "lore_snippets": lore_snippets,
            "visit_count": progress.visit_count,
            "completion_percentage": progress.completion_percentage
        }

        message = region.gandalf_introduction or f"Welcome to {region.display_name}!"
        logger.info(f"User {user_id} successfully traveled to {region_name}")

        return True, message, region_data

    def complete_quiz_in_region(
        self,
        user_id: str,
        region_name: str,
        quiz_id: str,
        score: float,
        questions_answered: int,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Record quiz completion and award progress.

        Args:
            user_id: User's unique identifier
            region_name: Region where quiz was taken
            quiz_id: Quiz identifier
            score: Quiz score (0.0 to 1.0)
            questions_answered: Number of questions answered
            answers: List of answer objects with concept tracking

        Returns:
            Dictionary containing:
            - knowledge_points_earned: Points awarded
            - new_completion_percentage: Updated completion percentage
            - achievements_earned: List of newly unlocked achievements
            - regions_unlocked: List of newly unlocked regions
        """
        logger.info(f"Recording quiz completion for user {user_id} in {region_name}")

        # Get progress record
        progress = self.db.query(UserJourneyProgress).filter_by(
            user_id=user_id,
            region_name=region_name
        ).first()

        if not progress:
            logger.error(f"No progress record found for user {user_id} in {region_name}")
            return {
                "knowledge_points_earned": 0,
                "new_completion_percentage": 0,
                "achievements_earned": [],
                "regions_unlocked": []
            }

        # Calculate knowledge points (base 100 points per quiz * score)
        knowledge_points = int(100 * score)

        # Bonus for difficulty
        region = self.db.query(MiddleEarthRegion).filter_by(name=region_name).first()
        if region:
            difficulty_multiplier = {
                "beginner": 1.0,
                "intermediate": 1.5,
                "advanced": 2.0,
                "expert": 2.5
            }.get(region.difficulty_level, 1.0)
            knowledge_points = int(knowledge_points * difficulty_multiplier)

        # Update progress
        quizzes_completed = progress.quizzes_completed.copy() if isinstance(progress.quizzes_completed, list) else []
        if quiz_id not in quizzes_completed:
            quizzes_completed.append(quiz_id)
        progress.quizzes_completed = quizzes_completed

        # Update success rate
        total_quizzes = len(quizzes_completed)
        if total_quizzes > 0:
            # Weighted average (new score has 30% weight)
            old_rate = progress.quiz_success_rate
            progress.quiz_success_rate = (old_rate * 0.7) + (score * 0.3)
        else:
            progress.quiz_success_rate = score

        # Update completion percentage (based on number of quizzes and success rate)
        # Assume 10 quizzes needed to complete a region
        quizzes_toward_completion = min(total_quizzes, 10)
        progress.completion_percentage = min(
            int((quizzes_toward_completion / 10) * 100 * progress.quiz_success_rate),
            100
        )

        # Mark as completed if 100%
        if progress.completion_percentage >= 100 and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()

        # Track concepts encountered
        concepts_encountered = progress.concepts_encountered.copy() if isinstance(progress.concepts_encountered, list) else []
        for answer in answers:
            if "concepts" in answer:
                for concept in answer["concepts"]:
                    if concept not in concepts_encountered:
                        concepts_encountered.append(concept)
        progress.concepts_encountered = concepts_encountered

        # Update user state
        state = self.db.query(UserJourneyState).filter_by(user_id=user_id).first()
        state.knowledge_points += knowledge_points
        state.total_quizzes_taken += 1

        # Check if region just completed
        if progress.is_completed and progress.completed_at == datetime.utcnow():
            state.total_regions_completed += 1

        state.last_activity = datetime.utcnow()

        self.db.commit()

        # Check for achievements
        achievements_earned = self._check_achievements(user_id)

        # Check for newly unlocked regions
        regions_unlocked = self._check_region_unlocks(user_id)

        logger.info(f"Awarded {knowledge_points} KP to user {user_id}. New total: {state.knowledge_points}")

        return {
            "knowledge_points_earned": knowledge_points,
            "new_completion_percentage": progress.completion_percentage,
            "achievements_earned": achievements_earned,
            "regions_unlocked": regions_unlocked
        }

    def _check_unlock_eligibility(self, user_id: str, region_name: str) -> Tuple[bool, Dict[str, bool]]:
        """
        Check if user meets requirements to unlock a region.

        Returns:
            Tuple of (can_unlock, requirements_dict)
            requirements_dict has keys: knowledge_points, prerequisite_regions, mastered_themes
        """
        region = self.db.query(MiddleEarthRegion).filter_by(name=region_name).first()
        if not region:
            return False, {}

        state = self.db.query(UserJourneyState).filter_by(user_id=user_id).first()
        if not state:
            return False, {}

        # Check knowledge points
        has_knowledge_points = state.knowledge_points >= region.knowledge_points_required

        # Check prerequisites
        prereq_regions = region.prerequisite_regions if isinstance(region.prerequisite_regions, list) else []
        has_prerequisites = all(
            prereq in state.unlocked_regions
            for prereq in prereq_regions
        )

        # Check mastered themes
        required_themes = region.mastered_themes_required if isinstance(region.mastered_themes_required, list) else []
        mastered_communities = state.mastered_communities if isinstance(state.mastered_communities, list) else []
        has_mastered_themes = all(
            theme in mastered_communities
            for theme in required_themes
        )

        requirements = {
            "knowledge_points": has_knowledge_points,
            "prerequisite_regions": has_prerequisites,
            "mastered_themes": has_mastered_themes if required_themes else True
        }

        can_unlock = all(requirements.values())

        return can_unlock, requirements

    def _generate_locked_message(self, region: MiddleEarthRegion, requirements: Dict[str, bool]) -> str:
        """Generate Gandalf's message when a region is locked."""
        messages = []

        if not requirements.get("knowledge_points"):
            messages.append(
                f"You must gain more wisdom before entering {region.display_name}. "
                f"({region.knowledge_points_required} knowledge points required)"
            )

        if not requirements.get("prerequisite_regions"):
            prereq_regions = region.prerequisite_regions if isinstance(region.prerequisite_regions, list) else []
            prereq_names = ", ".join(prereq_regions)
            messages.append(
                f"You must first journey through {prereq_names} before {region.display_name} will open to you."
            )

        if not requirements.get("mastered_themes"):
            required_themes = region.mastered_themes_required if isinstance(region.mastered_themes_required, list) else []
            themes_str = ", ".join(required_themes)
            messages.append(
                f"You must master the following themes: {themes_str}"
            )

        base_message = f"The path to {region.display_name} remains closed, young scholar. "
        return base_message + " ".join(messages)

    def _get_region_quiz_themes(self, region_name: str) -> List[str]:
        """Get available quiz themes for a region."""
        region = self.db.query(MiddleEarthRegion).filter_by(name=region_name).first()
        if not region:
            return []

        return region.available_quiz_themes if isinstance(region.available_quiz_themes, list) else []

    def _fetch_region_lore(self, region_name: str, community_tags: List[str]) -> List[Dict[str, str]]:
        """
        Fetch lore snippets from Neo4j for a region.

        Args:
            region_name: Region name
            community_tags: Neo4j community tags for this region

        Returns:
            List of lore snippet dictionaries
        """
        if not self.neo4j or not community_tags:
            return []

        lore_snippets = []

        try:
            with self.neo4j.session() as session:
                # Query for concepts in this region's communities
                query = """
                MATCH (c:Concept)
                WHERE c.community IN $communities
                RETURN c.name AS concept, c.description AS description
                LIMIT 5
                """

                result = session.run(query, communities=community_tags)

                for record in result:
                    lore_snippets.append({
                        "concept": record["concept"],
                        "description": record["description"]
                    })

        except Exception as e:
            logger.error(f"Error fetching lore from Neo4j: {str(e)}")

        return lore_snippets

    def _check_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Check if user has unlocked any new achievements.

        Returns:
            List of newly unlocked achievement dictionaries
        """
        state = self.db.query(UserJourneyState).filter_by(user_id=user_id).first()
        if not state:
            return []

        current_badges = state.achievement_badges if isinstance(state.achievement_badges, list) else []
        current_badge_codes = [badge.get("code") for badge in current_badges if isinstance(badge, dict)]

        all_achievements = self.db.query(Achievement).all()
        newly_earned = []

        for achievement in all_achievements:
            if achievement.code in current_badge_codes:
                continue

            # Check unlock criteria
            if self._meets_achievement_criteria(user_id, achievement):
                badge = {
                    "code": achievement.code,
                    "name": achievement.name,
                    "description": achievement.description,
                    "category": achievement.category,
                    "rarity": achievement.rarity,
                    "icon_name": achievement.icon_name,
                    "badge_color": achievement.badge_color,
                    "earned_at": datetime.utcnow().isoformat()
                }

                current_badges.append(badge)
                newly_earned.append(badge)

                logger.info(f"User {user_id} earned achievement: {achievement.code}")

        if newly_earned:
            state.achievement_badges = current_badges
            self.db.commit()

        return newly_earned

    def _meets_achievement_criteria(self, user_id: str, achievement: Achievement) -> bool:
        """Check if user meets criteria for an achievement."""
        criteria = achievement.unlock_criteria if isinstance(achievement.unlock_criteria, dict) else {}
        criteria_type = criteria.get("type")

        state = self.db.query(UserJourneyState).filter_by(user_id=user_id).first()
        if not state:
            return False

        if criteria_type == "visit_region":
            region = criteria.get("region")
            return region in state.unlocked_regions

        elif criteria_type == "complete_region":
            region_name = criteria.get("region")
            progress = self.db.query(UserJourneyProgress).filter_by(
                user_id=user_id,
                region_name=region_name
            ).first()
            return progress and progress.is_completed

        elif criteria_type == "knowledge_points":
            required = criteria.get("amount", 0)
            return state.knowledge_points >= required

        elif criteria_type == "regions_completed":
            required = criteria.get("count", 0)
            return state.total_regions_completed >= required

        elif criteria_type == "quizzes_taken":
            required = criteria.get("count", 0)
            return state.total_quizzes_taken >= required

        elif criteria_type == "complete_path":
            path_name = criteria.get("path")
            path = self.db.query(JourneyPath).filter_by(name=path_name).first()
            if not path:
                return False

            ordered_regions = path.ordered_regions if isinstance(path.ordered_regions, list) else []
            for region_name in ordered_regions:
                progress = self.db.query(UserJourneyProgress).filter_by(
                    user_id=user_id,
                    region_name=region_name
                ).first()
                if not progress or not progress.is_completed:
                    return False

            return True

        return False

    def _check_region_unlocks(self, user_id: str) -> List[str]:
        """
        Check if any new regions can be unlocked based on current progress.

        Returns:
            List of newly unlocked region names
        """
        state = self.db.query(UserJourneyState).filter_by(user_id=user_id).first()
        if not state:
            return []

        all_regions = self.db.query(MiddleEarthRegion).all()
        newly_unlocked = []

        for region in all_regions:
            if region.name in state.unlocked_regions:
                continue

            can_unlock, _ = self._check_unlock_eligibility(user_id, region.name)
            if can_unlock:
                unlocked_list = state.unlocked_regions.copy() if isinstance(state.unlocked_regions, list) else []
                unlocked_list.append(region.name)
                state.unlocked_regions = unlocked_list
                newly_unlocked.append(region.name)

                # Create progress record
                progress = UserJourneyProgress(
                    user_id=user_id,
                    region_name=region.name,
                    is_unlocked=True,
                    visit_count=0
                )
                self.db.add(progress)

                logger.info(f"User {user_id} unlocked region: {region.name}")

        if newly_unlocked:
            self.db.commit()

        return newly_unlocked
