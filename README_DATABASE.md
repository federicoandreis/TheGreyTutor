# The Grey Tutor Database

This document describes the database implementation for The Grey Tutor.

## Overview

The Grey Tutor database is a SQLAlchemy-based relational database that stores user data, conversations, and cache information. The database is designed to be flexible and extensible, allowing for easy addition of new features and data types.

## Database Structure

The database is organized into the following main components:

1. **Models**: Define the database schema and relationships between tables.
2. **Repositories**: Provide an interface for interacting with the database models.
3. **API**: Provides a high-level API for interacting with the database.
4. **Admin**: Provides a command-line interface for managing the database.

### Models

The database models are defined in the `database/models` directory:

- `user.py`: User-related models (User, UserProfile, UserSession)
- `conversation.py`: Conversation-related models (Conversation, ConversationParameters, Message, Question, Answer)
- `cache.py`: Cache-related models (Cache, QuestionCache, AssessmentCache)

### Repositories

The database repositories are defined in the `database/repositories` directory:

- `user.py`: User-related repositories (UserRepository, UserProfileRepository, UserSessionRepository)
- `conversation.py`: Conversation-related repositories (ConversationRepository, MessageRepository, QuestionRepository, AnswerRepository)
- `cache.py`: Cache-related repositories (CacheRepository, QuestionCacheRepository, AssessmentCacheRepository)

### API

The database API is defined in `database/api.py` and provides a high-level interface for interacting with the database. The API is designed to be easy to use and provides methods for common operations such as creating users, retrieving conversations, and managing cache entries.

### Admin

The database admin is defined in `database/admin.py` and provides a command-line interface for managing the database. The admin tool can be used to list users, create users, view conversations, and perform other administrative tasks.

## Setup

To set up the database, run the `setup_database.sh` script:

```bash
./setup_database.sh
```

This script will:

1. Install required packages
2. Initialize the database
3. Import data from existing files

## Migration

To migrate data from the old file-based storage to the new database, run the `setup_database.sh` script as described above. This will import all existing data into the database.

After verifying that the database is working correctly, you can move the original files to a legacy folder using the `move_to_legacy.sh` script:

```bash
./move_to_legacy.sh
```

This script will copy all original files to a `legacy` directory, allowing you to safely delete the original files once you're confident that the database is working correctly.

## Usage

### Database API

The database API can be used to interact with the database programmatically:

```python
from database.api import DatabaseAPI

# Create a database API instance
api = DatabaseAPI()

# Get a user by username
user = api.get_user_by_username("test_user")

# Get user conversations
conversations = api.get_user_conversations(user["id"])

# Close the database connection
api.close()
```

You can also use the API as a context manager:

```python
from database.api import DatabaseAPI

with DatabaseAPI() as api:
    # Get a user by username
    user = api.get_user_by_username("test_user")
    
    # Get user conversations
    conversations = api.get_user_conversations(user["id"])
```

### Database Admin

The database admin tool can be used to manage the database from the command line:

```bash
# List all users
python -m database.admin list-users

# Get a user by username
python -m database.admin get-user --username test_user

# Create a new user
python -m database.admin create-user --username new_user --name "New User" --email "new.user@example.com"

# List conversations for a user
python -m database.admin list-conversations --username test_user

# Get a conversation by ID
python -m database.admin get-conversation --id <conversation_id> --messages

# Initialize the database and import all data
python -m database.admin init-db --import-all

# Reset the database (warning: this will delete all data)
python -m database.admin reset-db
```

### KG Quizzing Database Adapter

The KG Quizzing module can use the database through the `DatabaseAdapter` class defined in `kg_quizzing/scripts/database_adapter.py`:

```python
from kg_quizzing.scripts.database_adapter import DatabaseAdapter

# Create a database adapter instance
adapter = DatabaseAdapter()

# Get a user by username
user = adapter.get_user("test_user")

# Create a session
session = adapter.create_session("test_user", session_type="quiz")

# Create a conversation
conversation = adapter.create_conversation("test_user", session["id"], conversation_type="quiz")

# Add a message to the conversation
message = adapter.add_message(conversation["id"], "user", "Hello, world!")

# Close the database connection
adapter.close()
```

You can also use the adapter as a context manager:

```python
from kg_quizzing.scripts.database_adapter import DatabaseAdapter

with DatabaseAdapter() as adapter:
    # Get a user by username
    user = adapter.get_user("test_user")
    
    # Create a session
    session = adapter.create_session("test_user", session_type="quiz")
    
    # Create a conversation
    conversation = adapter.create_conversation("test_user", session["id"], conversation_type="quiz")
    
    # Add a message to the conversation
    message = adapter.add_message(conversation["id"], "user", "Hello, world!")
```

## Database Schema

### User Models

