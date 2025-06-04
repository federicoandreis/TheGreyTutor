"""
OpenAI Client Module for LLM Services.

This module provides a centralized OpenAI client initialization and configuration
for all LLM services in the adaptive quizzing system.
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default model configuration
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4")

# OpenAI client initialization
try:
    import openai
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY environment variable not set. LLM features will not work.")
        OPENAI_AVAILABLE = False
    else:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        OPENAI_AVAILABLE = True
        logger.info("OpenAI client initialized successfully")
except ImportError as e:
    logger.warning(f"OpenAI package not found: {e}. LLM features will not work.")
    OPENAI_AVAILABLE = False
except Exception as e:
    logger.warning(f"Error initializing OpenAI client: {e}. LLM features will not work.")
    OPENAI_AVAILABLE = False


def get_openai_client():
    """
    Get the OpenAI client instance.
    
    Returns:
        OpenAI client instance if available, None otherwise
    """
    if OPENAI_AVAILABLE:
        return client
    return None


def is_openai_available():
    """
    Check if OpenAI is available.
    
    Returns:
        True if OpenAI is available, False otherwise
    """
    return OPENAI_AVAILABLE


def get_default_model():
    """
    Get the default LLM model.
    
    Returns:
        Default model name
    """
    return DEFAULT_MODEL
