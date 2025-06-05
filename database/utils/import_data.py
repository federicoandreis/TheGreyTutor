"""
Data import utilities for The Grey Tutor.

This module provides functions for importing data from existing files.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import re

from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.user import User, UserProfile
from database.models.conversation import Conversation, Message, Question, Answer
from database.repositories.user import UserRepository, UserProfileRepository
from database.repositories.conversation import ConversationRepository, MessageRepository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def import_conversation_history(base_dir: str, db: Optional[Session] = None) -> Dict[str, int]:
    """
    Import conversation history from JSON files.
    
    Args:
        base_dir: Base directory containing conversation history files
        db: SQLAlchemy session (optional, will create one if not provided)
        
    Returns:
        Dictionary with counts of imported items
    """
    if db is None:
        db = next(get_db())
    
    user_repo = UserRepository(db)
    profile_repo = UserProfileRepository(db)
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    
    stats = {
        "users": 0,
        "conversations": 0,
        "messages": 0,
        "questions": 0,
        "answers": 0,
        "errors": 0
    }
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                try:
                    file_path = os.path.join(root, file)
                    logger.info(f"Processing file: {file_path}")
                    
                    # Extract username from path
                    path_parts = root.split(os.path.sep)
                    username = path_parts[-1]  # Last directory name is the username
                    
                    # Load JSON data
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Process the conversation
                    process_conversation(
                        username, file, data, user_repo, profile_repo, 
                        conversation_repo, message_repo, stats
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing file {file}: {e}")
                    stats["errors"] += 1
    
    return stats


def process_conversation(
    username: str, 
    filename: str, 
    data: Dict[str, Any],
    user_repo: UserRepository,
    profile_repo: UserProfileRepository,
    conversation_repo: ConversationRepository,
    message_repo: MessageRepository,
    stats: Dict[str, int]
) -> None:
    """
    Process a conversation JSON file.
    
    Args:
        username: Username
        filename: Filename
        data: Conversation data
        user_repo: User repository
        profile_repo: User profile repository
        conversation_repo: Conversation repository
        message_repo: Message repository
        stats: Statistics dictionary
    """
    # Get or create user
    user = user_repo.get_by_username(username)
    if not user:
        user = user_repo.create({
            "username": username,
            "password_hash": "imported",  # Placeholder, will need to be reset
            "role": "user",
            "created_at": datetime.utcnow()
        })
        
        # Create user profile
        profile_repo.create({
            "user_id": user.id,
            "community_mastery": {},
            "entity_familiarity": {},
            "question_type_performance": {},
            "difficulty_performance": {},
            "overall_mastery": 0.0,
            "mastered_objectives": [],
            "last_updated": datetime.utcnow()
        })
        
        stats["users"] += 1
    
    # Extract conversation ID and timestamp from filename
    # Example: conversation_0e74da91-20cd-4927-a759-00ceec454934_20250603_092831.json
    match = re.match(r'conversation_([a-f0-9-]+)_(\d+)_(\d+)\.json', filename)
    if match:
        conversation_id = match.group(1)
        timestamp_str = match.group(2) + match.group(3)
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
        except ValueError:
            timestamp = datetime.utcnow()
    else:
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
    
    # Create conversation
    conversation_type = data.get("type", "chat")
    conversation = conversation_repo.create({
        "id": conversation_id,
        "user_id": user.id,
        "conversation_type": conversation_type,
        "start_time": timestamp,
        "end_time": None,  # Will be updated when processing messages
        "metadata": {
            "imported": True,
            "original_filename": filename
        }
    })
    
    stats["conversations"] += 1
    
    # Process messages
    if "messages" in data:
        process_messages(data["messages"], conversation.id, message_repo, stats)
    
    # Update conversation end time
    if "messages" in data and data["messages"]:
        last_message = data["messages"][-1]
        if "timestamp" in last_message:
            try:
                end_time = datetime.fromisoformat(last_message["timestamp"].replace('Z', '+00:00'))
                conversation_repo.update(conversation.id, {"end_time": end_time})
            except (ValueError, TypeError):
                pass


def process_messages(
    messages: List[Dict[str, Any]],
    conversation_id: str,
    message_repo: MessageRepository,
    stats: Dict[str, int]
) -> None:
    """
    Process messages from a conversation.
    
    Args:
        messages: List of messages
        conversation_id: Conversation ID
        message_repo: Message repository
        stats: Statistics dictionary
    """
    for msg_data in messages:
        try:
            role = msg_data.get("role", "user")
            content = msg_data.get("content", "")
            
            # Parse timestamp
            timestamp = datetime.utcnow()
            if "timestamp" in msg_data:
                try:
                    timestamp = datetime.fromisoformat(msg_data["timestamp"].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    pass
            
            # Create message
            message = message_repo.create({
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "timestamp": timestamp,
                "metadata": {
                    "imported": True,
                    "original_data": {k: v for k, v in msg_data.items() if k not in ["role", "content", "timestamp"]}
                }
            })
            
            stats["messages"] += 1
            
            # Process questions and answers
            if role == "assistant" and "questions" in msg_data:
                for q_data in msg_data["questions"]:
                    process_question(q_data, message.id, stats)
            
            if role == "user" and "answers" in msg_data:
                for a_data in msg_data["answers"]:
                    process_answer(a_data, message.id, stats)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            stats["errors"] += 1


def process_question(question_data: Dict[str, Any], message_id: str, stats: Dict[str, int]) -> None:
    """
    Process a question.
    
    Args:
        question_data: Question data
        message_id: Message ID
        stats: Statistics dictionary
    """
    try:
        db = next(get_db())
        
        # Create question
        question = Question(
            id=str(uuid.uuid4()),
            message_id=message_id,
            type=question_data.get("type", "unknown"),
            difficulty=question_data.get("difficulty", 1),
            entity=question_data.get("entity", "unknown"),
            tier=question_data.get("tier"),
            options=question_data.get("options"),
            correct_answer=question_data.get("correct_answer"),
            community_id=question_data.get("community_id"),
            metadata={
                "imported": True,
                "original_data": {k: v for k, v in question_data.items() if k not in [
                    "type", "difficulty", "entity", "tier", "options", "correct_answer", "community_id"
                ]}
            }
        )
        
        db.add(question)
        db.commit()
        
        stats["questions"] += 1
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        stats["errors"] += 1


def process_answer(answer_data: Dict[str, Any], message_id: str, stats: Dict[str, int]) -> None:
    """
    Process an answer.
    
    Args:
        answer_data: Answer data
        message_id: Message ID
        stats: Statistics dictionary
    """
    try:
        db = next(get_db())
        
        # Create answer
        answer = Answer(
            id=str(uuid.uuid4()),
            message_id=message_id,
            question_id=answer_data.get("question_id"),
            content=answer_data.get("content", ""),
            correct=answer_data.get("correct"),
            quality_score=answer_data.get("quality_score"),
            feedback=answer_data.get("feedback")
        )
        
        db.add(answer)
        db.commit()
        
        stats["answers"] += 1
        
    except Exception as e:
        logger.error(f"Error processing answer: {e}")
        stats["errors"] += 1


def import_assessment_conversations(base_dir: str, db: Optional[Session] = None) -> Dict[str, int]:
    """
    Import assessment conversations from JSON files.
    
    Args:
        base_dir: Base directory containing assessment conversation files
        db: SQLAlchemy session (optional, will create one if not provided)
        
    Returns:
        Dictionary with counts of imported items
    """
    if db is None:
        db = next(get_db())
    
    user_repo = UserRepository(db)
    profile_repo = UserProfileRepository(db)
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    
    stats = {
        "users": 0,
        "conversations": 0,
        "messages": 0,
        "questions": 0,
        "answers": 0,
        "errors": 0
    }
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                try:
                    file_path = os.path.join(root, file)
                    logger.info(f"Processing assessment file: {file_path}")
                    
                    # Extract username from path
                    path_parts = root.split(os.path.sep)
                    username = path_parts[-1]  # Last directory name is the username
                    
                    # Load JSON data
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Process the conversation with assessment type
                    process_conversation(
                        username, file, data, user_repo, profile_repo, 
                        conversation_repo, message_repo, stats
                    )
                    
                    # Update conversation type to assessment
                    conversation_id = None
                    match = re.match(r'conversation_([a-f0-9-]+)_(\d+)_(\d+)\.json', file)
                    if match:
                        conversation_id = match.group(1)
                        conversation_repo.update(conversation_id, {"conversation_type": "assessment"})
                    
                except Exception as e:
                    logger.error(f"Error processing assessment file {file}: {e}")
                    stats["errors"] += 1
    
    return stats
