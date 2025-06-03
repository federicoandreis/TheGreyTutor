"""
API router for conversation history.

This module provides FastAPI endpoints for storing and retrieving conversation history.
It's designed to be integrated with the main backend application when needed.
"""
import os
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
import time
from datetime import datetime

from ..core.message import ConversationMessage
from ..core.conversation import QuizConversation
from ..core.manager import ConversationHistoryManager
from ..exporters.exporter import ConversationExporter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/conversations", tags=["conversations"])

# Initialize conversation history manager
conversation_manager = ConversationHistoryManager()


# Pydantic models for API requests and responses
class MessageMetadata(BaseModel):
    """Model for message metadata."""
    question_type: Optional[str] = None
    difficulty: Optional[int] = None
    community_id: Optional[int] = None
    question_id: Optional[str] = None
    is_question: Optional[bool] = None
    correct: Optional[bool] = None
    quality_score: Optional[int] = None
    feedback: Optional[Dict[str, Any]] = None
    is_answer: Optional[bool] = None
    is_feedback: Optional[bool] = None
    is_summary: Optional[bool] = None


class MessageRequest(BaseModel):
    """Model for a conversation message request."""
    role: str = Field(..., description="Role of the message sender (system, user, assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[float] = Field(None, description="Timestamp of the message")
    metadata: Optional[MessageMetadata] = Field(None, description="Additional metadata")


class ConversationMetadata(BaseModel):
    """Model for conversation metadata."""
    student_name: Optional[str] = None
    strategy: Optional[str] = None
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None


class ConversationRequest(BaseModel):
    """Model for a conversation request."""
    student_id: str = Field(..., description="ID of the student")
    quiz_id: Optional[str] = Field(None, description="ID of the quiz")
    metadata: Optional[ConversationMetadata] = Field(None, description="Additional metadata")
    messages: List[MessageRequest] = Field([], description="List of messages in the conversation")


class ConversationResponse(BaseModel):
    """Model for a conversation response."""
    conversation_id: str = Field(..., description="ID of the conversation")
    student_id: str = Field(..., description="ID of the student")
    quiz_id: Optional[str] = Field(None, description="ID of the quiz")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    start_time: float = Field(..., description="Start time of the conversation")
    start_time_formatted: str = Field(..., description="Formatted start time")
    end_time: Optional[float] = Field(None, description="End time of the conversation")
    end_time_formatted: Optional[str] = Field(None, description="Formatted end time")
    duration_seconds: Optional[float] = Field(None, description="Duration of the conversation in seconds")
    message_count: int = Field(..., description="Number of messages in the conversation")
    file_path: str = Field(..., description="Path to the conversation file")


class ConversationListResponse(BaseModel):
    """Model for a list of conversations."""
    conversations: List[ConversationResponse] = Field(..., description="List of conversations")
    count: int = Field(..., description="Number of conversations")


class MessageResponse(BaseModel):
    """Model for a conversation message response."""
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    timestamp: float = Field(..., description="Timestamp of the message")
    timestamp_formatted: str = Field(..., description="Formatted timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ConversationDetailResponse(ConversationResponse):
    """Model for a detailed conversation response."""
    messages: List[MessageResponse] = Field(..., description="List of messages in the conversation")


class ExportRequest(BaseModel):
    """Model for an export request."""
    format: str = Field("text", description="Export format (text, json, csv)")
    include_metadata: bool = Field(True, description="Whether to include metadata in the export")


class ExportResponse(BaseModel):
    """Model for an export response."""
    file_path: str = Field(..., description="Path to the exported file")
    format: str = Field(..., description="Export format")
    conversation_id: str = Field(..., description="ID of the conversation")
    student_id: str = Field(..., description="ID of the student")


# API endpoints
@router.post("", response_model=ConversationResponse)
async def create_conversation(request: ConversationRequest):
    """Create a new conversation."""
    try:
        # Create a new conversation
        conversation = QuizConversation(
            student_id=request.student_id,
            quiz_id=request.quiz_id,
            metadata=request.metadata.dict() if request.metadata else {}
        )
        
        # Add messages if provided
        for message_request in request.messages:
            message = ConversationMessage(
                role=message_request.role,
                content=message_request.content,
                timestamp=message_request.timestamp,
                metadata=message_request.metadata.dict() if message_request.metadata else {}
            )
            conversation.messages.append(message)
        
        # End the conversation if there are messages
        if conversation.messages:
            conversation.end_time = time.time()
        
        # Save the conversation
        file_path = conversation_manager.save_conversation(conversation)
        
        # Create response
        response = ConversationResponse(
            conversation_id=conversation.conversation_id,
            student_id=conversation.student_id,
            quiz_id=conversation.quiz_id,
            metadata=conversation.metadata,
            start_time=conversation.start_time,
            start_time_formatted=datetime.fromtimestamp(conversation.start_time).isoformat(),
            end_time=conversation.end_time,
            end_time_formatted=datetime.fromtimestamp(conversation.end_time).isoformat() if conversation.end_time else None,
            duration_seconds=conversation.end_time - conversation.start_time if conversation.end_time else None,
            message_count=len(conversation.messages),
            file_path=file_path
        )
        
        return response
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    student_id: Optional[str] = Query(None, description="Filter by student ID")
):
    """List all conversations, optionally filtered by student ID."""
    try:
        # Get conversations
        if student_id:
            conversation_files = conversation_manager.get_conversations_for_student(student_id)
        else:
            conversation_files = conversation_manager.get_all_conversations()
        
        # Load conversations
        conversations = []
        for file_path in conversation_files:
            try:
                conversation = conversation_manager.load_conversation(file_path)
                
                # Create response
                response = ConversationResponse(
                    conversation_id=conversation.conversation_id,
                    student_id=conversation.student_id,
                    quiz_id=conversation.quiz_id,
                    metadata=conversation.metadata,
                    start_time=conversation.start_time,
                    start_time_formatted=datetime.fromtimestamp(conversation.start_time).isoformat(),
                    end_time=conversation.end_time,
                    end_time_formatted=datetime.fromtimestamp(conversation.end_time).isoformat() if conversation.end_time else None,
                    duration_seconds=conversation.end_time - conversation.start_time if conversation.end_time else None,
                    message_count=len(conversation.messages),
                    file_path=file_path
                )
                
                conversations.append(response)
            except Exception as e:
                logger.error(f"Error loading conversation from {file_path}: {e}")
        
        return ConversationListResponse(
            conversations=conversations,
            count=len(conversations)
        )
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing conversations: {str(e)}")


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str = Path(..., description="ID of the conversation")
):
    """Get a conversation by ID."""
    try:
        # Find the conversation file
        all_files = conversation_manager.get_all_conversations()
        file_path = None
        
        for path in all_files:
            try:
                conversation = conversation_manager.load_conversation(path)
                if conversation.conversation_id == conversation_id:
                    file_path = path
                    break
            except Exception:
                pass
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        # Load the conversation
        conversation = conversation_manager.load_conversation(file_path)
        
        # Create response
        message_responses = [
            MessageResponse(
                role=message.role,
                content=message.content,
                timestamp=message.timestamp,
                timestamp_formatted=datetime.fromtimestamp(message.timestamp).isoformat(),
                metadata=message.metadata
            )
            for message in conversation.messages
        ]
        
        response = ConversationDetailResponse(
            conversation_id=conversation.conversation_id,
            student_id=conversation.student_id,
            quiz_id=conversation.quiz_id,
            metadata=conversation.metadata,
            start_time=conversation.start_time,
            start_time_formatted=datetime.fromtimestamp(conversation.start_time).isoformat(),
            end_time=conversation.end_time,
            end_time_formatted=datetime.fromtimestamp(conversation.end_time).isoformat() if conversation.end_time else None,
            duration_seconds=conversation.end_time - conversation.start_time if conversation.end_time else None,
            message_count=len(conversation.messages),
            file_path=file_path,
            messages=message_responses
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    message: MessageRequest,
    conversation_id: str = Path(..., description="ID of the conversation")
):
    """Add a message to a conversation."""
    try:
        # Find the conversation file
        all_files = conversation_manager.get_all_conversations()
        file_path = None
        
        for path in all_files:
            try:
                conversation = conversation_manager.load_conversation(path)
                if conversation.conversation_id == conversation_id:
                    file_path = path
                    break
            except Exception:
                pass
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        # Load the conversation
        conversation = conversation_manager.load_conversation(file_path)
        
        # Add the message
        new_message = ConversationMessage(
            role=message.role,
            content=message.content,
            timestamp=message.timestamp if message.timestamp else time.time(),
            metadata=message.metadata.dict() if message.metadata else {}
        )
        
        conversation.messages.append(new_message)
        
        # Save the conversation
        conversation_manager.save_conversation(conversation)
        
        # Create response
        response = MessageResponse(
            role=new_message.role,
            content=new_message.content,
            timestamp=new_message.timestamp,
            timestamp_formatted=datetime.fromtimestamp(new_message.timestamp).isoformat(),
            metadata=new_message.metadata
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message to conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding message: {str(e)}")


@router.post("/{conversation_id}/export", response_model=ExportResponse)
async def export_conversation(
    export_request: ExportRequest,
    conversation_id: str = Path(..., description="ID of the conversation")
):
    """Export a conversation in a specific format."""
    try:
        # Find the conversation file
        all_files = conversation_manager.get_all_conversations()
        file_path = None
        
        for path in all_files:
            try:
                conversation = conversation_manager.load_conversation(path)
                if conversation.conversation_id == conversation_id:
                    file_path = path
                    break
            except Exception:
                pass
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        # Load the conversation
        conversation = conversation_manager.load_conversation(file_path)
        
        # Create export directory
        export_dir = os.path.join(conversation_manager.storage_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate export filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{conversation.conversation_id}_{timestamp}"
        
        # Export based on format
        exporter = ConversationExporter()
        
        if export_request.format == "json":
            export_path = os.path.join(export_dir, f"{filename}.json")
            exporter.export_to_json(conversation, export_path)
        elif export_request.format == "csv":
            export_path = os.path.join(export_dir, f"{filename}.csv")
            exporter.export_to_csv(conversation, export_path)
        else:  # Default to text
            export_path = os.path.join(export_dir, f"{filename}.txt")
            exporter.export_to_text(conversation, export_path)
        
        # Create response
        response = ExportResponse(
            file_path=export_path,
            format=export_request.format,
            conversation_id=conversation.conversation_id,
            student_id=conversation.student_id
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting conversation: {str(e)}")


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str = Path(..., description="ID of the conversation")
):
    """Delete a conversation."""
    try:
        # Find the conversation file
        all_files = conversation_manager.get_all_conversations()
        file_path = None
        
        for path in all_files:
            try:
                conversation = conversation_manager.load_conversation(path)
                if conversation.conversation_id == conversation_id:
                    file_path = path
                    break
            except Exception:
                pass
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        # Delete the conversation
        success = conversation_manager.delete_conversation(file_path)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to delete conversation {conversation_id}")
        
        return {"message": f"Conversation {conversation_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")
