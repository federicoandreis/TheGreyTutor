"""
Database initialization module for The Grey Tutor.

This module provides functions for initializing the database and importing data.
"""
import logging
import os
import json
import glob
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.connection import get_db_session, create_tables, check_connection
from database.models.user import User, UserProfile, UserSession
from database.models.conversation import Conversation, ConversationParameters, Message, Question, Answer
from database.models.cache import Cache, QuestionCache, AssessmentCache
from database.repositories.user import UserRepository, UserProfileRepository, UserSessionRepository
from database.repositories.conversation import ConversationRepository, MessageRepository, QuestionRepository, AnswerRepository
from database.repositories.cache import CacheRepository, QuestionCacheRepository, AssessmentCacheRepository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database() -> None:
    """
    Initialize the database.
    """
    logger.info("Checking database connection...")
    if not check_connection():
        logger.error("Database connection failed. Aborting initialization.")
        raise RuntimeError("Database connection failed.")

    logger.info("Creating tables...")
    create_tables()
    logger.info("Database tables created successfully.")

    # Optional: verify tables exist
    db = get_db_session()
    try:
        from sqlalchemy import text
        tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
        logger.info(f"Tables present after creation: {[t[0] for t in tables]}")
    finally:
        db.close()


def import_users() -> None:
    """
    Import users from student_models directory.
    """
    # Get database session
    db = get_db_session()
    
    try:
        # Create repositories
        user_repo = UserRepository(db)
        profile_repo = UserProfileRepository(db)
        
        # Get all user files
        user_files = glob.glob("student_models/*.json")
        
        # Import users
        for user_file in user_files:
            try:
                # Get username from filename
                username = os.path.basename(user_file).replace(".json", "")
                
                # Skip if user already exists
                if user_repo.get_by_username(username):
                    logger.info(f"User {username} already exists, skipping")
                    continue
                
                # Load user data
                with open(user_file, "r") as f:
                    user_data = json.load(f)
                
                # Create user
                user = user_repo.create({
                    "username": username,
                    "email": user_data.get("email"),
                    "name": user_data.get("name", username),
                    "role": "user",
                })
                
                # Create user profile
                profile_data = {
                    "user_id": user.id,
                    "community_mastery": user_data.get("community_mastery", {}),
                    "entity_familiarity": user_data.get("entity_familiarity", {}),
                    "question_type_performance": user_data.get("question_type_performance", {}),
                    "difficulty_performance": user_data.get("difficulty_performance", {}),
                    "overall_mastery": user_data.get("overall_mastery", 0.0),
                    "mastered_objectives": user_data.get("mastered_objectives", []),
                    "current_objective": user_data.get("current_objective"),
                }
                profile_repo.create(profile_data)
                
                logger.info(f"Imported user {username}")
            except Exception as e:
                logger.error(f"Error importing user from {user_file}: {e}")
    except Exception as e:
        logger.error(f"Error importing users: {e}")
    finally:
        db.close()

def import_conversations() -> None:
    """
    Import conversations from conversation_history directory.
    """
    # Get database session
    db = get_db_session()
    
    try:
        # Create repositories
        user_repo = UserRepository(db)
        session_repo = UserSessionRepository(db)
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)
        
        # Get all conversation directories
        conversation_dirs = [d for d in os.listdir("conversation_history") if os.path.isdir(os.path.join("conversation_history", d))]
        
        # Import conversations
        for dir_name in conversation_dirs:
            try:
                # Get username from directory name
                username = dir_name
                
                # Get user
                user = user_repo.get_by_username(username)
                if not user:
                    logger.warning(f"User {username} not found, skipping conversations")
                    continue
                
                # Get all conversation files
                conversation_files = glob.glob(f"conversation_history/{dir_name}/conversation_*.json")
                
                # Import conversations
                for conversation_file in conversation_files:
                    try:
                        # Load conversation data
                        with open(conversation_file, "r") as f:
                            conversation_data = json.load(f)
                        
                        # Extract conversation ID from filename
                        filename = os.path.basename(conversation_file)
                        conversation_id = filename.split("_")[1].split(".")[0]
                        
                        # Skip if conversation already exists
                        if conversation_repo.get_by_id(conversation_id):
                            logger.info(f"Conversation {conversation_id} already exists, skipping")
                            continue
                        
                        # Create user session
                        session_data = {
                            "user_id": user.id,
                            "session_type": "chat",
                            "start_time": datetime.fromisoformat(conversation_data.get("start_time", datetime.utcnow().isoformat())),
                            "end_time": datetime.fromisoformat(conversation_data.get("end_time", datetime.utcnow().isoformat())) if conversation_data.get("end_time") else None,
                        }
                        session = session_repo.create(session_data)
                        
                        # Create conversation
                        conversation_data = {
                            "id": conversation_id,
                            "user_id": user.id,
                            "session_id": session.id,
                            "conversation_type": "chat",
                            "start_time": datetime.fromisoformat(conversation_data.get("start_time", datetime.utcnow().isoformat())),
                            "end_time": datetime.fromisoformat(conversation_data.get("end_time", datetime.utcnow().isoformat())) if conversation_data.get("end_time") else None,
                            "meta_data": conversation_data.get("meta_data", {}),
                        }
                        conversation = conversation_repo.create(conversation_data)
                        
                        # Create messages
                        for message_data in conversation_data.get("messages", []):
                            message = message_repo.create({
                                "conversation_id": conversation.id,
                                "role": message_data.get("role", "user"),
                                "content": message_data.get("content", ""),
                                "timestamp": datetime.fromisoformat(message_data.get("timestamp", datetime.utcnow().isoformat())),
                                "meta_data": message_data.get("meta_data", {}),
                            })
                        
                        logger.info(f"Imported conversation {conversation_id}")
                    except Exception as e:
                        logger.error(f"Error importing conversation from {conversation_file}: {e}")
            except Exception as e:
                logger.error(f"Error importing conversations for user {dir_name}: {e}")
    except Exception as e:
        logger.error(f"Error importing conversations: {e}")
    finally:
        db.close()

