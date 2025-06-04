"""
LLM Services Package for Adaptive Quizzing.

This package provides modular LLM-based services for the adaptive quizzing system,
including question generation and answer assessment.
"""

# Import key components for easier access
from kg_quizzing.scripts.llm_services.openai_client import (
    get_openai_client,
    is_openai_available,
    get_default_model
)

from kg_quizzing.scripts.llm_services.question_generator import LLMQuestionGenerator
from kg_quizzing.scripts.llm_services.assessment_service import LLMAssessmentService

# Version information
__version__ = "1.0.0"
