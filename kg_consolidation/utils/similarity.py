"""Utility functions for calculating similarities between strings and nodes."""
from typing import Dict, Any, List, Tuple, Optional
import re
from difflib import SequenceMatcher
import string

# Pre-compile regex patterns for performance
PUNCTUATION = re.compile(f'[{re.escape(string.punctuation)}]')
WHITESPACE = re.compile(r'\s+')

def normalize_string(s: str) -> str:
    """Normalize a string for comparison.
    
    Args:
        s: Input string to normalize
        
    Returns:
        Normalized string with punctuation removed and whitespace normalized
    """
    if not isinstance(s, str):
        return ""
    
    # Convert to lowercase
    s = s.lower()
    
    # Remove punctuation
    s = PUNCTUATION.sub(' ', s)
    
    # Normalize whitespace
    s = WHITESPACE.sub(' ', s).strip()
    
    return s

def calculate_similarity(str1: str, str2: str, method: str = 'ratio') -> float:
    """Calculate similarity between two strings.
    
    Args:
        str1: First string
        str2: Second string
        method: Similarity calculation method ('ratio', 'partial_ratio', 'token_sort_ratio')
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not str1 or not str2:
        return 0.0
    
    # Normalize both strings
    str1 = normalize_string(str1)
    str2 = normalize_string(str2)
    
    # Use SequenceMatcher for basic ratio calculation
    if method == 'ratio':
        return SequenceMatcher(None, str1, str2).ratio()
    
    # For partial ratio, find the best matching substring
    elif method == 'partial_ratio':
        len1, len2 = len(str1), len(str2)
        
        if len1 == 0 or len2 == 0:
            return 0.0
            
        # Use the shorter string as the needle
        if len1 <= len2:
            shorter, longer = str1, str2
        else:
            shorter, longer = str2, str1
            
        m = SequenceMatcher(None, shorter, longer)
        blocks = m.get_matching_blocks()
        
        # Find the best matching block
        scores = []
        for block in blocks:
            long_start = block[1] - block[0] if (block[1] - block[0]) > 0 else 0
            long_end = long_start + len(shorter)
            long_substr = longer[long_start:long_end]
            
            m2 = SequenceMatcher(None, shorter, long_substr)
            r = m2.ratio()
            scores.append(r)
            
        return max(scores) if scores else 0.0
    
    # For token sort ratio, sort tokens before comparing
    elif method == 'token_sort_ratio':
        tokens1 = sorted(str1.split())
        tokens2 = sorted(str2.split())
        return SequenceMatcher(None, ' '.join(tokens1), ' '.join(tokens2)).ratio()
    
    else:
        raise ValueError(f"Unknown similarity method: {method}")

def calculate_node_similarity(
    node1: Dict[str, Any], 
    node2: Dict[str, Any],
    property_weights: Optional[Dict[str, float]] = None
) -> float:
    """Calculate similarity between two nodes based on their properties.
    
    Args:
        node1: First node with properties
        node2: Second node with properties
        property_weights: Dictionary mapping property names to weights
        
    Returns:
        Weighted similarity score between 0.0 and 1.0
    """
    if not property_weights:
        property_weights = {'name': 1.0}  # Default to just comparing names
    
    total_weight = 0.0
    weighted_sum = 0.0
    
    for prop, weight in property_weights.items():
        if prop not in node1 or prop not in node2:
            continue
            
        # Handle different property types
        if isinstance(node1[prop], str) and isinstance(node2[prop], str):
            similarity = calculate_similarity(node1[prop], node2[prop])
        elif isinstance(node1[prop], (int, float)) and isinstance(node2[prop], (int, float)):
            # For numeric properties, use relative difference
            max_val = max(abs(node1[prop]), abs(node2[prop]))
            if max_val == 0:
                similarity = 1.0  # Both are zero
            else:
                similarity = 1.0 - (abs(node1[prop] - node2[prop]) / max_val)
        else:
            # For other types, just check equality
            similarity = 1.0 if node1[prop] == node2[prop] else 0.0
        
        weighted_sum += similarity * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
        
    return weighted_sum / total_weight

def find_duplicate_pairs(
    nodes: List[Dict[str, Any]], 
    threshold: float = 0.9,
    property_weights: Optional[Dict[str, float]] = None
) -> List[Tuple[int, int, float]]:
    """Find pairs of duplicate nodes from a list.
    
    Args:
        nodes: List of nodes with properties
        threshold: Minimum similarity score to consider nodes as duplicates
        property_weights: Dictionary mapping property names to weights
        
    Returns:
        List of tuples (index1, index2, similarity) for duplicate pairs
    """
    duplicates = []
    
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            similarity = calculate_node_similarity(
                nodes[i], nodes[j], property_weights
            )
            
            if similarity >= threshold:
                duplicates.append((i, j, similarity))
    
    # Sort by similarity in descending order
    return sorted(duplicates, key=lambda x: x[2], reverse=True)

def group_duplicates(
    nodes: List[Dict[str, Any]], 
    threshold: float = 0.9,
    property_weights: Optional[Dict[str, float]] = None
) -> List[List[int]]:
    """Group duplicate nodes together.
    
    Args:
        nodes: List of nodes with properties
        threshold: Minimum similarity score to consider nodes as duplicates
        property_weights: Dictionary mapping property names to weights
        
    Returns:
        List of groups, where each group contains indices of duplicate nodes
    """
    if not nodes:
        return []
        
    # Initialize each node in its own group
    groups = [[i] for i in range(len(nodes))]
    
    # If we have property weights, we can optimize by only comparing certain properties
    # For now, we'll do a full comparison
    
    # Compare each pair of nodes
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            similarity = calculate_node_similarity(
                nodes[i], nodes[j], property_weights
            )
            
            if similarity >= threshold:
                # Find the groups containing i and j
                group_i = next(g for g in groups if i in g)
                group_j = next(g for g in groups if j in g)
                
                # If they're in different groups, merge them
                if group_i != group_j:
                    groups.remove(group_i)
                    groups.remove(group_j)
                    groups.append(group_i + group_j)
    
    return groups
