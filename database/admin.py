"""
Database admin module for The Grey Tutor.

This module provides a command-line interface for managing the database.
"""
import logging
import argparse
import json
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from database.connection import get_db_session, create_tables, drop_tables, reset_database, check_connection
from database.api import DatabaseAPI
from database.init import init_database, import_all, import_users, import_conversations, import_assessment_conversations, import_question_cache, import_assessment_cache

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_users(args):
    """
    List all users.
    
    Args:
        args: Command-line arguments
    """
    with DatabaseAPI() as api:
        users = api.get_users()
        
        if args.json:
            print(json.dumps(users, indent=2))
        else:
            print(f"Found {len(users)} users:")
            for user in users:
                print(f"  {user['id']} - {user['username']} ({user['role']})")

def get_user(args):
    """
    Get a user by ID or username.
    
    Args:
        args: Command-line arguments
    """
    with DatabaseAPI() as api:
        if args.id:
            user = api.get_user(args.id)
        elif args.username:
            user = api.get_user_by_username(args.username)
        else:
            print("Error: Either --id or --username is required")
            return
        
        if not user:
            print(f"User not found")
            return
        
        if args.json:
            print(json.dumps(user, indent=2))
        else:
            print(f"User ID: {user['id']}")
            print(f"Username: {user['username']}")
            print(f"Email: {user['email']}")
            print(f"Name: {user['name']}")
            print(f"Role: {user['role']}")
            print(f"Created at: {user['created_at']}")
            print(f"Last login: {user['last_login']}")
            
            if user['profile']:
                print("Profile:")
                print(f"  ID: {user['profile']['id']}")
                print(f"  Overall mastery: {user['profile']['overall_mastery']}")
                print(f"  Current objective: {user['profile']['current_objective']}")
                print(f"  Last updated: {user['profile']['last_updated']}")

def create_user(args):
    """
    Create a new user.
    
    Args:
        args: Command-line arguments
    """
    with DatabaseAPI() as api:
        # Check if user already exists
        if api.get_user_by_username(args.username):
            print(f"Error: User with username '{args.username}' already exists")
            return
        
        # Create user data
        user_data = {
            "username": args.username,
            "email": args.email,
            "name": args.name,
            "role": args.role,
        }
        
        # Create profile data
        profile_data = {}
        if args.overall_mastery:
            profile_data["overall_mastery"] = float(args.overall_mastery)
        
        if profile_data:
            user_data["profile"] = profile_data
        
        # Create user
        user = api.create_user(user_data)
        
        print(f"User created with ID: {user['id']}")

def update_user(args):
    """
    Update a user.
    
    Args:
        args: Command-line arguments
    """
    with DatabaseAPI() as api:
        # Get user
        if args.id:
            user = api.get_user(args.id)
        elif args.username:
            user = api.get_user_by_username(args.username)
        else:
            print("Error: Either --id or --username is required")
            return
        
        if not user:
            print(f"User not found")
            return
        
        # Create user data
        user_data = {}
        if args.new_username:
            user_data["username"] = args.new_username
        if args.email:
            user_data["email"] = args.email
        if args.name:
            user_data["name"] = args.name
        if args.role:
            user_data["role"] = args.role
        
        # Create profile data
        profile_data = {}
        if args.overall_mastery:
            profile_data["overall_mastery"] = float(args.overall_mastery)
        
        if profile_data:
            user_data["profile"] = profile_data
        
        # Update user
        user = api.update_user(user['id'], user_data)
        
        print(f"User updated with ID: {user['id']}")

def delete_user(args):
    """
    Delete a user.
    
    Args:
        args: Command-line arguments
    """
    with DatabaseAPI() as api:
        # Get user
        if args.id:
            user = api.get_user(args.id)
        elif args.username:
            user = api.get_user_by_username(args.username)
        else:
            print("Error: Either --id or --username is required")
            return
        
        if not user:
            print(f"User not found")
            return
        
        # Confirm deletion
        if not args.force:
            confirm = input(f"Are you sure you want to delete user '{user['username']}' (y/n)? ")
            if confirm.lower() != 'y':
                print("Deletion cancelled")
                return
        
        # Delete user
        if api.delete_user(user['id']):
            print(f"User deleted with ID: {user['id']}")
        else:
            print(f"Error deleting user with ID: {user['id']}")

