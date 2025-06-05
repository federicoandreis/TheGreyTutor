"""
Admin interface for The Grey Tutor database.

This module provides a simple admin interface for the database.
"""
import sys
import argparse
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from tabulate import tabulate

from database.connection import get_db
from database.models.user import User, UserProfile, UserSession
from database.models.conversation import Conversation, Message, Question, Answer
from database.repositories.user import UserRepository, UserProfileRepository, UserSessionRepository
from database.repositories.conversation import (
    ConversationRepository, MessageRepository, QuestionRepository, AnswerRepository
)
from database.repositories.cache import CacheRepository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseAdmin:
    """Admin interface for the database."""
    
    def __init__(self):
        """Initialize the admin interface."""
        self.db = next(get_db())
        self.user_repo = UserRepository(self.db)
        self.profile_repo = UserProfileRepository(self.db)
        self.session_repo = UserSessionRepository(self.db)
        self.conversation_repo = ConversationRepository(self.db)
        self.message_repo = MessageRepository(self.db)
        self.question_repo = QuestionRepository(self.db)
        self.answer_repo = AnswerRepository(self.db)
        self.cache_repo = CacheRepository(self.db)
    
    def close(self) -> None:
        """Close the database session."""
        self.db.close()
    
    def list_users(self) -> None:
        """List all users."""
        users = self.user_repo.get_all()
        
        if not users:
            logger.info("No users found.")
            return
        
        # Prepare data for tabulate
        headers = ["ID", "Username", "Email", "Name", "Role", "Created At", "Last Login"]
        data = []
        
        for user in users:
            data.append([
                user.id,
                user.username,
                user.email or "",
                user.name or "",
                user.role,
                user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "",
                user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else ""
            ])
        
        # Print table
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def list_sessions(self, username: Optional[str] = None) -> None:
        """
        List user sessions.
        
        Args:
            username: Username (optional, will list all sessions if not provided)
        """
        if username:
            user = self.user_repo.get_by_username(username)
            if not user:
                logger.error(f"User '{username}' not found.")
                return
            
            sessions = self.session_repo.get_by_user_id(user.id)
        else:
            sessions = self.session_repo.get_all()
        
        if not sessions:
            logger.info("No sessions found.")
            return
        
        # Prepare data for tabulate
        headers = ["ID", "User", "Type", "Start Time", "End Time", "Questions", "Correct", "Accuracy"]
        data = []
        
        for session in sessions:
            # Get username
            user = self.user_repo.get_by_id(session.user_id)
            username = user.username if user else "Unknown"
            
            data.append([
                session.id,
                username,
                session.session_type,
                session.start_time.strftime("%Y-%m-%d %H:%M:%S") if session.start_time else "",
                session.end_time.strftime("%Y-%m-%d %H:%M:%S") if session.end_time else "",
                session.questions_asked or 0,
                session.correct_answers or 0,
                f"{session.accuracy:.2f}" if session.accuracy is not None else ""
            ])
        
        # Print table
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def list_conversations(self, username: Optional[str] = None) -> None:
        """
        List conversations.
        
        Args:
            username: Username (optional, will list all conversations if not provided)
        """
        if username:
            user = self.user_repo.get_by_username(username)
            if not user:
                logger.error(f"User '{username}' not found.")
                return
            
            conversations = self.conversation_repo.get_by_user_id(user.id)
        else:
            conversations = self.conversation_repo.get_all()
        
        if not conversations:
            logger.info("No conversations found.")
            return
        
        # Prepare data for tabulate
        headers = ["ID", "User", "Type", "Start Time", "End Time", "Duration (s)"]
        data = []
        
        for conversation in conversations:
            # Get username
            user = self.user_repo.get_by_id(conversation.user_id)
            username = user.username if user else "Unknown"
            
            data.append([
                conversation.id,
                username,
                conversation.conversation_type,
                conversation.start_time.strftime("%Y-%m-%d %H:%M:%S") if conversation.start_time else "",
                conversation.end_time.strftime("%Y-%m-%d %H:%M:%S") if conversation.end_time else "",
                conversation.duration_seconds or ""
            ])
        
        # Print table
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def list_messages(self, conversation_id: str) -> None:
        """
        List messages in a conversation.
        
        Args:
            conversation_id: Conversation ID
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            logger.error(f"Conversation '{conversation_id}' not found.")
            return
        
        messages = self.message_repo.get_by_conversation_id(conversation_id)
        
        if not messages:
            logger.info("No messages found.")
            return
        
        # Prepare data for tabulate
        headers = ["ID", "Role", "Timestamp", "Content"]
        data = []
        
        for message in messages:
            # Truncate content if too long
            content = message.content
            if len(content) > 50:
                content = content[:47] + "..."
            
            data.append([
                message.id,
                message.role,
                message.timestamp.strftime("%Y-%m-%d %H:%M:%S") if message.timestamp else "",
                content
            ])
        
        # Print table
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def list_questions(self, message_id: Optional[str] = None) -> None:
        """
        List questions.
        
        Args:
            message_id: Message ID (optional, will list all questions if not provided)
        """
        if message_id:
            questions = self.question_repo.get_by_message_id(message_id)
        else:
            questions = self.question_repo.get_all()
        
        if not questions:
            logger.info("No questions found.")
            return
        
        # Prepare data for tabulate
        headers = ["ID", "Type", "Difficulty", "Entity", "Tier", "Community"]
        data = []
        
        for question in questions:
            data.append([
                question.id,
                question.type,
                question.difficulty,
                question.entity,
                question.tier or "",
                question.community_id or ""
            ])
        
        # Print table
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def list_answers(self, question_id: Optional[str] = None) -> None:
        """
        List answers.
        
        Args:
            question_id: Question ID (optional, will list all answers if not provided)
        """
        if question_id:
            answers = self.answer_repo.get_by_question_id(question_id)
        else:
            answers = self.answer_repo.get_all()
        
        if not answers:
            logger.info("No answers found.")
            return
        
        # Prepare data for tabulate
        headers = ["ID", "Question ID", "Content", "Correct", "Quality Score"]
        data = []
        
        for answer in answers:
            # Truncate content if too long
            content = answer.content
            if len(content) > 50:
                content = content[:47] + "..."
            
            data.append([
                answer.id,
                answer.question_id or "",
                content,
                "Yes" if answer.correct else "No" if answer.correct is not None else "",
                f"{answer.quality_score:.2f}" if answer.quality_score is not None else ""
            ])
        
        # Print table
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def list_cache(self, cache_type: Optional[str] = None) -> None:
        """
        List cache entries.
        
        Args:
            cache_type: Cache type (optional, will list all cache entries if not provided)
        """
        if cache_type:
            entries = self.cache_repo.get_by_type(cache_type)
        else:
            entries = self.cache_repo.get_all()
        
        if not entries:
            logger.info("No cache entries found.")
            return
        
        # Prepare data for tabulate
        headers = ["ID", "Type", "Key", "Created At", "Last Accessed", "Access Count"]
        data = []
        
        for entry in entries:
            data.append([
                entry.id,
                entry.cache_type,
                entry.key,
                entry.created_at.strftime("%Y-%m-%d %H:%M:%S") if entry.created_at else "",
                entry.last_accessed.strftime("%Y-%m-%d %H:%M:%S") if entry.last_accessed else "",
                entry.access_count or 0
            ])
        
        # Print table
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def show_user(self, username: str) -> None:
        """
        Show user details.
        
        Args:
            username: Username
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            logger.error(f"User '{username}' not found.")
            return
        
        # Get user profile
        profile = self.profile_repo.get_by_user_id(user.id)
        
        # Print user details
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email or 'N/A'}")
        print(f"Name: {user.name or 'N/A'}")
        print(f"Role: {user.role}")
        print(f"Created At: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'}")
        print(f"Last Login: {user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'N/A'}")
        
        if profile:
            print("\nProfile:")
            print(f"Overall Mastery: {profile.overall_mastery}")
            print(f"Current Objective: {profile.current_objective or 'N/A'}")
            print(f"Last Updated: {profile.last_updated.strftime('%Y-%m-%d %H:%M:%S') if profile.last_updated else 'N/A'}")
            
            if profile.mastered_objectives:
                print("\nMastered Objectives:")
                for objective in profile.mastered_objectives:
                    print(f"- {objective}")
            
            if profile.community_mastery:
                print("\nCommunity Mastery:")
                for community, mastery in profile.community_mastery.items():
                    print(f"- {community}: {mastery}")
            
            if profile.entity_familiarity:
                print("\nEntity Familiarity:")
                for entity, familiarity in profile.entity_familiarity.items():
                    print(f"- {entity}: {familiarity}")
    
    def show_conversation(self, conversation_id: str) -> None:
        """
        Show conversation details.
        
        Args:
            conversation_id: Conversation ID
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            logger.error(f"Conversation '{conversation_id}' not found.")
            return
        
        # Get user
        user = self.user_repo.get_by_id(conversation.user_id)
        username = user.username if user else "Unknown"
        
        # Get messages
        messages = self.message_repo.get_by_conversation_id(conversation_id)
        
        # Print conversation details
        print(f"Conversation ID: {conversation.id}")
        print(f"User: {username}")
        print(f"Type: {conversation.conversation_type}")
        print(f"Start Time: {conversation.start_time.strftime('%Y-%m-%d %H:%M:%S') if conversation.start_time else 'N/A'}")
        print(f"End Time: {conversation.end_time.strftime('%Y-%m-%d %H:%M:%S') if conversation.end_time else 'N/A'}")
        print(f"Duration: {conversation.duration_seconds} seconds" if conversation.duration_seconds else "Duration: N/A")
        
        if conversation.meta_data:
            print("\nMeta Data:")
            for key, value in conversation.meta_data.items():
                print(f"- {key}: {value}")
        
        if messages:
            print("\nMessages:")
            for message in messages:
                print(f"\n[{message.timestamp.strftime('%Y-%m-%d %H:%M:%S') if message.timestamp else 'N/A'}] {message.role.upper()}:")
                print(message.content)
                
                # Get questions for assistant messages
                if message.role == "assistant":
                    questions = self.question_repo.get_by_message_id(message.id)
                    if questions:
                        print("\nQuestions:")
                        for question in questions:
                            print(f"- Type: {question.type}")
                            print(f"  Difficulty: {question.difficulty}")
                            print(f"  Entity: {question.entity}")
                            if question.options:
                                print(f"  Options: {', '.join(question.options)}")
                            if question.correct_answer:
                                print(f"  Correct Answer: {question.correct_answer}")
                
                # Get answers for user messages
                if message.role == "user":
                    answers = self.answer_repo.get_by_message_id(message.id)
                    if answers:
                        print("\nAnswers:")
                        for answer in answers:
                            print(f"- Content: {answer.content}")
                            if answer.correct is not None:
                                print(f"  Correct: {'Yes' if answer.correct else 'No'}")
                            if answer.quality_score is not None:
                                print(f"  Quality Score: {answer.quality_score}")
                            if answer.feedback:
                                print(f"  Feedback: {answer.feedback}")


def main() -> None:
    """Main entry point for the admin interface."""
    parser = argparse.ArgumentParser(description="The Grey Tutor Database Admin Interface")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List users command
    list_users_parser = subparsers.add_parser("list-users", help="List all users")
    
    # List sessions command
    list_sessions_parser = subparsers.add_parser("list-sessions", help="List user sessions")
    list_sessions_parser.add_argument("--username", help="Filter by username")
    
    # List conversations command
    list_conversations_parser = subparsers.add_parser("list-conversations", help="List conversations")
    list_conversations_parser.add_argument("--username", help="Filter by username")
    
    # List messages command
    list_messages_parser = subparsers.add_parser("list-messages", help="List messages in a conversation")
    list_messages_parser.add_argument("conversation_id", help="Conversation ID")
    
    # List questions command
    list_questions_parser = subparsers.add_parser("list-questions", help="List questions")
    list_questions_parser.add_argument("--message-id", help="Filter by message ID")
    
    # List answers command
    list_answers_parser = subparsers.add_parser("list-answers", help="List answers")
    list_answers_parser.add_argument("--question-id", help="Filter by question ID")
    
    # List cache command
    list_cache_parser = subparsers.add_parser("list-cache", help="List cache entries")
    list_cache_parser.add_argument("--type", help="Filter by cache type")
    
    # Show user command
    show_user_parser = subparsers.add_parser("show-user", help="Show user details")
    show_user_parser.add_argument("username", help="Username")
    
    # Show conversation command
    show_conversation_parser = subparsers.add_parser("show-conversation", help="Show conversation details")
    show_conversation_parser.add_argument("conversation_id", help="Conversation ID")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize admin interface
    admin = DatabaseAdmin()
    
    try:
        # Run command
        if args.command == "list-users":
            admin.list_users()
        elif args.command == "list-sessions":
            admin.list_sessions(args.username)
        elif args.command == "list-conversations":
            admin.list_conversations(args.username)
        elif args.command == "list-messages":
            admin.list_messages(args.conversation_id)
        elif args.command == "list-questions":
            admin.list_questions(args.message_id)
        elif args.command == "list-answers":
            admin.list_answers(args.question_id)
        elif args.command == "list-cache":
            admin.list_cache(args.type)
        elif args.command == "show-user":
            admin.show_user(args.username)
        elif args.command == "show-conversation":
            admin.show_conversation(args.conversation_id)
        else:
            parser.print_help()
    finally:
        # Close database session
        admin.close()


if __name__ == "__main__":
    main()
