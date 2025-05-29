"""
Knowledge Graph Consolidation System for Neo4j

This module provides tools for consolidating, deduplicating, and enhancing
knowledge graphs with a focus on non-destructive operations.
"""

__version__ = "0.1.0"

# Import core components
from .core.consolidator import KnowledgeGraphConsolidator  # noqa: F401
from .core.duplicate_detector import DuplicateDetector  # noqa: F401
from .core.node_merger import NodeMerger  # noqa: F401
from .core.relationship_discoverer import RelationshipDiscoverer  # noqa: F401
from .core.conflict_resolver import ConflictResolver  # noqa: F401
from .core.community_analyzer import CommunityAnalyzer  # noqa: F401
from .core.summary_consolidator import SummaryConsolidator  # noqa: F401
