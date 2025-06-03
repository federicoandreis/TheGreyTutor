# Conversation History Module for Adaptive Quizzing

This document describes the conversation history module for the adaptive quizzing system, which enables storing and retrieving quiz conversations for later inspection.

## Overview

The conversation history module provides a structured way to record all interactions during a quiz session, including:

- Questions presented to the student
- Student answers
- Feedback provided to the student
- Session statistics and summaries

This data is stored in a structured format that can be easily retrieved, analyzed, and exported in various formats (JSON, text, CSV).

## Key Components

### 1. `ConversationMessage`

Represents a single message in a conversation with the following attributes:
- `role`: The sender of the message (system, user/student, assistant/quiz)
- `content`: The actual message content
- `timestamp`: When the message was sent
- `metadata`: Additional information about the message (e.g., question difficulty, correctness of answer)

### 2. `QuizConversation`

Represents a complete quiz session conversation with the following attributes:
- `conversation_id`: Unique identifier for the conversation
- `student_id`: Identifier for the student
- `quiz_id`: Identifier for the quiz
- `messages`: List of `ConversationMessage` objects
- `start_time` and `end_time`: Timestamps for the session
- `metadata`: Additional information about the session

Methods for adding different types of messages:
- `add_message()`: Generic method for adding any message
- `add_system_message()`: Add a system message
- `add_user_message()`: Add a student message
- `add_assistant_message()`: Add a quiz system message
- `add_question()`: Add a question with metadata
- `add_answer()`: Add a student answer with correctness information
- `add_feedback()`: Add feedback on an answer

### 3. `ConversationHistoryManager`

Manages storing and retrieving conversation histories:
- `save_conversation()`: Save a conversation to a JSON file
- `load_conversation()`: Load a conversation from a JSON file
- `get_conversations_for_student()`: Get all conversations for a specific student
- `get_all_conversations()`: Get all conversations
- `delete_conversation()`: Delete a conversation file

### 4. `ConversationExporter`

Exports conversations in different formats:
- `export_to_json()`: Export as JSON
- `export_to_text()`: Export as human-readable text
- `export_to_csv()`: Export as CSV for data analysis

## Integration with Quiz Orchestrator

The conversation history module is integrated with the `QuizOrchestrator` and `QuizSession` classes:

1. Each `QuizSession` initializes a new `QuizConversation` object
2. Quiz interactions are automatically recorded:
   - System messages (welcome, instructions)
   - Questions presented to the student
   - Student answers
   - Feedback provided
   - Session summary

3. At the end of a session, the conversation is saved to disk

## Usage

### Recording Quiz Conversations

The recording happens automatically during quiz sessions. No additional code is required as the `QuizSession` class handles this internally.

### Exporting Conversation History

Use the command-line interface to export conversation history:

```bash
# Export conversation history for a student in text format (default)
python quiz_orchestrator.py --export student123 --export-format text

# Export in JSON format
python quiz_orchestrator.py --export student123 --export-format json

# Export in CSV format
python quiz_orchestrator.py --export student123 --export-format csv

# Specify a custom conversation directory
python quiz_orchestrator.py --export student123 --conversation-dir custom_dir
```

### Programmatic Access

```python
# Initialize the conversation history manager
manager = ConversationHistoryManager("conversation_history")

# Get all conversations for a student
conversation_files = manager.get_conversations_for_student("student123")

# Load a conversation
conversation = manager.load_conversation(conversation_files[0])

# Export a conversation
exporter = ConversationExporter()
exporter.export_to_text(conversation, "conversation.txt")
```

## Storage Format

Conversations are stored as JSON files with the following structure:
- Files are organized by student ID
- Each file contains a complete conversation with all messages and metadata
- Filenames include conversation ID and timestamp for easy identification

## Future Enhancements

1. **Backend API Integration**: Create a dedicated backend API for storing and retrieving conversations
2. **Frontend Visualization**: Develop a frontend interface for browsing and analyzing conversation history
3. **Analytics**: Add analytics capabilities to extract insights from conversation history
4. **Search**: Implement search functionality to find specific conversations or messages
5. **Filtering**: Add filtering options based on various criteria (date, correctness, topics)

## Notes

- The conversation history module is designed to be standalone and does not require immediate integration with existing frontend or backend systems
- When integration is desired, the module provides a clean API that can be easily connected to other components
- All data is stored locally in JSON files, making it easy to inspect and process
