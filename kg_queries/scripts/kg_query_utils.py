"""
Utility functions for Neo4j knowledge graph queries.
Provides common functionality for connecting to Neo4j and processing results.
"""
import os
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables from .env if available
load_dotenv()

# Neo4j connection parameters
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Common property names used in the knowledge graph
STRING_PROPERTIES = ["name", "title", "description"]
ARRAY_PROPERTIES = ["alias", "content", "text"]
ALL_PROPERTIES = STRING_PROPERTIES + ARRAY_PROPERTIES

# Node labels commonly used in the knowledge graph
COMMON_LABELS = ["__Entity__", "Character", "Chunk", "__KGBuilder__"]

def get_neo4j_driver():
    """Creates and returns a Neo4j driver instance."""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def execute_query(cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
    """
    Executes a Cypher query and returns the results as a list of dictionaries.
    
    Args:
        cypher: The Cypher query to execute
        params: Optional parameters for the query
        
    Returns:
        List of result records as dictionaries
    """
    driver = get_neo4j_driver()
    with driver.session() as session:
        if params is None:
            params = {}
        result = session.run(cypher, params)
        records = [dict(record) for record in result]
    driver.close()
    return records

def format_node_for_display(node, query: Optional[str] = None, 
                           properties: Optional[List[str]] = None,
                           context_size: int = 50) -> Dict[str, Any]:
    """
    Formats a Neo4j node for display, including matched properties if a query is provided.
    
    Args:
        node: The Neo4j node to format
        query: Optional search query to highlight matches
        properties: Optional list of properties to include (defaults to ALL_PROPERTIES)
        context_size: Number of characters to show before and after a match in text
        
    Returns:
        Dictionary with formatted node information
    """
    if properties is None:
        properties = ALL_PROPERTIES
        
    node_props = dict(node)
    formatted = {
        "id": node.element_id,
        "labels": list(node.labels),
        "properties": {}
    }
    
    # Track which properties matched the query
    matching_props = []
    
    for prop in properties:
        if prop not in node_props:
            continue
            
        value = node_props[prop]
        
        # If we have a query, check for matches and format accordingly
        if query:
            query_lower = query.lower()
            
            if isinstance(value, list):
                # For arrays, join and check
                text = ' '.join([str(item) for item in value])
                if query_lower in text.lower():
                    matching_props.append(prop)
                    # For text properties, truncate to show only relevant part
                    if prop in ['text', 'content'] and len(text) > context_size * 2 + len(query):
                        # Find the position of the query in the text
                        pos = text.lower().find(query_lower)
                        start = max(0, pos - context_size)
                        end = min(len(text), pos + len(query) + context_size)
                        formatted["properties"][prop] = f"...{text[start:end]}..."
                    else:
                        formatted["properties"][prop] = value
            else:
                # For strings, direct check
                try:
                    if query_lower in str(value).lower():
                        matching_props.append(prop)
                        formatted["properties"][prop] = value
                except Exception:
                    # Skip any properties that can't be converted to string
                    continue
        else:
            # If no query, include all properties
            formatted["properties"][prop] = value
    
    if query and matching_props:
        formatted["matched_in"] = matching_props
        
    return formatted

def paginate_results(results: List[Any], page: int = 1, page_size: int = 10) -> Tuple[List[Any], Dict[str, int]]:
    """
    Paginates a list of results.
    
    Args:
        results: The list to paginate
        page: The page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Tuple of (paginated_results, pagination_info)
    """
    total = len(results)
    total_pages = (total + page_size - 1) // page_size
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    # Calculate start and end indices
    start = (page - 1) * page_size
    end = min(start + page_size, total)
    
    pagination = {
        "page": page,
        "page_size": page_size,
        "total_items": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    return results[start:end], pagination

def print_results(results: List[Dict], pagination: Optional[Dict] = None, 
                 query: Optional[str] = None, verbose: bool = False):
    """
    Prints formatted search results.
    
    Args:
        results: List of formatted node results
        pagination: Optional pagination information
        query: Optional search query that was used
        verbose: Whether to print full property values
    """
    if query:
        print(f"\nResults for '{query}':")
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results):
        print(f"\n- Node {i+1}/{len(results)} | ID: {result['id']} | Labels: {result['labels']}")
        
        # Print properties
        for prop, value in result["properties"].items():
            if isinstance(value, list) and not verbose:
                # Truncate lists for display
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
                print(f"  {prop}: {value_str}")
            else:
                print(f"  {prop}: {value}")
        
        # Print which properties matched
        if "matched_in" in result:
            print(f"  [Matched in: {', '.join(result['matched_in'])}]")
        
        print("---")
    
    # Print pagination info if available
    if pagination:
        print(f"\nPage {pagination['page']}/{pagination['total_pages']} "
              f"(showing {len(results)} of {pagination['total_items']} items)")
        
        if pagination['has_prev']:
            print("Use --page X to view previous pages")
        if pagination['has_next']:
            print("Use --page X to view next pages")