def list_conversations(args):
    """
    List conversations.
    
    Args:
        args: Command-line arguments
    """
    with DatabaseAPI() as api:
        # Get conversations
        if args.user_id:
            conversations = api.get_user_conversations(args.user_id)
        elif args.username:
            user = api.get_user_by_username(args.username)
            if not user:
                print(f"User not found")
                return
            conversations = api.get_user_conversations(user['id'])
        elif args.session_id:
            conversations = api.get_session_conversations(args.session_id)
        else:
            print("Error: Either --user-id, --username, or --session-id is required")
            return
        
        if args.json:
            print(json.dumps(conversations, indent=2))
        else:
            print(f"Found {len(conversations)} conversations:")
            for conversation in conversations:
                print(f"  {conversation['id']} - {conversation['conversation_type']} - {conversation['start_time']}")

def get_conversation(args):
    """
    Get a conversation by ID.
    
    Args:
        args: Command-line arguments
    """
    with DatabaseAPI() as api:
        conversation = api.get_conversation(args.id)
        
        if not conversation:
            print(f"Conversation not found")
            return
        
        if args.json:
            print(json.dumps(conversation, indent=2))
        else:
            print(f"Conversation ID: {conversation['id']}")
            print(f"User ID: {conversation['user_id']}")
            print(f"Session ID: {conversation['session_id']}")
            print(f"Type: {conversation['conversation_type']}")
            print(f"Start time: {conversation['start_time']}")
            print(f"End time: {conversation['end_time']}")
            print(f"Duration: {conversation['duration_seconds']} seconds")
            print(f"Messages: {len(conversation['messages'])}")
            
            if args.messages:
                print("\nMessages:")
                for message in conversation['messages']:
                    print(f"  {message['timestamp']} - {message['role']}: {message['content'][:50]}...")

def delete_conversation(args):
    """
    Delete a conversation.
    
    Args:
        args: Command-line arguments
    """
    with DatabaseAPI() as api:
        # Get conversation
        conversation = api.get_conversation(args.id)
        
        if not conversation:
            print(f"Conversation not found")
            return
        
        # Confirm deletion
        if not args.force:
            confirm = input(f"Are you sure you want to delete conversation '{conversation['id']}' (y/n)? ")
            if confirm.lower() != 'y':
                print("Deletion cancelled")
                return
        
        # Delete conversation
        if api.delete_conversation(conversation['id']):
            print(f"Conversation deleted with ID: {conversation['id']}")
        else:
            print(f"Error deleting conversation with ID: {conversation['id']}")

def init_db(args):
    """
    Initialize the database.
    
    Args:
        args: Command-line arguments
    """
    # Initialize database
    init_database()
    
    # Import data
    if args.import_all:
        import_all()
    elif args.import_users:
        import_users()
    elif args.import_conversations:
        import_conversations()
    elif args.import_assessment_conversations:
        import_assessment_conversations()
    elif args.import_question_cache:
        import_question_cache()
    elif args.import_assessment_cache:
        import_assessment_cache()

def reset_db(args):
    """
    Reset the database.
    
    Args:
        args: Command-line arguments
    """
    # Confirm reset
    if not args.force:
        confirm = input("Are you sure you want to reset the database? This will delete all data (y/n)? ")
        if confirm.lower() != 'y':
            print("Reset cancelled")
            return
    
    # Reset database
    reset_database()
    print("Database reset")