def import_assessment_conversations() -> None:
    """
    Import assessment conversations from assessment_conversations directory.
    """
    # Get database session
    db = get_db_session()
    
    try:
        # Create repositories
        user_repo = UserRepository(db)
        session_repo = UserSessionRepository(db)
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)
        question_repo = QuestionRepository(db)
        answer_repo = AnswerRepository(db)
        
        # Get all assessment conversation directories
        assessment_dirs = [d for d in os.listdir("assessment_conversations") if os.path.isdir(os.path.join("assessment_conversations", d))]
        
        # Import assessment conversations
        for dir_name in assessment_dirs:
            try:
                # Get username from directory name
                username = dir_name
                
                # Get user
                user = user_repo.get_by_username(username)
                if not user and username != "anonymous":
                    logger.warning(f"User {username} not found, skipping assessment conversations")
                    continue
                
                # Get all assessment conversation files
                assessment_files = glob.glob(f"assessment_conversations/{dir_name}/conversation_*.json")
                
                # Import assessment conversations
                for assessment_file in assessment_files:
                    try:
                        # Load assessment conversation data
                        with open(assessment_file, "r") as f:
                            assessment_data = json.load(f)
                        
                        # Extract conversation ID from filename
                        filename = os.path.basename(assessment_file)
                        conversation_id = filename.split("_")[1].split(".")[0]
                        
                        # Skip if conversation already exists
                        if conversation_repo.get_by_id(conversation_id):
                            logger.info(f"Assessment conversation {conversation_id} already exists, skipping")
                            continue
                        
                        # Create user session
                        session_data = {
                            "user_id": user.id if user else None,
                            "session_type": "assessment",
                            "start_time": datetime.fromisoformat(assessment_data.get("start_time", datetime.utcnow().isoformat())),
                            "end_time": datetime.fromisoformat(assessment_data.get("end_time", datetime.utcnow().isoformat())) if assessment_data.get("end_time") else None,
                        }
                        session = session_repo.create(session_data)
                        
                        # Create conversation
                        conversation_data = {
                            "id": conversation_id,
                            "user_id": user.id if user else None,
                            "session_id": session.id,
                            "conversation_type": "assessment",
                            "start_time": datetime.fromisoformat(assessment_data.get("start_time", datetime.utcnow().isoformat())),
                            "end_time": datetime.fromisoformat(assessment_data.get("end_time", datetime.utcnow().isoformat())) if assessment_data.get("end_time") else None,
                            "meta_data": assessment_data.get("meta_data", {}),
                        }
                        conversation = conversation_repo.create(conversation_data)
                        
                        # Create messages, questions, and answers
                        for message_data in assessment_data.get("messages", []):
                            message = message_repo.create({
                                "conversation_id": conversation.id,
                                "role": message_data.get("role", "user"),
                                "content": message_data.get("content", ""),
                                "timestamp": datetime.fromisoformat(message_data.get("timestamp", datetime.utcnow().isoformat())),
                                "meta_data": message_data.get("meta_data", {}),
                            })
                            
                            # Create question if message is a question
                            if message_data.get("role") == "assistant" and message_data.get("meta_data", {}).get("is_question"):
                                question_data = message_data.get("meta_data", {}).get("question", {})
                                question = question_repo.create({
                                    "message_id": message.id,
                                    "type": question_data.get("type", "multiple_choice"),
                                    "difficulty": question_data.get("difficulty", "medium"),
                                    "entity": question_data.get("entity"),
                                    "tier": question_data.get("tier"),
                                    "options": question_data.get("options"),
                                    "correct_answer": question_data.get("correct_answer"),
                                    "community_id": question_data.get("community_id"),
                                    "meta_data": question_data.get("meta_data", {}),
                                })
                            
                            # Create answer if message is an answer
                            if message_data.get("role") == "user" and message_data.get("meta_data", {}).get("is_answer"):
                                answer_data = message_data.get("meta_data", {}).get("answer", {})
                                question_id = answer_data.get("question_id")
                                
                                # Find question
                                question = None
                                for q in question_repo.get_all():
                                    if q.meta_data.get("original_id") == question_id:
                                        question = q
                                        break
                                
                                if question:
                                    answer = answer_repo.create({
                                        "message_id": message.id,
                                        "question_id": question.id,
                                        "content": message_data.get("content", ""),
                                        "correct": answer_data.get("correct"),
                                        "quality_score": answer_data.get("quality_score"),
                                        "feedback": answer_data.get("feedback"),
                                    })
                        
                        logger.info(f"Imported assessment conversation {conversation_id}")
                    except Exception as e:
                        logger.error(f"Error importing assessment conversation from {assessment_file}: {e}")
            except Exception as e:
                logger.error(f"Error importing assessment conversations for user {dir_name}: {e}")
    except Exception as e:
        logger.error(f"Error importing assessment conversations: {e}")
    finally:
        db.close()

