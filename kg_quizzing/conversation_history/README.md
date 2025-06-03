# Conversation History Module

This module provides a comprehensive solution for storing, retrieving, and exporting conversation history in the adaptive quizzing system. It's designed to be modular, maintainable, and easily integrated with the existing codebase.

## Module Structure

The conversation history module is organized into the following directories:

```
conversation_history/
├── __init__.py             # Package initializer
├── core/                   # Core components
│   ├── __init__.py         # Core package initializer
│   ├── message.py          # ConversationMessage class
│   ├── conversation.py     # QuizConversation class
│   └── manager.py          # ConversationHistoryManager class
├── exporters/              # Export functionality
│   ├── __init__.py         # Exporters package initializer
│   └── exporter.py         # ConversationExporter class
├── api/                    # API components
│   ├── __init__.py         # API package initializer
│   ├── router.py           # FastAPI router for conversation history
│   └── server.py           # Standalone API server for testing
├── utils/                  # Utility functions
│   ├── __init__.py         # Utils package initializer
│   └── cli.py              # CLI utilities for conversation history
└── README.md               # This documentation file
```

## Core Components

### ConversationMessage

Represents a single message in a conversation, with the following attributes:
- `role`: The sender's role (system, user, assistant)
- `content`: The message content
- `timestamp`: When the message was sent
- `metadata`: Additional information about the message

### QuizConversation

Represents a complete quiz conversation session, with the following attributes:
- `conversation_id`: Unique identifier for the conversation
- `student_id`: Identifier for the student
- `quiz_id`: Identifier for the quiz
- `metadata`: Additional information about the conversation
- `messages`: List of ConversationMessage objects
- `start_time`: When the conversation started
- `end_time`: When the conversation ended

### ConversationHistoryManager

Manages the storage and retrieval of conversation history, with the following functionality:
- Save conversations to JSON files
- Load conversations from JSON files
- Get conversations for a specific student
- Get all conversations
- Delete conversations

## Exporters

### ConversationExporter

Provides functionality to export conversations in different formats:
- JSON: Full conversation data with metadata
- Text: Human-readable format with timestamps and roles
- CSV: Tabular format for analysis

## API Components

### FastAPI Router

Provides RESTful API endpoints for conversation history:
- `POST /api/conversations`: Create a new conversation
- `GET /api/conversations`: List all conversations
- `GET /api/conversations/{conversation_id}`: Get a specific conversation
- `POST /api/conversations/{conversation_id}/messages`: Add a message to a conversation
- `POST /api/conversations/{conversation_id}/export`: Export a conversation
- `DELETE /api/conversations/{conversation_id}`: Delete a conversation

### Standalone API Server

A standalone FastAPI server for testing the conversation history API.

## Utility Functions

### CLI Utilities

Command-line utilities for working with conversation history:
- Export conversation history for a student in different formats

## Usage Examples

### Creating and Saving a Conversation

```python
from conversation_history.core import QuizConversation, ConversationHistoryManager

# Create a new conversation
conversation = QuizConversation(
    student_id="student123",
    quiz_id="quiz456",
    metadata={"strategy": "adaptive"}
)

# Add messages to the conversation
conversation.add_system_message("Welcome to the quiz!")
conversation.add_assistant_message("Here's your first question...")
conversation.add_user_message("My answer is...")

# End the conversation
conversation.end_conversation()

# Save the conversation
manager = ConversationHistoryManager()
file_path = manager.save_conversation(conversation)
print(f"Conversation saved to {file_path}")
```

### Exporting Conversation History

```python
from conversation_history.core import ConversationHistoryManager
from conversation_history.exporters import ConversationExporter

# Load a conversation
manager = ConversationHistoryManager()
conversation_files = manager.get_conversations_for_student("student123")
conversation = manager.load_conversation(conversation_files[0])

# Export the conversation
exporter = ConversationExporter()
exporter.export_to_text(conversation, "conversation.txt")
exporter.export_to_json(conversation, "conversation.json")
exporter.export_to_csv(conversation, "conversation.csv")
```

### Using the API

```python
import requests

# Create a new conversation
response = requests.post("http://localhost:8000/api/conversations", json={
    "student_id": "student123",
    "quiz_id": "quiz456",
    "metadata": {
        "strategy": "adaptive"
    }
})
conversation_id = response.json()["conversation_id"]

# Add a message to the conversation
requests.post(f"http://localhost:8000/api/conversations/{conversation_id}/messages", json={
    "role": "assistant",
    "content": "Here's your question...",
    "metadata": {
        "is_question": True
    }
})

# Get the conversation
conversation = requests.get(f"http://localhost:8000/api/conversations/{conversation_id}").json()

# Export the conversation
export = requests.post(f"http://localhost:8000/api/conversations/{conversation_id}/export", json={
    "format": "text"
}).json()
```

## Integration with Quiz Orchestrator

The conversation history module is integrated with the quiz orchestrator to automatically record quiz interactions:

1. The quiz orchestrator creates a new conversation at the start of a quiz session
2. Questions, answers, feedback, and summaries are recorded as messages
3. The conversation is saved at the end of the quiz session

## Storage Format

Conversations are stored as JSON files in the following directory structure:

```
conversation_history/data/
├── student123/                           # Student ID
│   ├── conversation_abc_20250601_123456.json  # Conversation ID and timestamp
│   └── conversation_def_20250602_123456.json
└── student456/
    └── conversation_ghi_20250603_123456.json
```

## Future Plans

- Integration with the main backend API
- Frontend components for viewing and managing conversation history
- Analytics for conversation data
- Search functionality for conversations
- Real-time updates via WebSockets

## Running the Standalone API Server

To run the standalone API server for testing:

```bash
python -m conversation_history.api.server
```

The API will be available at http://localhost:8000.

## Using the CLI

To export conversation history for a student:

```bash
python -m conversation_history.utils.cli export student123 --format text
```

This will export all conversations for the student in text format.
