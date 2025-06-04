"""
Quiz Orchestrator for Adaptive Quizzing.

This module orchestrates the adaptive quizzing system, managing quiz sessions
and database setup.
"""
import os
import logging
import time
from typing import Dict, Any

# Import conversation history module
import sys

# Add the parent directory to sys.path to enable relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import QuizSession
from kg_quizzing.scripts.quiz_session import QuizSession

from kg_quizzing.scripts.quiz_utils import (
    check_educational_metadata_exists,
    get_available_communities
)

from kg_quizzing.scripts.schema_extension import (
    create_educational_schema,
    create_question_templates,
    create_learning_objectives,
    create_difficulty_progression_paths,
    create_community_bridges
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class QuizOrchestrator:
    """Main class for orchestrating the adaptive quizzing system."""

    def __init__(self, student_id: str = None, student_name: str = None, 
                 strategy: str = "adaptive", conversation_dir: str = "conversation_history", 
                 use_llm: bool = True, tier: str = None, fussiness: int = 3, theme: str = None):
        """Initialize the quiz orchestrator.
        
        Args:
            student_id: The ID of the student
            student_name: The name of the student
            strategy: The question selection strategy to use
            conversation_dir: Directory for conversation history
            use_llm: Whether to use LLM for question generation
            tier: The question tier to use (basic, intermediate, advanced)
            fussiness: Gandalf's fussiness (1=very lenient, 10=very strict)
            theme: The theme of the quiz
        """
        self.current_session = None
        self.conversation_dir = conversation_dir
        self.use_llm = use_llm
        self.student_id = student_id
        self.student_name = student_name
        self.strategy = strategy
        self.tier = tier
        self.fussiness = fussiness
        self.theme = theme

        # Create the conversation directory if it doesn't exist
        os.makedirs(conversation_dir, exist_ok=True)

    def setup_database(self, force: bool = False):
        """
        Set up the database with educational metadata.

        Args:
            force: Whether to force setup even if metadata already exists
        """
        if force or not check_educational_metadata_exists():
            logger.info("Setting up educational metadata...")
            create_educational_schema()
            create_question_templates()
            create_learning_objectives()
            create_difficulty_progression_paths()
            create_community_bridges()
            logger.info("Educational metadata setup complete.")
        else:
            logger.info("Educational metadata already exists.")

    def start_session(self, student_id: str = None, student_name: str = None, strategy: str = None, theme: str = None):
        """
        Start a new quiz session.

        Args:
            student_id: Unique identifier for the student (overrides the one set in __init__)
            student_name: Name of the student (overrides the one set in __init__)
            strategy: Question selection strategy (overrides the one set in __init__)
        """
        # Use parameters from __init__ if not provided
        student_id = student_id or self.student_id
        student_name = student_name or self.student_name
        strategy = strategy or self.strategy
        theme = theme or self.theme
        
        if not student_id:
            raise ValueError("Student ID is required to start a session")
            
        self.current_session = QuizSession(
            student_id,
            student_name,
            strategy,
            conversation_dir=self.conversation_dir,
            use_llm=self.use_llm,
            tier=self.tier,
            fussiness=self.fussiness,
            theme=theme
        )

    def run_interactive_session(self):
        """Run an interactive quiz session with Tolkien-themed language and clear formatting."""
        if not self.current_session:
            logger.error("No active session. Please start a session first.")
            return

        try:
            # Start the session
            self.current_session.start_session()

            # Print welcome message with Gandalf-themed language and clear formatting
            print("\n" + "="*80)
            print("THE GREY TUTOR: A JOURNEY THROUGH THE LORE OF MIDDLE-EARTH")
            print("="*80)
            print(f"\nAh, {self.current_session.student_name}! Welcome to our scholarly discourse on the lore of Middle-earth.")
            print("I am Gandalf the Grey, and I shall be your guide through the ancient wisdom.")

            # Explain the strategy in Tolkien-themed language
            if self.current_session.strategy == "adaptive":
                print("Like the paths through Mirkwood, our journey shall adapt to your knowledge and wisdom. I shall pose questions that challenge your understanding, yet remain within your grasp.")
            elif self.current_session.strategy == "depth_first":
                print("We shall delve deep like the Dwarves of Moria, exploring one realm of knowledge thoroughly before moving to another.")
            elif self.current_session.strategy == "breadth_first":
                print("Our journey shall be wide-ranging, like an Elf's view from the tallest mallorn tree in Lothlórien, touching upon many realms of Middle-earth's lore.")
            elif self.current_session.strategy == "spiral":
                print("Like the winding stair of Orthanc, we shall revisit topics with increasing depth and complexity as your understanding grows.")

            print("\nShould you wish to end our discourse, simply say 'farewell' or 'I must depart'.")

            while True:
                # Get the next question
                question = self.current_session.next_question()

                # Print the question with clear formatting
                print("\n" + "-"*60)
                
                # Get the tier and display appropriate header
                tier = question.get('tier', 'intermediate')
                if tier == "basic":
                    print("A SIMPLE QUERY FROM THE SCROLLS OF MIDDLE-EARTH:")
                elif tier == "intermediate":
                    print("A RIDDLE FROM THE SCROLLS OF MIDDLE-EARTH:")
                else:  # advanced
                    print("A PROFOUND MYSTERY FROM THE ANCIENT SCROLLS:")
                    
                print("-"*60)
                
                # Get the question text - could be under 'question' or 'text' key
                question_text = question.get('question', question.get('text', 'What do you know about this topic?'))
                
                # Make sure we have a question text to display
                if not question_text or question_text.strip() == '':
                    # If no question text, try to create one based on the entity
                    entity = question.get('entity', 'this topic')
                    if question.get('type') == 'multiple_choice':
                        question_text = f"Which of these options best describes {entity}?"
                    else:
                        question_text = f"What do you know about {entity}?"
                
                # Print the question text with proper spacing
                print(f"\n{question_text}\n")

                # If it's a multiple-choice question, print the options with clear formatting
                # Always display 4 options, even if missing or blank
                options = question.get("options", [])
                if not options or not any(o.strip() for o in options):
                    answer = question.get("correct_answer") or question.get("answer") or "Mordor"
                    options = ["Gondor", "Rohan", "The Shire", answer]
                elif len(options) < 4:
                    distractors = ["Gondor", "Rohan", "Mordor", "The Shire", "Elrond", "Galadriel", "Saruman", "Sauron", "Aragorn", "Legolas", "Gimli", "Frodo", "Samwise", "Pippin", "Merry"]
                    used = set(options)
                    while len(options) < 4:
                        for d in distractors:
                            if d not in used:
                                options.append(d)
                                used.add(d)
                            if len(options) == 4:
                                break
                # Ensure correct answer is present
                answer = question.get("correct_answer") or question.get("answer")
                if answer and answer not in options:
                    options[-1] = answer
                
                # Randomize the options to avoid having the correct answer always in position 4
                import random
                random.shuffle(options)
                
                # Update the correct answer in the question to match the shuffled options
                if answer:
                    question["correct_answer"] = answer
                print("\nConsider these possibilities from the ancient lore:")
                import re
                for i, option in enumerate(options):
                    clean_option = option.strip() if isinstance(option, str) else str(option)
                    # Remove only a single leading 'A)', 'B).', etc. if present
                    clean_option = re.sub(r'^[A-Da-d][).: ]+','', clean_option, count=1)
                    print(f"  {i+1}. {clean_option}")
                # Update question so downstream logic uses correct options
                question["options"] = options

                # Input validation loop for MC questions
                while True:
                    answer = input("\nYour answer, wise traveler: ")

                    # Check if the student wants to quit with Tolkien-themed exit phrases
                    if answer.lower() in ["quit", "exit", "q", "farewell", "i must depart", "goodbye"]:
                        print("\nVery well. May the light of Eärendil guide your path until our next meeting.")
                        return

                    # For multiple-choice questions, validate answer
                    valid = True
                    if "options" in question and len(question["options"]) == 4:
                        opts = question["options"]
                        if answer.isdigit():
                            idx = int(answer) - 1
                            if not (0 <= idx < len(opts)):
                                valid = False
                        else:
                            # Accept only if matches one of the options (case-insensitive, stripped)
                            answer_clean = answer.strip().lower()
                            valid = any(answer_clean == o.strip().lower() for o in opts)
                        if not valid:
                            print("\nThat is not among the choices, young hobbit! Please select a number between 1 and 4 or type the exact option.")
                            continue
                    break

                # For multiple-choice questions, convert numeric answers to the actual option
                if "options" in question and answer.isdigit():
                    option_index = int(answer) - 1
                    if 0 <= option_index < len(question["options"]):
                        answer = question["options"][option_index]

                # Process the answer
                correct, quality_score, feedback = self.current_session.process_answer(answer)

                # Print feedback with Gandalf-themed language and clear formatting
                print("\n" + "-"*60)
                print("GANDALF'S WISDOM:")
                print("-"*60)
                
                # Print the main explanation
                feedback_msg = feedback.get('message') or feedback.get('explanation') or str(feedback)
                print(f"\n{feedback_msg}")
                
                # Print strengths if available
                if feedback.get("strengths") and len(feedback.get("strengths")) > 0:
                    print("\nYour strengths:")
                    for strength in feedback["strengths"]:
                        print(f"  • {strength}")
                
                # Print weaknesses if available and answer was incorrect
                if not correct and feedback.get("weaknesses") and len(feedback.get("weaknesses")) > 0:
                    print("\nAreas for improvement:")
                    for weakness in feedback["weaknesses"]:
                        print(f"  • {weakness}")
                
                # Print next steps or suggestions
                if feedback.get("next_steps") and len(feedback.get("next_steps")) > 0:
                    print("\nFor your continued journey through Middle-earth's lore:")
                    for step in feedback["next_steps"]:
                        print(f"  • {step}")
                elif feedback.get("suggestions") and len(feedback.get("suggestions")) > 0:
                    print("\nFor your continued journey through Middle-earth's lore:")
                    for suggestion in feedback["suggestions"]:
                        print(f"  • {suggestion}")

                # Print current mastery level with Tolkien-themed language
                print("\n" + "-"*60)
                print("YOUR MASTERY OF THE ANCIENT LORE:")
                print("-"*60)

                mastery = self.current_session.student_model.overall_mastery
                if mastery < 30:
                    print(f"\nYour understanding of the lore is like a hobbit who has never left the Shire: {mastery}% of the wisdom awaits you.")
                elif mastery < 60:
                    print(f"\nYour knowledge grows like Bilbo's courage on his journey: {mastery}% of the way to true wisdom.")
                elif mastery < 90:
                    print(f"\nYour wisdom approaches that of the Elven-lords of old: {mastery}% of the lore is known to you.")
                else:
                    print(f"\nYou have attained the wisdom of the White Council itself: {mastery}% mastery of the ancient lore!")

                # Ask if the student wants to continue with Tolkien-themed language
                continue_quiz = input("\nShall we continue our journey through the lore of Middle-earth? (yes/no): ")
                if continue_quiz.lower() not in ["y", "yes", "continue", "proceed", "go on"]:
                    print("\nVery well. Until our next meeting, may the light of Eärendil guide your path.")
                    break

        finally:
            # End the session
            stats = self.current_session.end_session()

            # Print session summary with Tolkien-themed language and improved formatting
            print("\n" + "="*80)
            print("THE CHRONICLES OF YOUR JOURNEY THROUGH MIDDLE-EARTH")
            print("="*80)

            print(f"\n• Time in the company of Gandalf: {stats['summary']['duration_formatted']}")
            print(f"• Ancient riddles encountered: {stats['summary']['total_questions']}")
            print(f"• Wisdom demonstrated: {stats['summary']['correct_answers']} correct answers")
            print(f"• Your insight into the lore: {stats['summary']['accuracy']:.1f}% accuracy")
            print(f"• Mastery of the ancient knowledge: {stats['summary']['mastery_after']}%")

            # Add a thematic farewell message
            print("\n" + "-"*80)
            print("May your path be ever lit by the light of the Eldar, and may the wisdom")
            print("you have gained serve you well on your continued journeys through Middle-earth.")
            print("-"*80)
