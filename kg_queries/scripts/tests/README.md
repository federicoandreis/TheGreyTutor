# PathRAG Test Suite

This directory contains test scripts for the PathRAG retriever implementation. These tests have been organized into a dedicated directory for better code organization and maintainability.

## Available Test Scripts

### `test_pathrag_suite.py`

A comprehensive test suite for the PathRAG retriever that evaluates multiple query categories and retrieval strategies.

```bash
# Run the full test suite with the pathrag strategy
python test_pathrag_suite.py --strategy pathrag --verbose

# Run tests for specific categories
python test_pathrag_suite.py --category character --strategy pathrag
```

### `test_pathrag.py`

Demonstrates the PathRAG retriever's capabilities for community-aware path-based retrieval.

```bash
# Test with a specific query
python test_pathrag.py "Who is Aragorn?"

# Test with verbose output
python test_pathrag.py "What is the One Ring?" --verbose
```

### `test_improved_prompt.py`

Demonstrates the improved PathRAG LLM prompt formatting and shows how the prompt is structured for better answer synthesis.

```bash
# Test the improved prompt with a specific query
python test_improved_prompt.py "What is the relationship between Frodo and the Ring of Power?"
```

### `test_retriever.py`

Tests the basic functionality of the GraphRAG retriever with simple queries to ensure everything is working correctly.

```bash
# Run the basic retriever tests
python test_retriever.py
```

## Running Tests

When running tests from this directory, make sure you're in the correct working directory:

```bash
# Run from the scripts directory
cd ..
python tests/test_pathrag_suite.py

# Or run directly from the tests directory
cd tests
python test_pathrag.py "Who is Gandalf?"
```

## Test Coverage

The test suite covers:

1. **Basic Functionality**: Verifies that the retriever can execute queries and return results
2. **Performance Metrics**: Measures execution time and result counts
3. **Retrieval Strategies**: Tests different retrieval strategies (entity, relationship, hybrid, pathrag)
4. **Edge Cases**: Tests queries with no results, complex queries, and special characters
5. **Prompt Formatting**: Tests the LLM prompt generation for different query types

## Adding New Tests

When adding new tests to this directory, please follow these guidelines:

1. Use descriptive names for test files and functions
2. Include docstrings explaining the purpose of each test
3. Add command-line arguments for flexibility
4. Update this README with information about new test files
