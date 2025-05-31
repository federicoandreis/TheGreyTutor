# GraphRAG Scripts (Deprecated)

**IMPORTANT: The files in this directory represent an older version of the GraphRAG implementation and have been superseded by the newer implementation in the parent directory.**

This directory contains an earlier version of the GraphRAG (Graph Retrieval Augmented Generation) implementation for Neo4j knowledge graphs. The scripts provide multiple retrieval strategies, caching, and a clean API for integrating graph-based retrieval into applications.

## Overview

The GraphRAG system implements several retrieval strategies inspired by research papers and best practices:

- **Entity-Centric Retrieval**: Focuses on finding specific entities mentioned in queries
- **Relationship-Aware Retrieval**: Explores connections and paths between entities
- **Hybrid Retrieval**: Combines multiple strategies for comprehensive results
- **Caching**: File-based caching system to improve performance
- **Modular Design**: Clean separation of concerns with Pydantic models

## Files

### Core Components

- **`graphrag_retriever.py`** - Main retriever implementation with all strategies
- **`models.py`** - Pydantic data models for type safety
- **`config.py`** - Configuration management
- **`cache_manager.py`** - Caching system implementation
- **`neo4j_client.py`** - Neo4j database client wrapper
- **`retrieval_strategies.py`** - Individual strategy implementations

### Testing and Examples

- **`test_retriever.py`** - Test suite for validating functionality
- **`example_usage.py`** - Comprehensive usage examples
- **`__init__.py`** - Package initialization

## Quick Start

### Basic Usage

```python
from graphrag_retriever import GraphRAGRetriever

# Initialize retriever
retriever = GraphRAGRetriever()

# Ask a question
result = retriever.retrieve("Who is Frodo?", strategy="hybrid")

# Print results
retriever.print_result(result)
```

### Command Line Usage

```bash
# Basic query
python graphrag_retriever.py "Who is Frodo?" --strategy entity

# Relationship query
python graphrag_retriever.py "How is Frodo related to Bilbo?" --strategy relationship

# Comprehensive search
python graphrag_retriever.py "Tell me about the One Ring" --strategy hybrid --max-results 15

# JSON output
python graphrag_retriever.py "What is Mordor?" --output json
```

## Retrieval Strategies

### Entity-Centric Strategy

Best for queries about specific entities:
- "Who is Gandalf?"
- "What is the One Ring?"
- "Tell me about Mordor"

**How it works:**
1. Extracts entity names from the query (capitalized words)
2. Searches for nodes containing those entity names
3. Returns matching nodes with their properties

### Relationship-Aware Strategy

Best for queries about connections:
- "How is Frodo related to Bilbo?"
- "What is the connection between Gandalf and Saruman?"
- "How are the hobbits connected?"

**How it works:**
1. Extracts entities from the query
2. Finds paths between entity pairs using shortest path algorithms
3. For single entities, finds all directly connected nodes
4. Returns paths, relationships, and connected nodes

### Hybrid Strategy

Best for comprehensive queries:
- "Tell me about the Fellowship of the Ring"
- "What happened to the One Ring?"
- "Describe the relationship between hobbits and the Shire"

**How it works:**
1. Combines entity-centric and relationship-aware strategies
2. Merges results and removes duplicates
3. Provides the most comprehensive information

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Configuration Options

```python
from config import GraphRAGConfig

config = GraphRAGConfig(
    max_results=20,
    cache_enabled=True,
    cache_ttl=3600,  # 1 hour
    neo4j_timeout=30
)

retriever = GraphRAGRetriever(config=config)
```

## Caching

The system includes a file-based caching mechanism:

- **Automatic**: Results are cached automatically based on query + strategy + parameters
- **Performance**: Significantly improves response times for repeated queries
- **Storage**: Cache files are stored in the `cache/` directory
- **TTL**: Configurable time-to-live for cache entries

### Cache Management

```python
# Disable caching
retriever = GraphRAGRetriever(use_cache=False)

# Clear cache programmatically
retriever.cache.clear()

# Manual cache operations
cache_key = retriever.cache._get_cache_key(query, strategy, params)
cached_result = retriever.cache.get(query, strategy, params)
```

## Testing

### Run Tests

```bash
# Run the test suite
python test_retriever.py

# Run examples
python example_usage.py
```