- **User**: Represents a user of the system.
  - `id`: UUID primary key
  - `username`: Username (unique)
  - `email`: Email address
  - `name`: Full name
  - `role`: User role (user, admin, etc.)
  - `created_at`: Creation timestamp
  - `last_login`: Last login timestamp

- **UserProfile**: Represents a user's profile information.
  - `id`: UUID primary key
  - `user_id`: Foreign key to User
  - `community_mastery`: Community mastery data (JSON)
  - `entity_familiarity`: Entity familiarity data (JSON)
  - `question_type_performance`: Question type performance data (JSON)
  - `difficulty_performance`: Difficulty performance data (JSON)
  - `overall_mastery`: Overall mastery score
  - `mastered_objectives`: Mastered objectives (JSON array)
  - `current_objective`: Current objective
  - `last_updated`: Last update timestamp

- **UserSession**: Represents a user session.
  - `id`: UUID primary key
  - `user_id`: Foreign key to User
  - `session_type`: Session type (chat, quiz, etc.)
  - `start_time`: Start timestamp
  - `end_time`: End timestamp
  - `questions_asked`: Number of questions asked
  - `correct_answers`: Number of correct answers
  - `accuracy`: Accuracy score
  - `mastery_before`: Mastery score before session
  - `mastery_after`: Mastery score after session
  - `strategy`: Session strategy
  - `theme`: Session theme
  - `fussiness`: Session fussiness
  - `tier`: Session tier
  - `use_llm`: Whether to use LLM
  - `parameters`: Session parameters (JSON)

### Conversation Models

- **Conversation**: Represents a conversation.
  - `id`: UUID primary key
  - `user_id`: Foreign key to User
  - `session_id`: Foreign key to UserSession
  - `conversation_type`: Conversation type (chat, quiz, etc.)
  - `quiz_id`: Quiz ID
  - `start_time`: Start timestamp
  - `end_time`: End timestamp
  - `duration_seconds`: Duration in seconds
  - `meta_data`: Metadata (JSON)

- **ConversationParameters**: Represents conversation parameters.
  - `id`: UUID primary key
  - `conversation_id`: Foreign key to Conversation
  - `strategy`: Conversation strategy
  - `theme`: Conversation theme
  - `fussiness`: Conversation fussiness
  - `tier`: Conversation tier
  - `use_llm`: Whether to use LLM
  - `parameters`: Conversation parameters (JSON)

- **Message**: Represents a message in a conversation.
  - `id`: UUID primary key
  - `conversation_id`: Foreign key to Conversation
  - `role`: Message role (user, assistant, etc.)
  - `content`: Message content
  - `timestamp`: Timestamp
  - `meta_data`: Metadata (JSON)

- **Question**: Represents a question in a conversation.
  - `id`: UUID primary key
  - `message_id`: Foreign key to Message
  - `type`: Question type (multiple_choice, open_ended, etc.)
  - `difficulty`: Question difficulty (easy, medium, hard, etc.)
  - `entity`: Question entity
  - `tier`: Question tier
  - `options`: Question options (JSON array)
  - `correct_answer`: Correct answer
  - `community_id`: Community ID
  - `meta_data`: Metadata (JSON)

- **Answer**: Represents an answer to a question.
  - `id`: UUID primary key
  - `message_id`: Foreign key to Message
  - `question_id`: Foreign key to Question
  - `content`: Answer content
  - `correct`: Whether the answer is correct
  - `quality_score`: Answer quality score
  - `feedback`: Feedback on the answer

### Cache Models

- **Cache**: Represents a generic cache entry.
  - `id`: UUID primary key
  - `cache_type`: Cache type
  - `key`: Cache key
  - `value`: Cache value (JSON)
  - `created_at`: Creation timestamp
  - `last_accessed`: Last access timestamp
  - `access_count`: Access count

- **QuestionCache**: Represents a question cache entry.
  - `id`: UUID primary key
  - `question_id`: Question ID
  - `question_text`: Question text
  - `question_type`: Question type
  - `difficulty`: Question difficulty
  - `entity`: Question entity
  - `tier`: Question tier
  - `options`: Question options (JSON array)
  - `correct_answer`: Correct answer
  - `community_id`: Community ID
  - `meta_data`: Metadata (JSON)
  - `created_at`: Creation timestamp
  - `last_accessed`: Last access timestamp
  - `access_count`: Access count

- **AssessmentCache**: Represents an assessment cache entry.
  - `id`: UUID primary key
  - `assessment_id`: Assessment ID
  - `user_id`: User ID
  - `assessment_type`: Assessment type
  - `questions`: Questions (JSON array)
  - `answers`: Answers (JSON array)
  - `score`: Score
  - `max_score`: Maximum score
  - `created_at`: Creation timestamp
  - `last_accessed`: Last access timestamp
  - `access_count`: Access count
