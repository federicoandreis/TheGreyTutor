"""
LLM Services Package for Adaptive Quizzing.

This package provides modular LLM-based services for the adaptive quizzing system,
including question generation and answer assessment.
"""

# Import key components for easier access
from .openai_client import (
    get_openai_client,
    is_openai_available,
    get_default_model
)

from .question_generator import LLMQuestionGenerator
from .assessment_service import LLMAssessmentService

# Version information
__version__ = "1.0.0"
