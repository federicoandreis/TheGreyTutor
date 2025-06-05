"""
Command-line interface for The Grey Tutor database.

This module provides a command-line interface for database administration.
"""
import os
import sys
import argparse
import logging
import getpass
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import uuid
import bcrypt

from sqlalchemy.orm import Session
from database.connection import get_db, init_db
from database.models.user import User, UserProfile
from database.repositories.user import UserRepository, UserProfileRepository
from database.utils.import_data import import_conversation_history, import_assessment_conversations

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def init_database(args: argparse.Namespace) -> None:
    """
    Initialize the database.
    
    Args:
        args: Command-line arguments
    """
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")


def create_user(args: argparse.Namespace) -> None:
    """
    Create a new user.
    
    Args:
        args: Command-line arguments
    """
    db = next(get_db())
    user_repo = UserRepository(db)
    profile_repo = UserProfileRepository(db)
    
    # Check if user already exists
    existing_user = user_repo.get_by_username(args.username)
    if existing_user:
        logger.error(f"User '{args.username}' already exists.")
        return
    
    # Get password if not provided
    password = args.password
    if not password:
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            logger.error("Passwords do not match.")
            return
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user
    user = user_repo.create({
        "username": args.username,
        "email": args.email,
        "password_hash": password_hash,
        "name": args.name,
        "role": args.role,
        "created_at": datetime.utcnow()
    })
    
    if not user:
        logger.error("Failed to create user.")
        return
    
    # Create user profile
    profile = profile_repo.create({
        "user_id": user.id,
        "community_mastery": {},
        "entity_familiarity": {},
        "question_type_performance": {},
        "difficulty_performance": {},
        "overall_mastery": 0.0,
        "mastered_objectives": [],
        "last_updated": datetime.utcnow()
    })
    
    if not profile:
        logger.error("Failed to create user profile.")
        return
    
    logger.info(f"User '{args.username}' created successfully.")


def list_users(args: argparse.Namespace) -> None:
    """
    List users.
    
    Args:
        args: Command-line arguments
    """
    db = next(get_db())
    user_repo = UserRepository(db)
    
    users = user_repo.get_all()
    
    if not users:
        logger.info("No users found.")
        return
    
    # Print users
    print(f"{'ID':<36} {'Username':<20} {'Email':<30} {'Role':<10} {'Created At'}")
    print("-" * 100)
    
    for user in users:
        print(f"{user.id:<36} {user.username:<20} {user.email or '':<30} {user.role:<10} {user.created_at}")


def delete_user(args: argparse.Namespace) -> None:
    """
    Delete a user.
    
    Args:
        args: Command-line arguments
    """
    db = next(get_db())
    user_repo = UserRepository(db)
    
    # Check if user exists
    user = user_repo.get_by_username(args.username)
    if not user:
        logger.error(f"User '{args.username}' not found.")
        return
    
    # Confirm deletion
    if not args.force:
        confirm = input(f"Are you sure you want to delete user '{args.username}'? (y/n): ")
        if confirm.lower() != 'y':
            logger.info("User deletion cancelled.")
            return
    
    # Delete user
    if user_repo.delete(user.id):
        logger.info(f"User '{args.username}' deleted successfully.")
    else:
        logger.error(f"Failed to delete user '{args.username}'.")


def reset_password(args: argparse.Namespace) -> None:
    """
    Reset a user's password.
    
    Args:
        args: Command-line arguments
    """
    db = next(get_db())
    user_repo = UserRepository(db)
    
    # Check if user exists
    user = user_repo.get_by_username(args.username)
    if not user:
        logger.error(f"User '{args.username}' not found.")
        return
    
    # Get new password
    password = args.password
    if not password:
        password = getpass.getpass("Enter new password: ")
        password_confirm = getpass.getpass("Confirm new password: ")
        if password != password_confirm:
            logger.error("Passwords do not match.")
            return
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update user
    if user_repo.update(user.id, {"password_hash": password_hash}):
        logger.info(f"Password for user '{args.username}' reset successfully.")
    else:
        logger.error(f"Failed to reset password for user '{args.username}'.")


def import_data(args: argparse.Namespace) -> None:
    """
    Import data from existing files.
    
    Args:
        args: Command-line arguments
    """
    db = next(get_db())
    
    # Import conversation history
    if args.conversations:
        logger.info(f"Importing conversation history from '{args.conversations}'...")
        stats = import_conversation_history(args.conversations, db)
        logger.info(f"Conversation history import complete: {stats}")
    
    # Import assessment conversations
    if args.assessments:
        logger.info(f"Importing assessment conversations from '{args.assessments}'...")
        stats = import_assessment_conversations(args.assessments, db)
        logger.info(f"Assessment conversations import complete: {stats}")


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="The Grey Tutor Database CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init database command
    init_parser = subparsers.add_parser("init", help="Initialize the database")
    
    # Create user command
    create_user_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_user_parser.add_argument("username", help="Username")
    create_user_parser.add_argument("--email", help="Email address")
    create_user_parser.add_argument("--name", help="Full name")
    create_user_parser.add_argument("--role", default="user", choices=["user", "admin"], help="User role")
    create_user_parser.add_argument("--password", help="Password (will prompt if not provided)")
    
    # List users command
    list_users_parser = subparsers.add_parser("list-users", help="List users")
    
    # Delete user command
    delete_user_parser = subparsers.add_parser("delete-user", help="Delete a user")
    delete_user_parser.add_argument("username", help="Username")
    delete_user_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    # Reset password command
    reset_password_parser = subparsers.add_parser("reset-password", help="Reset a user's password")
    reset_password_parser.add_argument("username", help="Username")
    reset_password_parser.add_argument("--password", help="New password (will prompt if not provided)")
    
    # Import data command
    import_parser = subparsers.add_parser("import", help="Import data from existing files")
    import_parser.add_argument("--conversations", help="Directory containing conversation history files")
    import_parser.add_argument("--assessments", help="Directory containing assessment conversation files")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run command
    if args.command == "init":
        init_database(args)
    elif args.command == "create-user":
        create_user(args)
    elif args.command == "list-users":
        list_users(args)
    elif args.command == "delete-user":
        delete_user(args)
    elif args.command == "reset-password":
        reset_password(args)
    elif args.command == "import":
        import_data(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