def import_question_cache() -> None:
    """
    Import question cache from question_cache directory.
    """
    # Get database session
    db = get_db_session()
    
    try:
        # Create repository
        question_cache_repo = QuestionCacheRepository(db)
        
        # Get question cache file
        question_cache_file = "question_cache/question_cache.json"
        
        # Check if file exists
        if not os.path.exists(question_cache_file):
            logger.warning(f"Question cache file {question_cache_file} not found, skipping")
            return
        
        # Load question cache data
        with open(question_cache_file, "r") as f:
            question_cache_data = json.load(f)
        
        # Import question cache
        for question_id, question_data in question_cache_data.items():
            try:
                # Skip if question cache already exists
                if question_cache_repo.get_by_question_id(question_id):
                    logger.info(f"Question cache for question {question_id} already exists, skipping")
                    continue
                
                # Create question cache
                question_cache = question_cache_repo.create({
                    "question_id": question_id,
                    "question_text": question_data.get("question_text", ""),
                    "question_type": question_data.get("question_type", "multiple_choice"),
                    "difficulty": question_data.get("difficulty", "medium"),
                    "entity": question_data.get("entity"),
                    "tier": question_data.get("tier"),
                    "options": question_data.get("options"),
                    "correct_answer": question_data.get("correct_answer"),
                    "community_id": question_data.get("community_id"),
                    "meta_data": question_data.get("meta_data", {}),
                })
                
                logger.info(f"Imported question cache for question {question_id}")
            except Exception as e:
                logger.error(f"Error importing question cache for question {question_id}: {e}")
    except Exception as e:
        logger.error(f"Error importing question cache: {e}")
    finally:
        db.close()

def import_assessment_cache() -> None:
    """
    Import assessment cache from assessment_cache directory.
    """
    # Get database session
    db = get_db_session()
    
    try:
        # Create repository
        assessment_cache_repo = AssessmentCacheRepository(db)
        
        # Get assessment cache file
        assessment_cache_file = "assessment_cache/assessment_cache.json"
        
        # Check if file exists
        if not os.path.exists(assessment_cache_file):
            logger.warning(f"Assessment cache file {assessment_cache_file} not found, skipping")
            return
        
        # Load assessment cache data
        with open(assessment_cache_file, "r") as f:
            assessment_cache_data = json.load(f)
        
        # Import assessment cache
        for assessment_id, assessment_data in assessment_cache_data.items():
            if not isinstance(assessment_data, dict):
                logger.warning(f"Skipping assessment cache entry for {assessment_id}: expected dict, got {type(assessment_data).__name__}")
                continue
            try:
                # Skip if assessment cache already exists
                if assessment_cache_repo.get_by_assessment_id(assessment_id):
                    logger.info(f"Assessment cache for assessment {assessment_id} already exists, skipping")
                    continue
                
                # Create assessment cache
                assessment_cache = assessment_cache_repo.create({
                    "assessment_id": assessment_id,
                    "user_id": assessment_data.get("user_id"),
                    "assessment_type": assessment_data.get("assessment_type", "quiz"),
                    "questions": assessment_data.get("questions", []),
                    "answers": assessment_data.get("answers", []),
                    "score": assessment_data.get("score", 0.0),
                    "max_score": assessment_data.get("max_score", 0.0),
                })
                
                logger.info(f"Imported assessment cache for assessment {assessment_id}")
            except Exception as e:
                logger.error(f"Error importing assessment cache for assessment {assessment_id}: {e}")
    except Exception as e:
        logger.error(f"Error importing assessment cache: {e}")
    finally:
        db.close()

def import_all() -> None:
    """
    Import all data.
    """
    # Import users
    import_users()
    
    # Import conversations
    import_conversations()
    
    # Import assessment conversations
    import_assessment_conversations()
    
    # Import question cache
    import_question_cache()
    
    # Import assessment cache
    import_assessment_cache()
    
    logger.info("All data imported")

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Import all data
    import_all()