def main():
    """
    Main function.
    """
    # Create parser
    parser = argparse.ArgumentParser(description="The Grey Tutor Database Admin")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List users command
    list_users_parser = subparsers.add_parser("list-users", help="List all users")
    list_users_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_users_parser.set_defaults(func=list_users)
    
    # Get user command
    get_user_parser = subparsers.add_parser("get-user", help="Get a user by ID or username")
    get_user_parser.add_argument("--id", help="User ID")
    get_user_parser.add_argument("--username", help="Username")
    get_user_parser.add_argument("--json", action="store_true", help="Output as JSON")
    get_user_parser.set_defaults(func=get_user)
    
    # Create user command
    create_user_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_user_parser.add_argument("--username", required=True, help="Username")
    create_user_parser.add_argument("--email", help="Email")
    create_user_parser.add_argument("--name", help="Name")
    create_user_parser.add_argument("--role", default="user", help="Role (default: user)")
    create_user_parser.add_argument("--overall-mastery", help="Overall mastery")
    create_user_parser.set_defaults(func=create_user)
    
    # Update user command
    update_user_parser = subparsers.add_parser("update-user", help="Update a user")
    update_user_parser.add_argument("--id", help="User ID")
    update_user_parser.add_argument("--username", help="Username")
    update_user_parser.add_argument("--new-username", help="New username")
    update_user_parser.add_argument("--email", help="Email")
    update_user_parser.add_argument("--name", help="Name")
    update_user_parser.add_argument("--role", help="Role")
    update_user_parser.add_argument("--overall-mastery", help="Overall mastery")
    update_user_parser.set_defaults(func=update_user)
    
    # Delete user command
    delete_user_parser = subparsers.add_parser("delete-user", help="Delete a user")
    delete_user_parser.add_argument("--id", help="User ID")
    delete_user_parser.add_argument("--username", help="Username")
    delete_user_parser.add_argument("--force", action="store_true", help="Force deletion without confirmation")
    delete_user_parser.set_defaults(func=delete_user)
    
    # List conversations command
    list_conversations_parser = subparsers.add_parser("list-conversations", help="List conversations")
    list_conversations_parser.add_argument("--user-id", help="User ID")
    list_conversations_parser.add_argument("--username", help="Username")
    list_conversations_parser.add_argument("--session-id", help="Session ID")
    list_conversations_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_conversations_parser.set_defaults(func=list_conversations)
    
    # Get conversation command
    get_conversation_parser = subparsers.add_parser("get-conversation", help="Get a conversation by ID")
    get_conversation_parser.add_argument("--id", required=True, help="Conversation ID")
    get_conversation_parser.add_argument("--messages", action="store_true", help="Show messages")
    get_conversation_parser.add_argument("--json", action="store_true", help="Output as JSON")
    get_conversation_parser.set_defaults(func=get_conversation)
    
    # Delete conversation command
    delete_conversation_parser = subparsers.add_parser("delete-conversation", help="Delete a conversation")
    delete_conversation_parser.add_argument("--id", required=True, help="Conversation ID")
    delete_conversation_parser.add_argument("--force", action="store_true", help="Force deletion without confirmation")
    delete_conversation_parser.set_defaults(func=delete_conversation)
    
    # Initialize database command
    init_db_parser = subparsers.add_parser("init-db", help="Initialize the database")
    init_db_parser.add_argument("--import-all", action="store_true", help="Import all data")
    init_db_parser.add_argument("--import-users", action="store_true", help="Import users")
    init_db_parser.add_argument("--import-conversations", action="store_true", help="Import conversations")
    init_db_parser.add_argument("--import-assessment-conversations", action="store_true", help="Import assessment conversations")
    init_db_parser.add_argument("--import-question-cache", action="store_true", help="Import question cache")
    init_db_parser.add_argument("--import-assessment-cache", action="store_true", help="Import assessment cache")
    init_db_parser.set_defaults(func=init_db)
    
    # Reset database command
    reset_db_parser = subparsers.add_parser("reset-db", help="Reset the database")
    reset_db_parser.add_argument("--force", action="store_true", help="Force reset without confirmation")
    reset_db_parser.set_defaults(func=reset_db)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run command
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
