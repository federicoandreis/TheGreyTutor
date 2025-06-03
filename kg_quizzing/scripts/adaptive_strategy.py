"""
Adaptive Strategy Engine for Quiz Generation.

This module implements the adaptive strategy engine that determines which questions
to present to the student based on their performance and learning objectives.
"""
import os
import logging
import random
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path

from kg_quizzing.scripts.quiz_utils import (
    execute_query, 
    get_entity_by_name, 
    get_entity_relationships,
    get_entities_in_community,
    get_available_communities
)
from kg_quizzing.scripts.question_generation import (
    generate_question,
    QuestionGeneratorFactory
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class StudentModel:
    """Model representing a student's knowledge and performance."""
    
    id: str
    name: str
    # Dictionary mapping community IDs to mastery levels (0-100)
    community_mastery: Dict[str, int] = field(default_factory=dict)
    # Dictionary mapping entity IDs to familiarity levels (0-100)
    entity_familiarity: Dict[str, int] = field(default_factory=dict)
    # Dictionary mapping question types to performance scores (0-100)
    question_type_performance: Dict[str, int] = field(default_factory=dict)
    # Dictionary mapping difficulty levels to performance scores (0-100)
    difficulty_performance: Dict[str, int] = field(default_factory=dict)
    # List of recently asked questions (to avoid repetition)
    recent_questions: List[Dict[str, Any]] = field(default_factory=list)
    # List of learning objectives IDs that have been mastered
    mastered_objectives: List[str] = field(default_factory=list)
    # Current learning objective ID
    current_objective: Optional[str] = None
    # Overall mastery level (0-100)
    overall_mastery: int = 0
    
    def update_with_question_result(self, question: Dict[str, Any], correct: bool, 
                                   quality_score: Optional[int] = None):
        """
        Update the student model based on a question result.
        
        Args:
            question: The question that was answered
            correct: Whether the answer was correct
            quality_score: Optional quality score for open-ended questions (0-100)
        """
        # Add the question to recent questions
        self.recent_questions.append(question)
        if len(self.recent_questions) > 20:
            self.recent_questions.pop(0)
        
        # Update community mastery
        community_id = str(question.get("community_id"))
        if community_id:
            current_mastery = self.community_mastery.get(community_id, 50)
            if correct:
                # Increase mastery, with diminishing returns as mastery approaches 100
                increase = max(1, 10 * (1 - current_mastery / 100))
                self.community_mastery[community_id] = min(100, current_mastery + increase)
            else:
                # Decrease mastery, with smaller decreases as mastery approaches 0
                decrease = max(1, 5 * (current_mastery / 100))
                self.community_mastery[community_id] = max(0, current_mastery - decrease)
        
        # Update entity familiarity
        for entity_key in ["entity", "entity1", "entity2"]:
            if entity_key in question:
                entity_name = question[entity_key]
                entity_data = get_entity_by_name(entity_name)
                if entity_data:
                    entity_id = entity_data.get("n", {}).element_id
                    if entity_id:
                        current_familiarity = self.entity_familiarity.get(entity_id, 50)
                        # Always increase familiarity when encountering an entity
                        increase = 5 if correct else 2
                        self.entity_familiarity[entity_id] = min(100, current_familiarity + increase)
        
        # Update question type performance
        question_type = question.get("type", "unknown")
        current_performance = self.question_type_performance.get(question_type, 50)
        if correct:
            increase = 5
            self.question_type_performance[question_type] = min(100, current_performance + increase)
        else:
            decrease = 3
            self.question_type_performance[question_type] = max(0, current_performance - decrease)
        
        # Update difficulty performance
        difficulty = question.get("difficulty", 5)
        difficulty_key = str(difficulty)
        current_performance = self.difficulty_performance.get(difficulty_key, 50)
        if correct:
            increase = 5
            self.difficulty_performance[difficulty_key] = min(100, current_performance + increase)
        else:
            decrease = 3
            self.difficulty_performance[difficulty_key] = max(0, current_performance - decrease)
        
        # Update overall mastery
        self._update_overall_mastery()
        
        # Check if current learning objective has been mastered
        if self.current_objective:
            self._check_objective_mastery()
    
    def _update_overall_mastery(self):
        """Update the overall mastery level based on community mastery and question performance."""
        if not self.community_mastery:
            self.overall_mastery = 0
            return
        
        # Calculate overall mastery as a weighted average of community mastery
        total_mastery = sum(self.community_mastery.values())
        self.overall_mastery = total_mastery // len(self.community_mastery)
    
    def _check_objective_mastery(self):
        """Check if the current learning objective has been mastered."""
        if not self.current_objective:
            return
        
        # Get the learning objective
        query = """
        MATCH (lo:LearningObjective {id: $objective_id})
        RETURN lo.community_id AS community_id
        """
        
        results = execute_query(query, {"objective_id": self.current_objective})
        if not results:
            return
        
        community_id = str(results[0]["community_id"])
        
        # Check if the community has been mastered (mastery level >= 80)
        if self.community_mastery.get(community_id, 0) >= 80:
            # Mark the objective as mastered
            if self.current_objective not in self.mastered_objectives:
                self.mastered_objectives.append(self.current_objective)
            
            # Set the current objective to None
            self.current_objective = None
    
    def get_next_learning_objective(self):
        """
        Get the next learning objective for the student.
        
        Returns:
            Learning objective ID if found, None otherwise
        """
        # Get all learning objectives
        query = """
        MATCH (lo:LearningObjective)
        OPTIONAL MATCH (lo)-[:HAS_PREREQUISITE]->(prereq)
        RETURN lo.id AS id, lo.description AS description, 
               lo.community_id AS community_id,
               collect(prereq.id) AS prerequisites
        """
        
        results = execute_query(query)
        
        # Filter out objectives that have already been mastered
        available_objectives = [
            obj for obj in results 
            if obj["id"] not in self.mastered_objectives
        ]
        
        if not available_objectives:
            return None
        
        # Find objectives with all prerequisites mastered
        eligible_objectives = []
        for obj in available_objectives:
            prerequisites = obj["prerequisites"]
            if all(prereq in self.mastered_objectives for prereq in prerequisites if prereq):
                eligible_objectives.append(obj)
        
        if not eligible_objectives:
            # If no eligible objectives, return the one with the most prerequisites mastered
            available_objectives.sort(
                key=lambda obj: sum(1 for prereq in obj["prerequisites"] 
                                  if prereq in self.mastered_objectives)
            )
            return available_objectives[-1]["id"]
        
        # Return the eligible objective with the lowest community mastery
        eligible_objectives.sort(
            key=lambda obj: self.community_mastery.get(str(obj["community_id"]), 0)
        )
        
        return eligible_objectives[0]["id"]
    
    def save(self, file_path: str):
        """
        Save the student model to a file.
        
        Args:
            file_path: Path to save the model to
        """
        with open(file_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, file_path: str) -> 'StudentModel':
        """
        Load a student model from a file.
        
        Args:
            file_path: Path to load the model from
            
        Returns:
            StudentModel instance
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return cls(**data)


class AdaptiveStrategyEngine:
    """Engine for selecting questions based on student performance and learning objectives."""
    
    def __init__(self, student_model: StudentModel):
        """
        Initialize the adaptive strategy engine.
        
        Args:
            student_model: The student model to use
        """
        self.student_model = student_model
        self.question_generators = {
            "factual": QuestionGeneratorFactory.create_generator("factual"),
            "relationship": QuestionGeneratorFactory.create_generator("relationship"),
            "multiple_choice": QuestionGeneratorFactory.create_generator("multiple_choice"),
            "synthesis": QuestionGeneratorFactory.create_generator("synthesis"),
            "application": QuestionGeneratorFactory.create_generator("application")
        }
    
    def select_next_question_params(self, strategy: str = "adaptive") -> Dict[str, Any]:
        """
        Select parameters for the next question to present to the student.
        This method is used by the LLM question generator to create more natural questions.
        
        Args:
            strategy: The strategy to use for selecting the question
                     Options: "adaptive", "depth_first", "breadth_first", "spiral"
            
        Returns:
            Dictionary containing parameters for question generation:
            - question_type: Type of question (factual, relationship, etc.)
            - difficulty: Difficulty level (1-5)
            - entity_name: Name of the entity to ask about (if applicable)
            - community_id: ID of the community to focus on (if applicable)
        """
        # Determine which strategy to use
        if strategy == "adaptive":
            # Use the adaptive strategy based on student performance
            question_type = self._select_question_type_adaptive()
            difficulty = self._select_difficulty_adaptive()
            community_id = self._select_community_adaptive()
        elif strategy == "depth_first":
            # Focus on one community in depth
            question_type = random.choice(["factual", "relationship", "multiple_choice"])
            difficulty = random.randint(1, 5)
            community_id = self._select_community_depth_first()
        elif strategy == "breadth_first":
            # Cover multiple communities at a shallow level
            question_type = random.choice(["factual", "multiple_choice"])
            difficulty = random.randint(1, 3)  # Keep difficulty lower for breadth
            community_id = self._select_community_breadth_first()
        elif strategy == "spiral":
            # Periodically return to previously covered topics
            question_type = self._select_question_type_spiral()
            difficulty = self._select_difficulty_spiral()
            community_id = self._select_community_spiral()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Select an entity from the chosen community
        entity_name = self._select_entity_from_community(community_id)
        
        # Return the parameters for question generation
        return {
            "question_type": question_type,
            "difficulty": difficulty,
            "entity_name": entity_name,
            "community_id": community_id
        }
    
    def _select_question_type_adaptive(self) -> str:
        """
        Select a question type based on the student's performance.
        
        Returns:
            Question type (factual, relationship, multiple_choice, synthesis, application)
        """
        # Get the student's performance for each question type
        performance = self.student_model.question_type_performance
        
        # If we don't have performance data for all question types, prioritize simpler types
        if not all(qt in performance for qt in ["factual", "relationship", "multiple_choice"]):
            return random.choice(["factual", "multiple_choice"])
        
        # Calculate the probability of selecting each question type based on performance
        # Lower performance = higher probability (to focus on areas that need improvement)
        total_weight = 0
        weights = {}
        
        for qt in ["factual", "relationship", "multiple_choice", "synthesis", "application"]:
            # Default performance of 50 if we don't have data
            qt_performance = performance.get(qt, 50)
            
            # Inverse weight: lower performance = higher weight
            # Add 10 to avoid zero weights
            weight = 100 - qt_performance + 10
            
            # Adjust weights based on question complexity
            if qt == "synthesis" and self.student_model.overall_mastery < 50:
                weight *= 0.5  # Reduce probability of synthesis questions for beginners
            elif qt == "application" and self.student_model.overall_mastery < 70:
                weight *= 0.3  # Reduce probability of application questions for non-advanced students
            
            weights[qt] = weight
            total_weight += weight
        
        # Normalize weights to probabilities
        probabilities = {qt: w / total_weight for qt, w in weights.items()}
        
        # Select a question type based on the calculated probabilities
        question_types = list(probabilities.keys())
        question_type_probs = [probabilities[qt] for qt in question_types]
        
        return random.choices(question_types, weights=question_type_probs, k=1)[0]
    
    def _select_difficulty_adaptive(self) -> int:
        """
        Select a difficulty level based on the student's performance.
        
        Returns:
            Difficulty level (1-5)
        """
        # Get the student's overall mastery level
        mastery = self.student_model.overall_mastery
        
        # Calculate the target difficulty based on mastery
        # Higher mastery = higher target difficulty
        if mastery < 30:
            target_difficulty = 1
        elif mastery < 50:
            target_difficulty = 2
        elif mastery < 70:
            target_difficulty = 3
        elif mastery < 85:
            target_difficulty = 4
        else:
            target_difficulty = 5
        
        # Add some randomness: 60% chance of target difficulty, 20% chance of one level higher or lower
        difficulty_options = [max(1, target_difficulty - 1), target_difficulty, min(5, target_difficulty + 1)]
        difficulty_weights = [0.2, 0.6, 0.2]
        
        # If target_difficulty is 1 or 5, adjust the weights
        if target_difficulty == 1:
            difficulty_options = [1, 2]
            difficulty_weights = [0.7, 0.3]
        elif target_difficulty == 5:
            difficulty_options = [4, 5]
            difficulty_weights = [0.3, 0.7]
        
        return random.choices(difficulty_options, weights=difficulty_weights, k=1)[0]
    
    def _select_community_adaptive(self) -> str:
        """
        Select a community based on the student's performance.
        
        Returns:
            Community ID
        """
        # Get available communities
        communities = get_available_communities()
        
        # If no communities are available, return None
        if not communities:
            return None
        
        # Get the student's mastery level for each community
        mastery = self.student_model.community_mastery
        
        # Calculate the probability of selecting each community based on mastery
        # Lower mastery = higher probability (to focus on areas that need improvement)
        total_weight = 0
        weights = {}
        
        for community in communities:
            community_id = community.get("id")
            # Default mastery of 50 if we don't have data
            community_mastery = mastery.get(community_id, 50)
            
            # Inverse weight: lower mastery = higher weight
            # Add 10 to avoid zero weights
            weight = 100 - community_mastery + 10
            weights[community_id] = weight
            total_weight += weight
        
        # Normalize weights to probabilities
        probabilities = {c: w / total_weight for c, w in weights.items()}
        
        # Select a community based on the calculated probabilities
        community_ids = list(probabilities.keys())
        community_probs = [probabilities[c] for c in community_ids]
        
        return random.choices(community_ids, weights=community_probs, k=1)[0]
    
    def _select_question_type_spiral(self) -> str:
        """
        Select a question type using the spiral strategy.
        
        Returns:
            Question type
        """
        # In spiral strategy, we periodically return to previously covered question types
        # Start with simpler types and gradually introduce more complex ones
        
        # Get the student's overall mastery level
        mastery = self.student_model.overall_mastery
        
        if mastery < 30:
            # Beginners: focus on factual and multiple choice
            return random.choice(["factual", "multiple_choice"])
        elif mastery < 60:
            # Intermediate: add relationship questions
            return random.choice(["factual", "relationship", "multiple_choice"])
        else:
            # Advanced: include all question types
            return random.choice(["factual", "relationship", "multiple_choice", "synthesis", "application"])
    
    def _select_difficulty_spiral(self) -> int:
        """
        Select a difficulty level using the spiral strategy.
        
        Returns:
            Difficulty level (1-5)
        """
        # In spiral strategy, we periodically return to easier difficulties
        # to reinforce learning
        
        # Get the student's overall mastery level
        mastery = self.student_model.overall_mastery
        
        if mastery < 30:
            # Beginners: focus on difficulties 1-2
            return random.randint(1, 2)
        elif mastery < 60:
            # Intermediate: difficulties 1-3 with emphasis on 2-3
            difficulties = [1, 2, 2, 3, 3]
            return random.choice(difficulties)
        else:
            # Advanced: all difficulties with emphasis on 3-5
            # but still include some easier questions for reinforcement
            difficulties = [1, 2, 3, 3, 4, 4, 5, 5]
            return random.choice(difficulties)
    
    def _select_community_spiral(self) -> str:
        """
        Select a community using the spiral strategy.
        
        Returns:
            Community ID
        """
        # In spiral strategy, we periodically return to previously covered communities
        
        # Get available communities
        communities = get_available_communities()
        
        # If no communities are available, return None
        if not communities:
            return None
        
        # Get the student's mastery level for each community
        mastery = self.student_model.community_mastery
        
        # Select a mix of mastered and unmastered communities
        # with a bias towards reinforcing mastered ones
        mastered = [c.get("id") for c in communities if mastery.get(c.get("id"), 0) >= 70]
        unmastered = [c.get("id") for c in communities if mastery.get(c.get("id"), 0) < 70]
        
        if not mastered:
            # If no communities are mastered, select from unmastered
            return random.choice(unmastered) if unmastered else communities[0].get("id")
        
        if not unmastered:
            # If all communities are mastered, select from mastered
            return random.choice(mastered)
        
        # 70% chance of selecting a mastered community for reinforcement
        # 30% chance of selecting an unmastered community for new learning
        if random.random() < 0.7:
            return random.choice(mastered)
        else:
            return random.choice(unmastered)
    
    def _select_community_depth_first(self) -> str:
        """
        Select a community using the depth-first strategy.
        
        Returns:
            Community ID
        """
        # In depth-first strategy, we focus on one community until it's mastered
        
        # Get available communities
        communities = get_available_communities()
        
        # If no communities are available, return None
        if not communities:
            return None
        
        # Get the student's mastery level for each community
        mastery = self.student_model.community_mastery
        
        # Find the community with the highest mastery that's not fully mastered
        best_community = None
        best_mastery = -1
        
        for community in communities:
            community_id = community.get("id")
            community_mastery = mastery.get(community_id, 0)
            
            if community_mastery < 90 and community_mastery > best_mastery:
                best_community = community_id
                best_mastery = community_mastery
        
        # If all communities are mastered, select a random one
        if best_community is None:
            return random.choice([c.get("id") for c in communities])
    
    def update_student_model(self, topic: str, difficulty: int, correct: bool, quality_score: float) -> None:
        """
        Update the student model based on the question result.
        
        Args:
            topic: The entity or topic of the question
            difficulty: The difficulty level of the question
            correct: Whether the answer was correct
            quality_score: Quality score for the answer (0-1)
        """
        # Create a simple question dict to pass to the student model
        question = {
            "entity": topic,
            "difficulty": difficulty,
            "type": "unknown"  # We don't need the exact type for updating
        }
        
        # Update the student model
        self.student_model.update_with_question_result(question, correct, int(quality_score * 100))
    
    def _select_community_breadth_first(self) -> str:
        """
        Select a community using the breadth-first strategy.
        
        Returns:
            Community ID
        """
        # In breadth-first strategy, we cover all communities at a shallow level
        
        # Get available communities
        communities = get_available_communities()
        
        # If no communities are available, return None
        if not communities:
            return None
        
        # Get the student's mastery level for each community
        mastery = self.student_model.community_mastery
        
        # Find the community with the lowest mastery
        worst_community = None
        worst_mastery = 101  # Higher than possible mastery
        
        for community in communities:
            community_id = community.get("id")
            community_mastery = mastery.get(community_id, 0)
            
            if community_mastery < worst_mastery:
                worst_community = community_id
                worst_mastery = community_mastery
        
        return worst_community
    
    def _select_entity_from_community(self, community_id: str) -> str:
        """
        Select an entity from a community.
        
        Args:
            community_id: ID of the community
            
        Returns:
            Entity name or None if no entities are available
        """
        if not community_id:
            return None
        
        # Get entities in the community
        entities = get_entities_in_community(community_id)
        
        # If no entities are available, return None
        if not entities:
            return None
        
        # Get the student's familiarity level for each entity
        familiarity = self.student_model.entity_familiarity
        
        # Calculate the probability of selecting each entity based on familiarity
        # Lower familiarity = higher probability (to focus on unfamiliar entities)
        total_weight = 0
        weights = {}
        
        for entity in entities:
            entity_id = entity.get("id")
            entity_name = entity.get("name")
            
            # Skip entities without names
            if not entity_name:
                continue
                
            # Convert entity_id to string if it's a list
            if isinstance(entity_id, list):
                entity_id = str(entity_id[0]) if entity_id else None
            elif entity_id is not None:
                entity_id = str(entity_id)
                
            # Skip entities without IDs
            if not entity_id:
                continue
                
            # Convert entity_name to string if it's a list
            if isinstance(entity_name, list):
                entity_name = str(entity_name[0]) if entity_name else None
                # Skip if we couldn't get a valid name
                if not entity_name:
                    continue
                
            # Default familiarity of 50 if we don't have data
            entity_familiarity = familiarity.get(entity_id, 50)
            
            # Inverse weight: lower familiarity = higher weight
            # Add 10 to avoid zero weights
            weight = 100 - entity_familiarity + 10
            weights[entity_name] = weight
            total_weight += weight
        
        # If no valid entities with names, return None
        if not weights:
            return None
            
        # Normalize weights to probabilities
        probabilities = {e: w / total_weight for e, w in weights.items()}
        
        # Select an entity based on the calculated probabilities
        entity_names = list(probabilities.keys())
        entity_probs = [probabilities[e] for e in entity_names]
        
        return random.choices(entity_names, weights=entity_probs, k=1)[0]
    
    def select_next_question(self, strategy: str = "adaptive") -> Dict[str, Any]:
        """
        Select the next question to present to the student.
        
        Args:
            strategy: The strategy to use for selecting the question
                     Options: "adaptive", "depth_first", "breadth_first", "spiral"
            
        Returns:
            Dictionary containing the selected question
        """
        if strategy == "adaptive":
            return self._select_adaptive_question()
        elif strategy == "depth_first":
            return self._select_depth_first_question()
        elif strategy == "breadth_first":
            return self._select_breadth_first_question()
        elif strategy == "spiral":
            return self._select_spiral_question()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _select_adaptive_question(self) -> Dict[str, Any]:
        """
        Select a question using the adaptive strategy.
        
        This strategy selects questions based on the student's performance and learning objectives.
        
        Returns:
            Dictionary containing the selected question
        """
        # Check if we need to set a new learning objective
        if not self.student_model.current_objective:
            next_objective = self.student_model.get_next_learning_objective()
            if next_objective:
                self.student_model.current_objective = next_objective
        
        # Get the current learning objective
        current_objective = self.student_model.current_objective
        
        if current_objective:
            # Get the learning objective details
            query = """
            MATCH (lo:LearningObjective {id: $objective_id})
            RETURN lo.community_id AS community_id, lo.difficulty AS difficulty
            """
            
            results = execute_query(query, {"objective_id": current_objective})
            if results:
                community_id = results[0]["community_id"]
                objective_difficulty = results[0].get("difficulty", 5)
                
                # Get the student's mastery level for this community
                community_mastery = self.student_model.community_mastery.get(str(community_id), 50)
                
                # Select question type based on mastery level
                if community_mastery < 30:
                    # For low mastery, focus on factual and multiple-choice questions
                    question_type = random.choice(["factual", "multiple_choice"])
                    # Set difficulty slightly below the objective difficulty
                    difficulty = max(1, objective_difficulty - 2)
                elif community_mastery < 70:
                    # For medium mastery, include relationship questions
                    question_type = random.choice(["factual", "multiple_choice", "relationship"])
                    # Set difficulty at the objective difficulty
                    difficulty = objective_difficulty
                else:
                    # For high mastery, include synthesis and application questions
                    question_type = random.choice(["relationship", "synthesis", "application"])
                    # Set difficulty slightly above the objective difficulty
                    difficulty = min(10, objective_difficulty + 2)
                
                # Generate the question
                return generate_question(
                    question_type=question_type,
                    difficulty=difficulty,
                    community_id=community_id
                )
        
        # If no learning objective is set, select a random question
        return self._select_random_question()
    
    def _select_depth_first_question(self) -> Dict[str, Any]:
        """
        Select a question using the depth-first strategy.
        
        This strategy focuses on exploring a single community in depth before moving to others.
        
        Returns:
            Dictionary containing the selected question
        """
        # Get the community with the lowest mastery level
        community_mastery = self.student_model.community_mastery
        
        if not community_mastery:
            # If no communities have been explored yet, select a random community
            communities = get_available_communities()
            if not communities:
                return self._select_random_question()
            
            community = random.choice(communities)
            community_id = community["id"]
        else:
            # Select the community with the lowest mastery level
            community_id = min(community_mastery.items(), key=lambda x: x[1])[0]
            community_id = int(community_id)
        
        # Get the student's mastery level for this community
        mastery = community_mastery.get(str(community_id), 50)
        
        # Select question type and difficulty based on mastery level
        if mastery < 30:
            question_type = random.choice(["factual", "multiple_choice"])
            difficulty = random.randint(1, 3)
        elif mastery < 70:
            question_type = random.choice(["factual", "multiple_choice", "relationship"])
            difficulty = random.randint(3, 6)
        else:
            question_type = random.choice(["relationship", "synthesis", "application"])
            difficulty = random.randint(6, 10)
        
        # Generate the question
        return generate_question(
            question_type=question_type,
            difficulty=difficulty,
            community_id=community_id
        )
    
    def _select_breadth_first_question(self) -> Dict[str, Any]:
        """
        Select a question using the breadth-first strategy.
        
        This strategy focuses on exploring multiple communities at a shallow level.
        
        Returns:
            Dictionary containing the selected question
        """
        # Get all communities
        communities = get_available_communities()
        if not communities:
            return self._select_random_question()
        
        # Select a random community, with preference for those with low mastery
        community_mastery = self.student_model.community_mastery
        
        if not community_mastery or random.random() < 0.3:
            # 30% chance to select a completely random community
            community = random.choice(communities)
            community_id = community["id"]
        else:
            # Weight communities by inverse mastery level
            weights = []
            for community in communities:
                community_id = str(community["id"])
                mastery = community_mastery.get(community_id, 50)
                # Higher weight for lower mastery
                weight = 100 - mastery
                weights.append(weight)
            
            # Normalize weights
            total_weight = sum(weights)
            if total_weight == 0:
                community = random.choice(communities)
            else:
                normalized_weights = [w / total_weight for w in weights]
                community_index = random.choices(
                    range(len(communities)), weights=normalized_weights, k=1
                )[0]
                community = communities[community_index]
            
            community_id = community["id"]
        
        # For breadth-first, focus on simpler question types
        question_type = random.choice(["factual", "multiple_choice", "relationship"])
        difficulty = random.randint(1, 5)
        
        # Generate the question
        return generate_question(
            question_type=question_type,
            difficulty=difficulty,
            community_id=community_id
        )
    
    def _select_spiral_question(self) -> Dict[str, Any]:
        """
        Select a question using the spiral strategy.
        
        This strategy periodically returns to previously covered topics for reinforcement.
        
        Returns:
            Dictionary containing the selected question
        """
        # Get the student's recent questions
        recent_questions = self.student_model.recent_questions
        
        if not recent_questions:
            return self._select_random_question()
        
        # 70% chance to select a question from a community that was recently covered
        if random.random() < 0.7:
            # Get communities from recent questions
            recent_communities = []
            for question in recent_questions:
                community_id = question.get("community_id")
                if community_id and community_id not in recent_communities:
                    recent_communities.append(community_id)
            
            if not recent_communities:
                return self._select_random_question()
            
            # Select a random community from recent ones
            community_id = random.choice(recent_communities)
            
            # For spiral strategy, vary question types and difficulty
            question_type = random.choice([
                "factual", "multiple_choice", "relationship", "synthesis", "application"
            ])
            
            # Vary difficulty based on the student's performance with this question type
            type_performance = self.student_model.question_type_performance.get(question_type, 50)
            
            if type_performance < 30:
                difficulty = random.randint(1, 3)
            elif type_performance < 70:
                difficulty = random.randint(3, 7)
            else:
                difficulty = random.randint(7, 10)
            
            # Generate the question
            return generate_question(
                question_type=question_type,
                difficulty=difficulty,
                community_id=community_id
            )
        else:
            # 30% chance to select a completely new question
            return self._select_random_question()
    
    def _select_random_question(self) -> Dict[str, Any]:
        """
        Select a completely random question.
        
        Returns:
            Dictionary containing the selected question
        """
        # Select a random question type
        question_type = random.choice([
            "factual", "multiple_choice", "relationship", "synthesis", "application"
        ])
        
        # Select a random difficulty
        difficulty = random.randint(1, 10)
        
        # Generate the question
        return generate_question(
            question_type=question_type,
            difficulty=difficulty
        )
    
    def evaluate_answer(self, question: Dict[str, Any], answer: str) -> Tuple[bool, Optional[int]]:
        """
        Evaluate a student's answer to a question.
        
        Args:
            question: The question that was answered
            answer: The student's answer
            
        Returns:
            Tuple of (correct, quality_score)
            correct: Whether the answer was correct
            quality_score: Optional quality score for open-ended questions (0-100)
        """
        question_type = question.get("type")
        
        if question_type in ["factual", "relationship"]:
            # For factual and relationship questions, check if the answer matches
            if answer is None:
                logger.warning(f"Missing student answer for {question_type} question")
                return False, None
                
            correct_answer = str(question.get("answer", "")).lower()
            student_answer = str(answer).lower()
            
            # Simple string matching (in a real system, this would be more sophisticated)
            correct = student_answer in correct_answer or correct_answer in student_answer
            
            return correct, None
        
        elif question_type == "multiple_choice":
            # For multiple-choice questions, check if the answer matches the correct option
            correct_answer = question.get("correct_answer")
            
            # Handle None values for answer or correct_answer
            if answer is None or correct_answer is None:
                logger.warning(f"Missing answer or correct_answer: answer={answer}, correct_answer={correct_answer}")
                return False, None
            
            # Check if the answer matches the correct option
            correct = str(answer).lower() == str(correct_answer).lower()
            
            return correct, None
        
        elif question_type in ["synthesis", "application"]:
            # For synthesis and application questions, we need LLM evaluation
            # This is a placeholder - in a real system, this would use an LLM
            
            # Handle None values for answer
            if answer is None:
                logger.warning(f"Missing answer for {question_type} question")
                return False, 0
            
            # For now, we'll assume the answer is correct if it's longer than 50 characters
            correct = len(str(answer)) > 50
            
            # Quality score is a function of answer length (placeholder)
            quality_score = min(100, len(str(answer)) // 5)
            
            return correct, quality_score
        
        else:
            # Unknown question type
            return False, None


def create_student_model(student_id: str, student_name: str) -> StudentModel:
    """
    Create a new student model.
    
    Args:
        student_id: Unique identifier for the student
        student_name: Name of the student
        
    Returns:
        StudentModel instance
    """
    return StudentModel(id=student_id, name=student_name)


def load_or_create_student_model(student_id: str, student_name: str, 
                               models_dir: str = "student_models") -> StudentModel:
    """
    Load an existing student model or create a new one if it doesn't exist.
    
    Args:
        student_id: Unique identifier for the student
        student_name: Name of the student
        models_dir: Directory to store student models
        
    Returns:
        StudentModel instance
    """
    # Create the models directory if it doesn't exist
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, f"{student_id}.json")
    
    if os.path.exists(model_path):
        try:
            return StudentModel.load(model_path)
        except Exception as e:
            logger.error(f"Failed to load student model: {e}")
    
    # Create a new model
    model = create_student_model(student_id, student_name)
    
    # Save the model
    model.save(model_path)
    
    return model


def main():
    """Main function for testing the adaptive strategy engine."""
    parser = argparse.ArgumentParser(description="Test the adaptive strategy engine")
    parser.add_argument("--student", type=str, default="test_student",
                       help="Student ID")
    parser.add_argument("--name", type=str, default="Test Student",
                       help="Student name")
    parser.add_argument("--strategy", type=str, 
                       choices=["adaptive", "depth_first", "breadth_first", "spiral"],
                       default="adaptive",
                       help="Question selection strategy")
    args = parser.parse_args()
    
    # Load or create the student model
    student_model = load_or_create_student_model(args.student, args.name)
    
    # Create the adaptive strategy engine
    engine = AdaptiveStrategyEngine(student_model)
    
    # Select a question
    question = engine.select_next_question(args.strategy)
    
    print(f"\nSelected Question:")
    print(f"Text: {question['text']}")
    print(f"Type: {question['type']}")
    print(f"Difficulty: {question['difficulty']}")
    
    if "options" in question:
        print(f"Options: {question['options']}")
        print(f"Correct Answer: {question['correct_answer']}")
    elif "answer" in question:
        print(f"Answer: {question['answer']}")
    else:
        print("This question requires LLM evaluation.")
    
    print(f"Community ID: {question.get('community_id')}")
    
    # Simulate an answer
    if "options" in question:
        # For multiple-choice questions, select the correct answer 50% of the time
        if random.random() < 0.5:
            answer = question["correct_answer"]
        else:
            # Select a random incorrect option
            incorrect_options = [o for o in question["options"] if o != question["correct_answer"]]
            answer = random.choice(incorrect_options) if incorrect_options else "Unknown"
    elif "answer" in question:
        # For factual and relationship questions, use the correct answer 50% of the time
        if random.random() < 0.5:
            answer = question["answer"]
        else:
            answer = "Incorrect answer"
    else:
        # For synthesis and application questions, generate a random answer
        answer = "This is a simulated answer for a complex question. " * random.randint(1, 5)
    
    print(f"\nSimulated Answer: {answer}")
    
    # Evaluate the answer
    correct, quality_score = engine.evaluate_answer(question, answer)
    
    print(f"Correct: {correct}")
    if quality_score is not None:
        print(f"Quality Score: {quality_score}")
    
    # Update the student model
    student_model.update_with_question_result(question, correct, quality_score)
    
    # Save the updated model
    student_model.save(os.path.join("student_models", f"{args.student}.json"))
    
    print(f"\nStudent Model:")
    print(f"Overall Mastery: {student_model.overall_mastery}%")
    print(f"Community Mastery: {student_model.community_mastery}")
    print(f"Question Type Performance: {student_model.question_type_performance}")
    print(f"Current Learning Objective: {student_model.current_objective}")
    print(f"Mastered Learning Objectives: {student_model.mastered_objectives}")

if __name__ == "__main__":
    main()
