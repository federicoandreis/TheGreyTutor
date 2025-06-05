# The Grey Tutor Database

This directory contains the database implementation for The Grey Tutor, which stores user data, conversation history, and caching.

## Database Schema

The database schema consists of the following tables:

- **users**: User accounts
- **user_profiles**: User profiles with mastery and performance data
- **user_sessions**: User sessions for tracking activity
- **conversations**: Conversation records
- **conversation_parameters**: Parameters for conversations
- **messages**: Messages in conversations
- **questions**: Questions asked in conversations
- **answers**: Answers to questions
- **cache_entries**: Cache entries for various data

## Setup

To set up the database, run the setup script:

```bash
./setup_database.sh
```

This script will:
1. Install the required dependencies
2. Start the PostgreSQL database
3. Initialize the database schema
4. Create an admin user
5. Import existing conversation history data

## Moving Original Files to Legacy

After successfully importing the data, you can move the original files to a legacy folder:

```bash
./move_to_legacy.sh
```

This script will:
1. Create legacy directories
2. Copy all files to the legacy directories
3. Provide instructions for removing the original files

## Command-Line Interface

The database comes with a command-line interface for administration:

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

## Development

### Models

The database models are defined in the `models` directory:

- `user.py`: User models
- `conversation.py`: Conversation models
- `cache.py`: Cache models

### Repositories

The repositories for database access are defined in the `repositories` directory:

- `base.py`: Base repository
- `user.py`: User repositories
- `conversation.py`: Conversation repositories
- `cache.py`: Cache repositories

### Migrations

Database migrations are managed using Alembic:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Revert migrations
alembic downgrade -1
```

## Configuration

Database connection parameters are configured using environment variables:

- `DB_USER`: Database username (default: "thegreytutor")
- `DB_PASSWORD`: Database password (default: "thegreytutor")
- `DB_HOST`: Database host (default: "localhost")
- `DB_PORT`: Database port (default: "5432")
- `DB_NAME`: Database name (default: "thegreytutor")

You can set these variables in your environment or create a `.env` file in the project root.
