"""Base classes for knowledge graph consolidation components."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from neo4j import Driver, GraphDatabase
import logging

class KGComponent(ABC):
    """Base class for all knowledge graph components."""
    
    def __init__(self, driver: Driver, config: Optional[Dict[str, Any]] = None):
        """Initialize the component with a Neo4j driver and configuration.
        
        Args:
            driver: Neo4j driver instance
            config: Configuration dictionary for the component
        """
        self.driver = driver
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        pass
    
    def execute_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Execute a read query against the Neo4j database.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
            except Exception as e:
                self.logger.error(f"Error executing query: {e}")
                raise
    
    def execute_write_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Execute a write query against the Neo4j database.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        with self.driver.session() as session:
            try:
                with session.begin_transaction() as tx:
                    result = tx.run(query, parameters or {})
                    records = [dict(record) for record in result]
                    tx.commit()
                    return records
            except Exception as e:
                self.logger.error(f"Error executing write query: {e}")
                if 'tx' in locals():
                    tx.rollback()
                raise
