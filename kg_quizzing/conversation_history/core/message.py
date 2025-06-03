"""
Message class for conversation history.
"""
import time
from typing import Dict, Any, Optional
from datetime import datetime


class ConversationMessage:
    """Class representing a message in a conversation."""
    
    def __init__(self, 
                role: str, 
                content: str, 
                timestamp: Optional[float] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a conversation message.
        
        Args:
            role: The role of the message sender (e.g., "system", "user", "assistant")
            content: The content of the message
            timestamp: Optional timestamp for the message (defaults to current time)
            metadata: Optional metadata for the message
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.metadata = metadata if metadata is not None else {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "timestamp_formatted": datetime.fromtimestamp(self.timestamp).isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """
        Create a message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            ConversationMessage instance
        """
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {})
        )
