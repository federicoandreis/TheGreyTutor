# Optimized PathRAG Retriever with LLM Integration

This directory contains the optimized PathRAG retriever implementation with LLM integration for the Tolkien knowledge graph project. The PathRAG retriever has been tuned with optimal parameters based on extensive testing to provide balanced coverage and performance.

## Features

- **Optimized PathRAG Parameters**: 
  - `max_communities=5`: Optimal number of communities to retrieve
  - `max_path_length=3`: Optimal maximum path length in hops
  - `max_paths_per_entity=5`: Optimal number of paths per entity pair

- **LLM Integration**

The PathRAG retriever is integrated with OpenAI's LLM API for answer synthesis. The integration:

- Uses the latest OpenAI Python SDK (v1.0.0+)
- Requires an OpenAI API key via environment variable
- Includes caching to avoid redundant API calls
- Features a comprehensive, structured prompt system for high-quality answers
- Implements Gandalf the Grey impersonation for authentic Tolkien-esque responses

- **Flexible Configuration**:
  - Command-line options for parameter tuning
  - Output file writing for result persistence
  - Verbose mode for debugging and analysis

## Requirements

```
neo4j==5.14.0
openai==1.12.0
python-dotenv==1.0.0
tqdm==4.66.1
numpy==1.24.3
```

## Gandalf Impersonation Feature

The PathRAG retriever now includes a sophisticated Gandalf the Grey impersonation feature that transforms the LLM's responses into the authentic voice of Tolkien's iconic wizard:

- **Character Voice**: Responses are delivered in Gandalf's distinctive speaking style from the books, including his characteristic phrases, metaphors, and philosophical observations.

- **Personalized Knowledge**: The system prompt positions the LLM as Gandalf himself, with personal knowledge of Middle-earth's history, peoples, and lore gained through thousands of years of experience.

- **Narrative Approach**: Rather than clinical information delivery, the LLM presents knowledge graph data as if recounting personal experiences and observations from Gandalf's long life.

- **Authentic Speech Patterns**: Includes Gandalf's thoughtful pauses, rhetorical questions, occasional archaic language, and wisdom-sharing that goes beyond the immediate question.

- **Structured Response Format**: Answers begin with direct wisdom in Gandalf's voice, elaborate with details from the knowledge graph as if from personal experience, and conclude with a philosophical reflection related to the question.

This feature significantly enhances the user experience by providing not just factually accurate information from the knowledge graph, but delivering it in an immersive, character-authentic manner that brings the Tolkien universe to life.

## Environment Setup

1. Create a `.env` file in the scripts directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
python run_pathrag.py "What is the relationship between Frodo and the Ring of Power?"
```

### Advanced Usage

```bash
python run_pathrag.py "What is the relationship between Frodo and the Ring of Power?" \
  --verbose \
  --no-cache \
  --output-file results.json \
  --max-communities 7 \
  --max-path-length 4 \
  --max-paths-per-entity 6
```

### Example

```bash
# Run with default parameters (includes Gandalf impersonation)
python run_pathrag.py "What is the relationship between Frodo and the Ring of Power?"

# Run with verbose output to see the detailed prompt
python run_pathrag.py "Who is Aragorn?" --verbose

# Run with custom parameters
python run_pathrag.py "Tell me about the Shire" --max-communities 3 --max-path-length 2 --no-cache
```

#### Example Gandalf-Style Response

For the query "What is the relationship between Frodo and the Ring of Power?", the system might respond:

```
Ah, my dear friend, you ask about a bond most perilous and profound. Frodo Baggins became the Ring-bearer, a burden he did not seek but accepted with remarkable courage. The One Ring, forged by Sauron in the fires of Mount Doom, sought always to return to its master's hand.

I first observed this fateful connection when Bilbo passed the Ring to Frodo at Bag End. Though Bilbo possessed it for sixty years, it was Frodo who carried it through the greatest perils to its destruction. The Ring exerted a terrible influence on its bearer - a constant temptation, a growing weight upon the spirit. It preserved him from aging, yes, but at the cost of slowly consuming his very self.

The path between them is clear in the knowledge of our world - Frodo inherited the Ring from Bilbo, who found it in Gollum's cave. The Ring sought to corrupt Frodo as it had corrupted others before him, yet his exceptional resilience allowed him to carry it further than any might have hoped, even to the Cracks of Doom where its power was finally unmade.

Remember this, for it is no small truth: it was not strength of arms but strength of heart that allowed Frodo to bear this burden. Even the smallest person can change the course of the future, when they carry both great burdens and great courage.
```

This response demonstrates how the Gandalf impersonation feature transforms factual information from the knowledge graph into an immersive, character-authentic narrative that brings the Tolkien universe to life.

### Command-line Options

- `query`: The question to answer (required)
- `--verbose`: Show verbose output including the full LLM prompt
- `--no-cache`: Disable caching for retrieval and LLM calls
- `--output-file`: File to write results to (JSON format)
- `--max-communities`: Maximum number of communities to retrieve (default: 5)
- `--max-path-length`: Maximum path length in hops (default: 3)
- `--max-paths-per-entity`: Maximum paths per entity pair (default: 5)

## Testing

The test files have been organized into a dedicated `tests` directory for better code organization. To run comprehensive tests on the PathRAG retriever:

```bash
python tests/test_pathrag_suite.py --strategy pathrag --verbose
```

Other available test scripts in the `tests` directory:

```bash
# Test the improved prompt formatting
python tests/test_improved_prompt.py "What is the relationship between Frodo and the Ring of Power?"

# Test basic PathRAG functionality
python tests/test_pathrag.py "Who is Aragorn?"

# Test the original retriever implementation
python tests/test_retriever.py
```

**Note**: The demo scripts (`demo_optimized_pathrag.py` and `pathrag_demo.py`) have been moved to the `old` directory as they have been superseded by the more comprehensive `run_pathrag.py` implementation.

## Implementation Details

The optimized PathRAG retriever is implemented in the `GraphRAGRetriever` class with the following key components:

1. **Entity Extraction**: Identifies entities in the query using capitalization and multi-word detection
2. **Community Detection**: Finds relevant communities containing the extracted entities
3. **Path Finding**: Discovers paths between entities using Neo4j graph traversal
4. **Result Aggregation**: Combines nodes, paths, and metadata into a comprehensive result
5. **LLM Integration**: Formats the retrieval results into a prompt for the LLM and processes the response

The LLM integration follows the project's existing patterns, using the OpenAI client interface with a system prompt and user prompt for consistent and high-quality answers.

## Performance

The optimized PathRAG retriever achieves a balance between coverage and performance:

- Average retrieval time: ~0.15s per query
- Average result count: 10-20 items per query
- 100% success rate on test suite with 25 diverse queries

## Next Steps

1. **Enhanced Prompt Engineering**: Further refine prompts for better LLM answer quality
2. **Hybrid Retrieval**: Integrate PathRAG with other retrieval strategies for more comprehensive results
3. **Performance Monitoring**: Monitor retrieval and LLM call latencies in production
4. **Expanded Testing**: Automate comprehensive tests with larger query sets and edge cases
