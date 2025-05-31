"""
Configuration for GraphRAG retrieval.

This module provides configuration settings for the GraphRAG system.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Neo4jConfig(BaseModel):
    """Neo4j database configuration."""
    uri: str = Field(
        default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        description="Neo4j URI"
    )
    username: str = Field(
        default=os.getenv("NEO4J_USER", "neo4j"),
        description="Neo4j username"
    )
    password: str = Field(
        default=os.getenv("NEO4J_PASSWORD", "password"),
        description="Neo4j password"
    )


class CacheConfig(BaseModel):
    """Cache configuration."""
    enabled: bool = Field(
        default=True,
        description="Whether caching is enabled"
    )
    ttl: int = Field(
        default=3600,  # 1 hour
        description="Time-to-live for cached items in seconds"
    )
    max_size: int = Field(
        default=1000,
        description="Maximum number of items in the cache"
    )
    directory: str = Field(
        default=os.getenv("CACHE_DIR", "./cache"),
        description="Directory for cache files"
    )


class RetrievalConfig(BaseModel):
    """Retrieval configuration."""
    default_strategy: str = Field(
        default="entity_centric",
        description="Default retrieval strategy"
    )
    max_results: int = Field(
        default=10,
        description="Maximum number of results to return"
    )
    similarity_threshold: float = Field(
        default=0.7,
        description="Minimum similarity threshold for semantic search"
    )
    max_path_length: int = Field(
        default=3,
        description="Maximum path length for path-based strategies"
    )
    default_properties: List[str] = Field(
        default=["name", "title", "description", "content", "text"],
        description="Default properties to search in"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(
        default=os.getenv("LOG_LEVEL", "INFO"),
        description="Logging level"
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Logging format"
    )
    file: Optional[str] = Field(
        default=os.getenv("LOG_FILE", None),
        description="Log file path"
    )


class GraphRAGConfig(BaseModel):
    """GraphRAG configuration."""
    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


# Global configuration instance
_config: Optional[GraphRAGConfig] = None


def get_config() -> GraphRAGConfig:
    """
    Get the global configuration instance.
    
    Returns:
        GraphRAGConfig instance
    """
    global _config
    
    if _config is None:
        _config = GraphRAGConfig()
        
        # Set up logging
        logging_level = getattr(logging, _config.logging.level.upper(), logging.INFO)
        logging.basicConfig(
            level=logging_level,
            format=_config.logging.format,
            filename=_config.logging.file
        )
    
    return _config


def set_config(config: GraphRAGConfig) -> None:
    """
    Set the global configuration instance.
    
    Args:
        config: GraphRAGConfig instance
    """
    global _config
    _config = config
    
    # Update logging configuration
    logging_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logging.basicConfig(
        level=logging_level,
        format=config.logging.format,
        filename=config.logging.file
    )


def load_config_from_file(file_path: str) -> GraphRAGConfig:
    """
    Load configuration from a file.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        GraphRAGConfig instance
    """
    import json
    
    with open(file_path, "r") as f:
        config_dict = json.load(f)
    
    config = GraphRAGConfig.parse_obj(config_dict)
    set_config(config)
    
    return config


def save_config_to_file(config: GraphRAGConfig, file_path: str) -> None:
    """
    Save configuration to a file.
    
    Args:
        config: GraphRAGConfig instance
        file_path: Path to the configuration file
    """
    import json
    
    config_dict = config.dict()
    
    with open(file_path, "w") as f:
        json.dump(config_dict, f, indent=2)
