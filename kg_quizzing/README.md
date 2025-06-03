# Adaptive Quizzing System

This module implements an adaptive quizzing system leveraging the Neo4j GraphRAG knowledge graph. The system generates questions based on the knowledge graph content, adapts to student performance, and provides personalized learning experiences.

## Architecture

The adaptive quizzing system consists of the following components:

1. **Schema Extension** - Extends the Neo4j schema with educational metadata
2. **Question Generation** - Generates different types of questions based on the knowledge graph
3. **Adaptive Strategy Engine** - Selects appropriate questions based on student performance
4. **LLM Assessment Service** - Evaluates open-ended student answers
5. **Quiz Orchestrator** - Manages the quiz session and user interaction

## Directory Structure

```
kg_quizzing/
├── scripts/
│   ├── quiz_utils.py           # Utility functions for the quizzing system
│   ├── schema_extension.py     # Schema extension for educational metadata
│   ├── question_generation.py  # Question generation engine
│   ├── adaptive_strategy.py    # Adaptive strategy engine
│   ├── llm_assessment.py       # LLM-based assessment service
│   └── quiz_orchestrator.py    # Quiz session orchestrator
└── README.md                   # This file
```

## Setup

1. Ensure Neo4j is running and accessible
2. Set up the required environment variables in `.env`:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   OPENAI_API_KEY=your_openai_api_key
   LLM_MODEL=gpt-4
   ```
3. Run the schema extension script to set up the educational metadata:
   ```
   python kg_quizzing/scripts/quiz_orchestrator.py --setup
   ```

## Usage

### Starting a Quiz Session

```bash
python kg_quizzing/scripts/quiz_orchestrator.py --student student_id --name "Student Name" --strategy adaptive
```

Available strategies:
- `adaptive` - Questions are selected based on student performance and learning objectives
- `depth_first` - Focus on mastering one topic at a time
- `breadth_first` - Cover a broad range of topics
- `spiral` - Periodically return to previously covered topics

### Testing Question Generation

```bash
python kg_quizzing/scripts/question_generation.py --type factual --difficulty 5 --community 1
```

Available question types:
- `factual` - Basic factual questions about entities
- `relationship` - Questions about relationships between entities
- `multiple_choice` - Multiple-choice questions
- `synthesis` - Questions requiring synthesis of information
- `application` - Questions requiring application of knowledge

### Testing the Adaptive Strategy Engine

```bash
python kg_quizzing/scripts/adaptive_strategy.py --student student_id --name "Student Name" --strategy adaptive
```

### Testing LLM Assessment

```bash
python kg_quizzing/scripts/llm_assessment.py --question "What are the implications of the War of the Ring?" --answer "The War of the Ring led to the defeat of Sauron and the restoration of the kingdom of Gondor." --type synthesis --difficulty 7
```

## Components

### Quiz Utils (`quiz_utils.py`)

Provides utility functions for:
- Neo4j connection management
- Query execution
- Educational metadata checks
- Community and entity retrieval
- Difficulty scoring

### Schema Extension (`schema_extension.py`)

Extends the Neo4j schema with:
- Question templates
- Learning objectives
- Difficulty progression paths
- Community bridges

### Question Generation (`question_generation.py`)

Implements a modular question generation system with:
- Factual questions
- Relationship questions
- Multiple-choice questions
- Synthesis questions
- Application questions

### Adaptive Strategy Engine (`adaptive_strategy.py`)

Manages the adaptive quizzing process:
- Student model tracking
- Question selection strategies
- Performance evaluation
- Learning objective progression

### LLM Assessment Service (`llm_assessment.py`)

Provides LLM-based assessment of student answers:
- Evaluation of open-ended responses
- Quality scoring
- Detailed feedback generation
- Caching for performance optimization

### Quiz Orchestrator (`quiz_orchestrator.py`)

Orchestrates the quiz session:
- User interaction
- Session management
- Progress tracking
- Feedback delivery

## Student Model

The system maintains a student model that tracks:
- Community mastery levels
- Entity familiarity
- Question type performance
- Difficulty level performance
- Learning objective progress
- Overall mastery level

This model is used to adapt the quiz experience to the student's needs and performance.

## Future Enhancements

1. Web-based user interface
2. Multi-user support with authentication
3. Enhanced visualization of student progress
4. Integration with external learning management systems
5. Expanded question types and templates
6. Improved LLM assessment with fine-tuned models
