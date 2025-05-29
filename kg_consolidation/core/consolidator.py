"""Main knowledge graph consolidation orchestrator."""
from typing import Dict, Any, List, Optional
from neo4j import Driver
import logging
from .base import KGComponent
from .duplicate_detector import DuplicateDetector
from .node_merger import NodeMerger
from .relationship_discoverer import RelationshipDiscoverer
from .conflict_resolver import ConflictResolver
from .community_analyzer import CommunityAnalyzer
from .summary_consolidator import SummaryConsolidator

class KnowledgeGraphConsolidator(KGComponent):
    """Orchestrates the knowledge graph consolidation process."""
    
    def __init__(self, driver: Driver, config: Optional[Dict[str, Any]] = None):
        """Initialize the consolidator with components and configuration.
        
        Args:
            driver: Neo4j driver instance
            config: Configuration dictionary
        """
        super().__init__(driver, config)
        self.components = self._initialize_components()
    
    def _initialize_components(self) -> Dict[str, KGComponent]:
        """Initialize all consolidation components."""
        config = self.config.get('components', {})
        
        return {
            'duplicate_detector': DuplicateDetector(
                self.driver, 
                config.get('duplicate_detector', {})
            ),
            'node_merger': NodeMerger(
                self.driver,
                config.get('node_merger', {})
            ),
            'relationship_discoverer': RelationshipDiscoverer(
                self.driver,
                config.get('relationship_discoverer', {})
            ),
            'conflict_resolver': ConflictResolver(
                self.driver,
                config.get('conflict_resolver', {})
            ),
            'community_analyzer': CommunityAnalyzer(
                self.driver,
                config.get('community_analyzer', {})
            ),
            'summary_consolidator': SummaryConsolidator(
                self.driver,
                config.get('summary_consolidator', {})
            )
        }
    
    def validate_config(self) -> bool:
        """Validate the configuration of all components."""
        return all(
            component.validate_config() 
            for component in self.components.values()
        )
    
    def run_consolidation(self, batch_size: int = 1000) -> Dict[str, Any]:
        """Run the complete consolidation pipeline.
        
        Args:
            batch_size: Number of nodes to process in each batch
            
        Returns:
            Dictionary with consolidation results and metrics
        """
        results = {}
        
        try:
            # 1. Detect and merge duplicate nodes
            self.logger.info("Starting duplicate detection...")
            duplicates = self.components['duplicate_detector'].find_duplicates(batch_size)
            results['duplicates_found'] = len(duplicates)
            
            # 2. Merge duplicate nodes
            if duplicates:
                self.logger.info(f"Merging {len(duplicates)} duplicate nodes...")
                merge_results = self.components['node_merger'].merge_nodes(duplicates)
                results.update(merge_results)
            
            # 3. Discover missing relationships
            self.logger.info("Discovering missing relationships...")
            relationships = self.components['relationship_discoverer'].find_relationships()
            results['relationships_discovered'] = len(relationships)
            
            # 4. Resolve conflicts
            self.logger.info("Resolving conflicts...")
            conflicts = self.components['conflict_resolver'].detect_conflicts()
            resolutions = self.components['conflict_resolver'].resolve_conflicts(conflicts)
            results['conflicts_resolved'] = len(resolutions)
            
            # 5. Analyze and link communities
            self.logger.info("Analyzing communities...")
            community_analysis = self.components['community_analyzer'].analyze_communities()
            results['communities_analyzed'] = len(community_analysis.get('communities', []))
            
            # 6. Consolidate community summaries
            self.logger.info("Consolidating community summaries...")
            summary_updates = self.components['summary_consolidator'].update_summaries()
            results['summaries_updated'] = len(summary_updates)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Consolidation failed: {e}")
            raise
    
    def incremental_update(self, changeset: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incremental update to the knowledge graph.
        
        Args:
            changeset: Dictionary describing the changes to process
            
        Returns:
            Dictionary with update results and metrics
        """
        results = {}
        
        try:
            # Process only the changed/added nodes and relationships
            if 'new_or_updated_nodes' in changeset:
                self.logger.info(f"Processing {len(changeset['new_or_updated_nodes'])} changed/added nodes...")
                
                # Check for duplicates involving the changed nodes
                duplicates = self.components['duplicate_detector'].find_duplicates(
                    node_ids=changeset['new_or_updated_nodes'],
                    batch_size=100
                )
                
                if duplicates:
                    merge_results = self.components['node_merger'].merge_nodes(duplicates)
                    results.update(merge_results)
            
            # Find new relationships involving the changed nodes
            if 'new_or_updated_nodes' in changeset:
                relationships = self.components['relationship_discoverer'].find_relationships(
                    node_ids=changeset['new_or_updated_nodes']
                )
                results['new_relationships'] = len(relationships)
            
            # Update affected communities
            if 'affected_communities' in changeset:
                community_updates = self.components['community_analyzer'].update_communities(
                    changeset['affected_communities']
                )
                results['communities_updated'] = len(community_updates)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Incremental update failed: {e}")
            raise