### Test Coverage

The test suite covers:
- Basic functionality of all strategies
- Caching behavior
- Output formats
- Error handling
- Performance benchmarks

## API Reference

### GraphRAGRetriever

Main class for graph retrieval operations.

```python
class GraphRAGRetriever:
    def __init__(self, use_cache: bool = True, config: Optional[GraphRAGConfig] = None)
    def retrieve(self, query: str, strategy: str = "hybrid", max_results: int = 10) -> RetrievalResult
    def print_result(self, result: RetrievalResult, verbose: bool = False)
```

### RetrievalResult

Data class containing retrieval results.

```python
@dataclass
class RetrievalResult:
    strategy: str
    query: str
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    paths: List[Dict[str, Any]]
    execution_time: float
    total_results: int
    metadata: Dict[str, Any]
```

## Performance Considerations

### Optimization Tips

1. **Use Caching**: Enable caching for production use
2. **Limit Results**: Use appropriate `max_results` values
3. **Choose Strategy**: Select the most appropriate strategy for your query type
4. **Index Properties**: Ensure your Neo4j database has proper indexes on searchable properties

### Benchmarks

Typical performance on a standard Neo4j instance:
- Entity queries: 50-200ms
- Relationship queries: 100-500ms
- Hybrid queries: 200-800ms
- Cached queries: 1-5ms

## Integration Examples

### Flask API

```python
from flask import Flask, request, jsonify
from graphrag_retriever import GraphRAGRetriever

app = Flask(__name__)
retriever = GraphRAGRetriever()

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    result = retriever.retrieve(
        query=data['query'],
        strategy=data.get('strategy', 'hybrid'),
        max_results=data.get('max_results', 10)
    )
    return jsonify(asdict(result))
```

### Streamlit App

```python
import streamlit as st
from graphrag_retriever import GraphRAGRetriever

st.title("Knowledge Graph Q&A")

retriever = GraphRAGRetriever()

query = st.text_input("Ask a question:")
strategy = st.selectbox("Strategy:", ["hybrid", "entity", "relationship"])

if query:
    result = retriever.retrieve(query, strategy=strategy)
    
    st.write(f"Found {result.total_results} results in {result.execution_time:.3f}s")
    
    for node in result.nodes:
        st.write(f"**{node['properties'].get('name', 'Unknown')}**")
        st.write(node['properties'].get('description', 'No description'))
```

## Best Practices

### Query Design

1. **Be Specific**: Use proper nouns and specific terms
2. **Natural Language**: Write queries as natural questions
3. **Entity Focus**: Include entity names when possible
4. **Relationship Words**: Use words like "related", "connected", "between" for relationship queries

### Error Handling

```python
try:
    result = retriever.retrieve(query, strategy="hybrid")
    if result.total_results == 0:
        print("No results found. Try a different query or strategy.")
    else:
        retriever.print_result(result)
except Exception as e:
    print(f"Query failed: {str(e)}")
```

### Production Deployment

1. **Environment Variables**: Use environment variables for configuration
2. **Logging**: Enable appropriate logging levels
3. **Monitoring**: Monitor query performance and cache hit rates
4. **Scaling**: Consider connection pooling for high-traffic applications

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check Neo4j connection parameters in `.env`
2. **No Results**: Verify data exists in the graph and try different strategies
3. **Slow Queries**: Enable caching and consider adding database indexes
4. **Memory Issues**: Reduce `max_results` for large datasets

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed query execution information
result = retriever.retrieve(query, strategy="hybrid")
```

## Contributing

When adding new features:

1. **Follow Patterns**: Use existing patterns for consistency
2. **Add Tests**: Include tests for new functionality
3. **Update Docs**: Update this README and add docstrings
4. **Type Safety**: Use Pydantic models for data validation

## License

This implementation is part of the larger project and follows the same license terms.

## References

- [GraphRAG Field Guide](https://neo4j.com/blog/developer/graphrag-field-guide-rag-patterns/)
- [10 Rules for Optimizing GraphRAG](https://www.lettria.com/blogpost/10-rules-for-optimizing-your-graphrag-strategies)
- [PathRAG Paper](https://arxiv.org/pdf/2502.14902)
- [Caching in RAG](https://arxiv.org/html/2404.12457v1)
