"""
Quiz Session module for Adaptive Quizzing.

Handles the student session state, question and answer flow, feedback, and statistics.
"""
import os
import time
import logging
import json
import random
import sys
from typing import Dict, List, Any, Optional, Tuple

# Add the current directory to the path to enable relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use relative imports
from quiz_utils import execute_query, get_entity_by_name
from adaptive_strategy import (
    StudentModel,
    AdaptiveStrategyEngine,
    load_or_create_student_model
)
from llm_question_generation import LLMQuestionGenerator
from llm_assessment import LLMAssessmentService
from conversation_history import QuizConversation, ConversationHistoryManager

logger = logging.getLogger(__name__)

class QuizSession:
    """Class representing a quiz session for a student."""
    def __init__(self, student_id: str, student_name: str, 
                 strategy: str = "adaptive", models_dir: str = "student_models",
                 conversation_dir: str = "conversation_history", use_llm: bool = True,
                 tier: str = None, fussiness: int = 3):
        self.student_id = student_id
        self.student_name = student_name
        self.strategy = strategy
        self.models_dir = models_dir
        self.conversation_dir = conversation_dir
        self.use_llm = use_llm  # Allow configuring LLM usage
        self.tier = tier  # Store the tier preference
        self.fussiness = fussiness
        self.student_model = load_or_create_student_model(
            student_id, student_name, models_dir
        )
        self.engine = AdaptiveStrategyEngine(self.student_model)
        self.llm_question_generator = LLMQuestionGenerator()
        self.llm_assessment_service = LLMAssessmentService(fussiness=fussiness)
        self.session_stats = {
            "questions_asked": 0,
            "correct": 0,
            "incorrect": 0,
            "start_time": time.time(),
            "end_time": None,
            "question_history": []
        }
        self.current_question = None
        self.conversation_manager = ConversationHistoryManager(conversation_dir)
        self.conversation = QuizConversation(
            student_id=student_id,
            quiz_id=f"{strategy}_quiz_{time.strftime('%Y%m%d_%H%M%S')}",
            metadata={
                "student_name": student_name,
                "strategy": strategy,
                "session_id": f"session_{time.strftime('%Y%m%d_%H%M%S')}"
            }
        )
    def next_question(self) -> Dict[str, Any]:
        """Generate the next question based on the selected strategy."""
        # Get the next question parameters based on the strategy
        params = self.engine.select_next_question_params(self.strategy)
        topic = params["entity_name"]
        difficulty = params["difficulty"]
        
        # Override difficulty based on tier if specified
        if self.tier:
            if self.tier == "basic":
                difficulty = random.randint(1, 3)  # Basic tier: difficulty 1-3
            elif self.tier == "intermediate":
                difficulty = random.randint(4, 7)  # Intermediate tier: difficulty 4-7
            elif self.tier == "advanced":
                difficulty = random.randint(8, 10)  # Advanced tier: difficulty 8-10
        
        # Always initialize the LLM question generator if not already done
        if not self.llm_question_generator:
            from kg_quizzing.scripts.llm_question_generation import LLMQuestionGenerator
            self.llm_question_generator = LLMQuestionGenerator()
            self.use_llm = True
            
        # Get entity data for the topic
        entity_data = get_entity_by_name(topic)
        
        if not entity_data:
            # If entity not found, use a generic Tolkien topic
            logger.warning(f"Entity {topic} not found, using generic Tolkien topic")
            generic_topics = ["The One Ring", "Frodo Baggins", "Gandalf", "Mordor", "The Shire", 
                             "Rivendell", "Aragorn", "Gollum", "Sauron", "Legolas", "Gimli"]
            topic = random.choice(generic_topics)
            
            # Try to get entity data for the generic topic
            entity_data = get_entity_by_name(topic)
        
        # Select a question type - weighted to favor more engaging types
        question_types = [
            "factual", "factual",  # More common
            "relationship", "relationship",  # More common
            "multiple_choice", "multiple_choice",  # More common
            "synthesis", "application"  # Less common but more engaging
        ]
        question_type = random.choice(question_types)
        
        # Generate the question using LLM
        try:
            question = self.llm_question_generator.generate_question(
                question_type=question_type,
                difficulty=difficulty,
                entity_data=entity_data
            )
        except Exception as e:
            logger.error(f"LLM question generation failed: {e}")
            # Use a fallback question about a well-known Tolkien topic
            question = None
        
        # Create a fallback question if we couldn't generate one
        if not question:
            logger.warning("Failed to generate a question, using fallback question")
            
            # Select a random fallback question from a curated list of engaging Tolkien-themed questions
            fallback_questions = [
                # Basic tier questions (concise, focused on essential knowledge)
                {
                    "text": "What was the One Ring forged to do?",
                    "type": "factual",
                    "difficulty": 1,
                    "tier": "basic",
                    "entity": "One Ring",
                    "requires_llm_evaluation": True
                },
                {
                    "text": "Who were the nine members of the Fellowship of the Ring?",
                    "type": "factual",
                    "difficulty": 2,
                    "tier": "basic",
                    "entity": "Fellowship of the Ring",
                    "requires_llm_evaluation": True
                },
                {
                    "text": "What race do Frodo and Bilbo belong to?",
                    "type": "factual",
                    "difficulty": 1,
                    "tier": "basic",
                    "entity": "Hobbits",
                    "requires_llm_evaluation": True
                },
                # Intermediate tier questions (moderate narrative elements)
                {
                    "text": "In the depths of Mordor, the One Ring was forged by Sauron to control the other Rings of Power. What unique abilities did the One Ring bestow upon its bearer?",
                    "type": "factual",
                    "difficulty": 5,
                    "tier": "intermediate",
                    "entity": "One Ring",
                    "requires_llm_evaluation": True
                },
                {
                    "text": "The Fellowship of the Ring was formed in the council of Elrond. Which members represented the different free peoples of Middle-earth, and what significance did this diversity hold in their quest?",
                    "type": "synthesis",
                    "difficulty": 6,
                    "tier": "intermediate",
                    "entity": "Fellowship of the Ring",
                    "requires_llm_evaluation": True
                },
                {
                    "text": "Gandalf the Grey fell in Moria, only to return as Gandalf the White. How did this transformation change his role in the War of the Ring?",
                    "type": "application",
                    "difficulty": 6,
                    "tier": "intermediate",
                    "entity": "Gandalf",
                    "requires_llm_evaluation": True
                },
                # Advanced tier questions (rich narrative, complex themes)
                {
                    "text": "The Silmarils were jewels of immense beauty and power in the First Age. What was their origin, and why did they cause such conflict among the Elves? Consider how their creation and subsequent fate mirror Tolkien's themes of creation, possession, and loss throughout his legendarium.",
                    "type": "relationship",
                    "difficulty": 9,
                    "tier": "advanced",
                    "entity": "Silmarils",
                    "requires_llm_evaluation": True
                },
                {
                    "text": "The Shire was home to the Hobbits, a people who valued comfort and simplicity. As we sit by the fire in Bag End, contemplating the great tales of Middle-earth, consider how this cultural background influenced Frodo and Sam's approach to their quest, and how their journey transformed not only themselves but the very nature of the Shire upon their return. What does this tell us about Tolkien's view on the relationship between comfort, adventure, and growth?",
                    "type": "synthesis",
                    "difficulty": 10,
                    "tier": "advanced",
                    "entity": "The Shire",
                    "requires_llm_evaluation": True
                }
            ]
            
            question = random.choice(fallback_questions)
        
        # Store the current question
        self.current_question = question
        
        # Add the question to the conversation history
        self.conversation.add_question(question)
        
        # Update session stats
        self.session_stats["questions_asked"] += 1
        self.session_stats["question_history"].append({
            "question": question,
            "answer": None,
            "correct": None,
            "quality_score": None,
            "feedback": None
        })
        
        return question
        
    def process_answer(self, answer: str) -> Tuple[bool, float, Dict[str, Any]]:
        """Process the student's answer and provide feedback."""
        if not self.current_question:
            logger.error("No current question to process answer for")
            return False, 0.0, {"message": "No question was asked.", "explanation": "", "next_steps": []}
        
        # Get the correct answer from the current question
        correct_answer = self.current_question.get("correct_answer") or self.current_question.get("answer", "")
        options = self.current_question.get("options", [])
        question_type = self.current_question.get("type", "")

        # For multiple choice questions, use strict option match for correctness
        if options and len(options) == 4:
            # Accept both option text and option index (1-based)
            answer_clean = answer.strip()
            correct = False
            # If user entered a number, map to option
            if answer_clean.isdigit():
                idx = int(answer_clean) - 1
                if 0 <= idx < len(options):
                    selected = options[idx].strip().lower()
                    correct = selected == correct_answer.strip().lower()
            else:
                correct = answer_clean.lower() == correct_answer.strip().lower()
            quality_score = 1.0 if correct else 0.0
            # Always use LLM for feedback only
            if self.use_llm and self.llm_assessment_service:
                _, _, feedback = self.llm_assessment_service.assess_answer(
                    self.current_question,
                    answer
                )
            else:
                feedback = self._generate_feedback(correct, quality_score, answer, correct_answer)
        else:
            # Fallback: open-ended or non-MC question
            if self.use_llm and self.llm_assessment_service:
                correct, quality_score, feedback = self.llm_assessment_service.assess_answer(
                    self.current_question,
                    answer
                )
            else:
                answer_lower = answer.lower().strip()
                correct_lower = correct_answer.lower().strip()
                correct = answer_lower == correct_lower or correct_lower in answer_lower
                quality_score = 1.0 if correct else 0.0
                feedback = self._generate_feedback(correct, quality_score, answer, correct_answer)

        # Update the student model with the result
        self.engine.update_student_model(
            topic=self.current_question["entity"],
            difficulty=self.current_question["difficulty"],
            correct=correct,
            quality_score=quality_score
        )

        # Update session stats
        if correct:
            self.session_stats["correct"] += 1
        else:
            self.session_stats["incorrect"] += 1

        # Update the last question in the history
        self.session_stats["question_history"][-1].update({
            "answer": answer,
            "correct": correct,
            "quality_score": quality_score,
            "feedback": feedback
        })

        # Add the answer and feedback to the conversation history
        self.conversation.add_answer(answer, correct, feedback)

        return correct, quality_score, feedback
    
    def _generate_feedback(self, correct: bool, quality_score: float, 
                          student_answer: str, correct_answer: str) -> Dict[str, Any]:
        """Generate feedback for the student's answer."""
        # Initialize feedback dictionary
        feedback = {
            "message": "",
            "explanation": "",
            "next_steps": []
        }
        
        # Generate feedback message based on correctness and quality
        if correct:
            if quality_score >= 0.9:
                feedback["message"] = "Excellent! Your wisdom rivals that of the White Council itself!"
            elif quality_score >= 0.7:
                feedback["message"] = "Well done! Your knowledge of Middle-earth grows like the mallorn trees of Lothlórien."
            else:
                feedback["message"] = "Indeed! Your wisdom serves you well on this matter."
        else:
            if quality_score >= 0.5:
                feedback["message"] = "Your answer holds truth, though like a young sapling, it has room yet to grow into a mighty mallorn."
            elif quality_score >= 0.3:
                feedback["message"] = "Like Bilbo at the beginning of his journey, you have taken the first steps toward understanding, but the road goes ever on."
            else:
                feedback["message"] = "Even the wisest cannot see all ends. Let us explore this matter further."
        
        # Add explanation
        if not correct:
            feedback["explanation"] = f"The lore of Middle-earth tells us that {correct_answer}."
        
        # Add next steps
        if not correct:
            feedback["next_steps"] = [
                "Consult the ancient texts for more knowledge on this subject.",
                "Reflect on the connections between different realms of Middle-earth's lore.",
                "Consider how this knowledge fits into the broader tapestry of Tolkien's world."
            ]
        else:
            feedback["next_steps"] = [
                "Continue your journey through the deeper mysteries of Middle-earth.",
                "Share your wisdom with others who seek to understand these ancient tales."
            ]
        
        return feedback
    
    def start_session(self) -> None:
        """Start a new quiz session."""
        # Reset session stats
        self.session_stats = {
            "questions_asked": 0,
            "correct": 0,
            "incorrect": 0,
            "start_time": time.time(),
            "end_time": None,
            "question_history": []
        }
        
        # Reset current question
        self.current_question = None
        
        # Create a new conversation
        self.conversation = QuizConversation(
            student_id=self.student_id,
            quiz_id=f"{self.strategy}_quiz_{time.strftime('%Y%m%d_%H%M%S')}",
            metadata={
                "student_name": self.student_name,
                "strategy": self.strategy,
                "session_id": f"session_{time.strftime('%Y%m%d_%H%M%S')}"
            }
        )
        
        # Log session start
        logger.info(f"Started new quiz session for student {self.student_name} ({self.student_id}) using {self.strategy} strategy")
    
    def end_session(self) -> Dict[str, Any]:
        """End the quiz session and return session statistics."""
        # Set end time
        self.session_stats["end_time"] = time.time()
        
        # Calculate duration
        duration = self.session_stats["end_time"] - self.session_stats["start_time"]
        
        # Calculate accuracy
        total_questions = self.session_stats["questions_asked"]
        correct_answers = self.session_stats["correct"]
        accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Get mastery level
        mastery_after = self.student_model.overall_mastery
        
        # Since we don't have initial_mastery, we'll use a default value or calculate from stats
        mastery_change = 0
        if total_questions > 0:
            # Estimate mastery change based on accuracy
            mastery_change = (accuracy / 100) * 10  # Rough estimate: 10% max change per session
        
        # Format duration
        duration_formatted = self._format_duration(duration)
        
        # Create summary
        summary = {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy": accuracy,
            "duration": duration,
            "duration_formatted": duration_formatted,
            "mastery_after": mastery_after,
            "mastery_change": mastery_change
        }
        
        # Add summary to session stats
        self.session_stats["summary"] = summary
        
        # Save the student model
        self._save_student_model()
        
        # Save the session stats
        self._save_session_stats()
        
        # Save the conversation history
        self.conversation_manager.save_conversation(self.conversation)
        
        # Log session end
        logger.info(f"Ended quiz session for student {self.student_name} ({self.student_id})")
        logger.info(f"Session summary: {total_questions} questions, {correct_answers} correct, {accuracy:.1f}% accuracy")
        
        return {
            "stats": self.session_stats,
            "summary": summary
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format a duration in seconds as a human-readable string."""
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
        elif minutes > 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''}, {seconds} second{'s' if seconds != 1 else ''}"
        else:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
    
    def _save_student_model(self) -> None:
        """Save the student model to a file."""
        os.makedirs(self.models_dir, exist_ok=True)
        self.student_model.save(os.path.join(self.models_dir, f"{self.student_id}.json"))
    
    def _save_session_stats(self) -> None:
        """Save the session statistics to a file."""
        # Create the directory if it doesn't exist
        stats_dir = os.path.join(self.models_dir, "session_stats")
        os.makedirs(stats_dir, exist_ok=True)
        
        # Generate a filename with timestamp
        filename = f"{self.student_id}_{time.strftime('%Y%m%d_%H%M%S')}.json"
        
        # Save the stats to a JSON file
        with open(os.path.join(stats_dir, filename), 'w') as f:
            json.dump(self.session_stats, f, indent=2)
