# Knowledge Graph Queries (kg_queries)

This directory contains the implementation of query systems for the Neo4j knowledge graph used in the Grey Tutor project.

## Directory Structure

The codebase has been organized as follows:

### Main Components

- **`scripts/`**: Contains the newer, more streamlined GraphRAG implementation
  - `graphrag_retriever.py` - Main retriever implementation with all strategies
  - `run_pathrag.py` - Optimized PathRAG runner with LLM integration (Gandalf impersonation)
  - `cache_manager.py` - Caching system implementation
  - `kg_query_utils.py` - Shared utility functions for Neo4j connection management
  - `tests/` - Dedicated directory for test scripts (moved for better organization)
  - `old/` - Archive of older implementations and deprecated scripts

### Query Scripts

- **Global Search**: Search across all nodes with filtering, sorting, and pagination
- **Local Search**: Search within a specific subgraph starting from a node
- **Relationship Search**: Find and analyze relationships between nodes
- **PathRAG**: Path-based retrieval augmented generation

## Key Features

- **Multiple Retrieval Strategies**:
  - Entity-centric retrieval
  - Relationship-aware retrieval
  - Hybrid retrieval
  - Path-based retrieval with community detection

- **LLM Integration**:
  - OpenAI API integration
  - Structured prompts for high-quality answers
  - Gandalf the Grey impersonation for Tolkien-esque responses

- **Performance Optimizations**:
  - Caching for both retrieval results and LLM responses
  - Optimized query parameters based on extensive testing
  - Efficient Neo4j query patterns

## Getting Started

See the README files in the respective subdirectories for detailed usage instructions:

- [PathRAG README](scripts/README_PATHRAG.md) - For the optimized PathRAG implementation
- [Tests README](scripts/tests/README.md) - For information about the test suite

## Recent Updates

- Test scripts have been moved to a dedicated `tests` directory for better organization
- Demo scripts have been moved to the `old` directory as they've been superseded by `run_pathrag.py`
- The system prompt for Gandalf impersonation has been updated to ensure responses stay within the Tolkien universe
