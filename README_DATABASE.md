# The Grey Tutor Database System

This document describes the new database system for The Grey Tutor, which replaces the previous file-based storage approach with a robust PostgreSQL database.

## Overview

The database system consists of:

1. A PostgreSQL database for storing user data, conversation history, and cache entries
2. SQLAlchemy ORM models for interacting with the database
3. Repository classes for database operations
4. Migration scripts for database schema management
5. Command-line tools for administration
6. Utility functions for importing existing data

## Getting Started

### Prerequisites

- Docker and Docker Compose (for running PostgreSQL)
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Start the PostgreSQL database:

```bash
docker-compose up -d postgres
```

3. Initialize the database and import existing data:

```bash
./setup_database.sh
```

4. After successful import, move original files to legacy folder:

```bash
./move_to_legacy.sh
```

## Database Schema

The database schema includes the following tables:

- **users**: User accounts
- **user_profiles**: User profiles with mastery and performance data
- **user_sessions**: User sessions for tracking activity
- **conversations**: Conversation records
- **conversation_parameters**: Parameters for conversations
- **messages**: Messages in conversations
- **questions**: Questions asked in conversations
- **answers**: Answers to questions
- **cache_entries**: Cache entries for various data

## Command-Line Interface

The database system includes a command-line interface for administration:

```bash
python -m database.cli [command] [options]
```

Available commands:

- **init**: Initialize the database
- **create-user**: Create a new user
- **list-users**: List all users
- **delete-user**: Delete a user
- **reset-password**: Reset a user's password
- **import**: Import data from existing files

For help on a specific command:

```bash
python -m database.cli [command] --help
```

## Admin Interface

The database system also includes an admin interface for viewing and managing data:

```bash
./run_admin.sh [command] [options]
```

Available commands:

- **list-users**: List all users
- **list-sessions**: List user sessions
- **list-conversations**: List conversations
- **list-messages**: List messages in a conversation
- **list-questions**: List questions
- **list-answers**: List answers
- **list-cache**: List cache entries
- **show-user**: Show user details
- **show-conversation**: Show conversation details

For help on a specific command:

```bash
./run_admin.sh [command] --help
```

## API

The database system provides an API for interacting with the database from other parts of the application:

```python
from database.api import DatabaseAPI

# Initialize API
api = DatabaseAPI()

# Get user
user = api.get_user("username")

# Create conversation
conversation = api.create_conversation(
    "username",
    {"conversation_type": "chat"},
    {"parameter_type": "default"}
)

# Add message
message = api.add_message(conversation["id"], {
    "role": "user",
    "content": "Hello, world!"
})

# Close API session
api.close()
```

## Testing

The database system includes test scripts for verifying functionality:

```bash
# Test database connection
python -m database.test_connection

# Test API
python -m database.test_api
```

## Configuration

Database connection parameters are configured using environment variables:

- `DB_USER`: Database username (default: "thegreytutor")
- `DB_PASSWORD`: Database password (default: "thegreytutor")
- `DB_HOST`: Database host (default: "localhost")
- `DB_PORT`: Database port (default: "5432")
- `DB_NAME`: Database name (default: "thegreytutor")

You can set these variables in your environment or create a `.env` file in the project root.

## Directory Structure

```
database/
├── __init__.py           # Package initialization
├── connection.py         # Database connection
├── api.py                # API for interacting with the database
├── cli.py                # Command-line interface
├── admin.py              # Admin interface
├── test_connection.py    # Test script for database connection
├── test_api.py           # Test script for API
├── models/               # Database models
│   ├── __init__.py
│   ├── user.py           # User models
│   ├── conversation.py   # Conversation models
│   └── cache.py          # Cache models
├── repositories/         # Database repositories
│   ├── __init__.py
│   ├── base.py           # Base repository
│   ├── user.py           # User repositories
│   ├── conversation.py   # Conversation repositories
│   └── cache.py          # Cache repositories
├── migrations/           # Database migrations
│   ├── __init__.py
│   ├── env.py            # Alembic environment
│   ├── script.py.mako    # Alembic script template
│   └── versions/         # Migration versions
│       └── 001_initial_schema.py
└── utils/                # Utility functions
    ├── __init__.py
    └── import_data.py    # Data import utilities
```

## Scripts

- `setup_database.sh`: Set up the database and import existing data
- `move_to_legacy.sh`: Move original files to legacy folder
- `run_admin.sh`: Run the admin interface

## Legacy Data

After importing the data, the original files are moved to the `legacy` directory:

```
legacy/
├── conversation_history/
├── assessment_conversations/
└── kg_quizzing/
    └── scripts/
        └── assessment_conversations/
```

## Further Documentation

For more detailed information, see:

- [Database README](database/README.md): Detailed documentation for the database system
- [Alembic Documentation](https://alembic.sqlalchemy.org/): Documentation for Alembic, the migration tool
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/): Documentation for SQLAlchemy, the ORM
