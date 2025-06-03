"""
Conversation class for conversation history.
"""
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from .message import ConversationMessage


class QuizConversation:
    """Class representing a conversation in a quiz session."""
    
    def __init__(self, 
                conversation_id: Optional[str] = None,
                student_id: Optional[str] = None,
                quiz_id: Optional[str] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a quiz conversation.
        
        Args:
            conversation_id: Optional unique identifier for the conversation
            student_id: Optional identifier for the student
            quiz_id: Optional identifier for the quiz
            metadata: Optional metadata for the conversation
        """
        self.conversation_id = conversation_id if conversation_id else str(uuid.uuid4())
        self.student_id = student_id
        self.quiz_id = quiz_id
        self.metadata = metadata if metadata is not None else {}
        self.messages: List[ConversationMessage] = []
        self.start_time = time.time()
        self.end_time: Optional[float] = None
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add a message to the conversation.
        
        Args:
            role: The role of the message sender
            content: The content of the message
            metadata: Optional metadata for the message
            
        Returns:
            The created ConversationMessage
        """
        message = ConversationMessage(role, content, metadata=metadata)
        self.messages.append(message)
        return message
    
    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add a system message to the conversation.
        
        Args:
            content: The content of the message
            metadata: Optional metadata for the message
            
        Returns:
            The created ConversationMessage
        """
        return self.add_message("system", content, metadata)
    
    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add a user message to the conversation.
        
        Args:
            content: The content of the message
            metadata: Optional metadata for the message
            
        Returns:
            The created ConversationMessage
        """
        return self.add_message("user", content, metadata)
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add an assistant message to the conversation.
        
        Args:
            content: The content of the message
            metadata: Optional metadata for the message
            
        Returns:
            The created ConversationMessage
        """
        return self.add_message("assistant", content, metadata)
    
    def add_question(self, question: Dict[str, Any]) -> ConversationMessage:
        """
        Add a question to the conversation.
        
        Args:
            question: The question dictionary
            
        Returns:
            The created ConversationMessage
        """
        question_text = question.get("text", "")
        
        # Add options if it's a multiple-choice question
        if "options" in question:
            options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(question["options"])])
            question_text = f"{question_text}\n\n{options_text}"
        
        return self.add_assistant_message(question_text, {
            "question_type": question.get("type"),
            "difficulty": question.get("difficulty"),
            "community_id": question.get("community_id"),
            "question_id": question.get("id", str(uuid.uuid4())),
            "is_question": True
        })
    
    def add_answer(self, answer: str, correct: bool, 
                 quality_score: Optional[int] = None,
                 feedback: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add an answer to the conversation.
        
        Args:
            answer: The student's answer
            correct: Whether the answer was correct
            quality_score: Optional quality score for the answer
            feedback: Optional feedback for the answer
            
        Returns:
            The created ConversationMessage
        """
        return self.add_user_message(answer, {
            "correct": correct,
            "quality_score": quality_score,
            "feedback": feedback,
            "is_answer": True
        })
    
    def add_feedback(self, feedback: Dict[str, Any]) -> ConversationMessage:
        """
        Add feedback to the conversation.
        
        Args:
            feedback: The feedback dictionary
            
        Returns:
            The created ConversationMessage
        """
        feedback_text = feedback.get("message", "")
        
        if feedback.get("explanation"):
            feedback_text += f"\n\n{feedback['explanation']}"
        
        if feedback.get("next_steps"):
            next_steps = "\n".join([f"- {step}" for step in feedback["next_steps"]])
            feedback_text += f"\n\n{next_steps}"
        
        return self.add_assistant_message(feedback_text, {
            "correct": feedback.get("correct"),
            "quality_score": feedback.get("quality_score"),
            "is_feedback": True
        })
    
    def end_conversation(self) -> None:
        """End the conversation and record the end time."""
        self.end_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the conversation to a dictionary.
        
        Returns:
            Dictionary representation of the conversation
        """
        return {
            "conversation_id": self.conversation_id,
            "student_id": self.student_id,
            "quiz_id": self.quiz_id,
            "metadata": self.metadata,
            "messages": [message.to_dict() for message in self.messages],
            "start_time": self.start_time,
            "start_time_formatted": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": self.end_time,
            "end_time_formatted": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_seconds": self.end_time - self.start_time if self.end_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuizConversation':
        """
        Create a conversation from a dictionary.
        
        Args:
            data: Dictionary representation of the conversation
            
        Returns:
            QuizConversation instance
        """
        conversation = cls(
            conversation_id=data.get("conversation_id"),
            student_id=data.get("student_id"),
            quiz_id=data.get("quiz_id"),
            metadata=data.get("metadata", {})
        )
        
        conversation.start_time = data.get("start_time", time.time())
        conversation.end_time = data.get("end_time")
        
        for message_data in data.get("messages", []):
            message = ConversationMessage.from_dict(message_data)
            conversation.messages.append(message)
        
        return conversation
