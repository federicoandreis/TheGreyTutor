"""
Response Parser Module for LLM Services.

This module provides functionality for parsing LLM responses for question generation
and answer assessment.
"""
import re
import json
import logging
import random
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_question_response(
    response_text: str,
    question_type: str,
    entity_name: str,
    difficulty: int,
    community_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Parse the LLM's response to a question generation prompt.
    
    Args:
        response_text: The LLM's response text
        question_type: The type of question
        entity_name: The entity name
        difficulty: The difficulty level
        community_id: The community ID
        
    Returns:
        Dictionary containing the generated question
    """
    try:
        # Extract the JSON object from the response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in the response")
        
        json_str = response_text[json_start:json_end]
        question_data = json.loads(json_str)
        
        # Extract the question text and answer (accept both 'question_text' and 'question')
        question_text = question_data.get("question_text") or question_data.get("question") or ""
        answer = question_data.get("answer") or question_data.get("correct_answer") or ""
        options = question_data.get("options", [])
        
        # Determine the tier based on difficulty
        tier = "basic"
        if difficulty > 3 and difficulty < 8:
            tier = "intermediate"
        elif difficulty >= 8:
            tier = "advanced"
        
        # Create the question object
        question = {
            "question": question_text,
            "text": question_text,
            "type": question_type,
            "difficulty": difficulty,
            "tier": tier,
            "entity": entity_name,
            "community_id": community_id,
            "answer": answer
        }
        
        if question_type == "multiple_choice":
            # Accept LLM output if options and correct_answer are present and question_text is non-empty
            options = question_data.get("options")
            answer = question_data.get("correct_answer") or question_data.get("answer")
            question_text_llm = question_data.get("question_text") or question_data.get("question") or ""
            valid = bool(question_text_llm and options and answer)
            if valid:
                question["question"] = question_text_llm
                question["text"] = question_text_llm
                question["options"] = options
                question["correct_answer"] = answer
            else:
                logging.warning(f"LLM response missing or invalid for entity '{entity_name}'. Using fallback options.")
                question_text = f"What do you know about {entity_name}?"
                options = generate_fallback_options(entity_name)
                answer = options[0]
                question["question"] = question_text
                question["text"] = question_text
                question["options"] = options
                question["correct_answer"] = answer
        return question
    
    except Exception as e:
        logger.error(f"Failed to parse question response: {e}")
        logger.debug(f"Response text: {response_text}")
        
        # Extract question text directly if possible
        question_text = entity_name
        try:
            question_match = re.search(r'"question_text":\s*"([^"]+)"', response_text)
            if question_match:
                question_text = question_match.group(1)
        except:
            pass
        
        # Extract answer if possible
        answer = ""
        try:
            answer_match = re.search(r'"answer":\s*"([^"]+)"', response_text)
            if answer_match:
                answer = answer_match.group(1)
        except:
            pass
        
        # For multiple choice, try to extract options
        options = []
        if question_type == "multiple_choice":
            try:
                # Try to extract a list from the response text
                regex_options = re.findall(r'"options"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
                if regex_options:
                    # Split by comma, remove quotes and whitespace
                    raw_opts = regex_options[0].split(',')
                    options = [opt.strip().strip('"\'') for opt in raw_opts if opt.strip()]
            except:
                pass
            
            # If we still don't have options, use fallback options
            if not options:
                # Try to extract entity type from the response text
                entity_type = None
                try:
                    # Look for type hints in the response
                    type_indicators = {
                        "person": ["character", "person", "being", "wizard", "hobbit", "elf", "dwarf", "king", "queen"],
                        "place": ["location", "place", "realm", "kingdom", "land", "region", "city", "fortress", "mountain"],
                        "object": ["artifact", "object", "item", "weapon", "ring", "sword", "treasure", "tool"],
                        "race": ["race", "species", "folk", "people", "beings"],
                        "event": ["event", "battle", "war", "council", "meeting", "journey"]
                    }
                    
                    for type_name, indicators in type_indicators.items():
                        if any(indicator in response_text.lower() for indicator in indicators):
                            entity_type = type_name
                            break
                except:
                    pass
                
                options = generate_fallback_options(entity_name, entity_type)
        
        # Create a fallback question
        fallback_question = {
            "question": f"What do you know about {entity_name}?",
            "text": f"What do you know about {entity_name}?",
            "type": question_type,
            "difficulty": difficulty,
            "tier": "basic",
            "entity": entity_name,
            "community_id": community_id,
            "answer": answer or f"Information about {entity_name} can be found in the lore of Middle-earth."
        }
        
        # Add options for multiple choice
        if question_type == "multiple_choice":
            fallback_question["options"] = options
            fallback_question["correct_answer"] = options[0] if options else entity_name
        
        return fallback_question


def parse_assessment_response(response_text: str) -> Tuple[bool, int, Dict[str, Any]]:
    """
    Parse the LLM's response to an assessment prompt.
    
    Args:
        response_text: The LLM's response text
        
    Returns:
        Tuple of (correct, quality_score, assessment_details)
        correct: Whether the answer was correct
        quality_score: Quality score for the answer (0-100)
        assessment_details: Dictionary containing detailed assessment information
    """
    try:
        # Extract the JSON object from the response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in the response")
        
        json_str = response_text[json_start:json_end]
        assessment = json.loads(json_str)
        
        # Extract the assessment components
        correct = assessment.get("correct", False)
        quality_score = assessment.get("quality_score", 0)
        
        # Ensure quality score is within range
        quality_score = max(0, min(100, quality_score))
        
        # Extract the assessment details
        assessment_details = {
            "explanation": assessment.get("explanation", ""),
            "strengths": assessment.get("strengths", []),
            "weaknesses": assessment.get("weaknesses", []),
            "suggestions": assessment.get("suggestions", [])
        }
        
        return correct, quality_score, assessment_details
    
    except Exception as e:
        logger.error(f"Failed to parse assessment response: {e}")
        logger.debug(f"Response text: {response_text}")
        
        # Try to extract information from the text directly
        correct = "yes" in response_text.lower() and "correct" in response_text.lower()
        
        # Try to extract a quality score
        quality_score = 0
        try:
            score_match = re.search(r"quality score:?\s*(\d+)", response_text, re.IGNORECASE)
            if score_match:
                quality_score = int(score_match.group(1))
                quality_score = max(0, min(100, quality_score))
        except:
            pass
        
        # Return a basic assessment
        return correct, quality_score, {
            "explanation": "The assessment could not be parsed correctly.",
            "strengths": [],
            "weaknesses": [],
            "suggestions": ["Please provide a more detailed answer."]
        }


def generate_fallback_options(entity_name: str, entity_type: str = None) -> List[str]:
    """
    Generate contextually relevant fallback options for multiple-choice questions.
    
    Args:
        entity_name: The entity name
        entity_type: The type of entity (person, place, object, etc.)
        
    Returns:
        List of options including the correct answer
    """
    # Categorized Tolkien-themed options for better contextual relevance
    tolkien_categories = {
        "person": [
            "Aragorn", "Gandalf", "Frodo Baggins", "Samwise Gamgee", "Legolas", "Gimli", 
            "Boromir", "Galadriel", "Elrond", "Saruman", "Sauron", "Gollum", "Bilbo Baggins", 
            "Thorin Oakenshield", "Éowyn", "Faramir", "Théoden", "Éomer", "Arwen", "Celeborn",
            "Círdan", "Glorfindel", "Haldir", "Treebeard", "Tom Bombadil", "Goldberry"
        ],
        "place": [
            "Gondor", "Rohan", "Mordor", "The Shire", "Rivendell", "Lothlórien",
            "Minas Tirith", "Isengard", "Moria", "Erebor", "Dale", "Mirkwood",
            "Fangorn Forest", "Helm's Deep", "Edoras", "Bree", "Weathertop", "Mount Doom",
            "Barad-dûr", "Cirith Ungol", "Osgiliath", "Ithilien", "Grey Havens", "Caradhras"
        ],
        "object": [
            "The One Ring", "Glamdring", "Sting", "Andúril", "Narsil", "Mithril",
            "Palantír", "Phial of Galadriel", "Elven Cloaks", "Lembas Bread", "Arkenstone",
            "Rings of Power", "White Tree of Gondor", "Silmarils", "Horn of Gondor", "Elven Rope"
        ],
        "race": [
            "Elves", "Dwarves", "Hobbits", "Men", "Orcs", "Uruk-hai", "Ents", "Eagles", 
            "Wizards", "Nazgûl", "Balrogs", "Trolls", "Wargs", "Maiar", "Valar"
        ],
        "event": [
            "War of the Ring", "Battle of the Pelennor Fields", "Council of Elrond",
            "Battle of Helm's Deep", "Fall of Gondolin", "Destruction of the Ring",
            "The Last Alliance", "Battle of Five Armies", "Scouring of the Shire"
        ]
    }
    
    # Default to a mix of categories if entity_type is not specified
    if not entity_type:
        # Try to infer entity type from name
        if any(place in entity_name for place in ["Mordor", "Gondor", "Rohan", "Shire", "Forest", "Mountain", "Tower", "City", "Land"]):
            entity_type = "place"
        elif any(item in entity_name for item in ["Ring", "Sword", "Blade", "Staff", "Cloak", "Armor", "Shield"]):
            entity_type = "object"
        elif any(race in entity_name for race in ["Elf", "Elves", "Dwarf", "Dwarves", "Hobbit", "Man", "Men", "Orc"]):
            entity_type = "race"
        elif any(event in entity_name for event in ["War", "Battle", "Council", "Siege", "Fall", "Destruction"]):
            entity_type = "event"
        else:
            # Default to person if we can't determine
            entity_type = "person"
    
    # Get options from the appropriate category
    category_options = tolkien_categories.get(entity_type, [])
    
    # If category is empty or not found, mix options from all categories
    if not category_options:
        category_options = [item for sublist in tolkien_categories.values() for item in sublist]
    
    # Ensure the entity name is not in the options
    options = [opt for opt in category_options if opt.lower() != entity_name.lower()]
    
    # Select 3 random options from the same category for contextual relevance
    if len(options) >= 3:
        selected_options = random.sample(options, 3)
    else:
        # If we don't have enough options, get some from other categories
        all_options = [item for sublist in tolkien_categories.values() for item in sublist]
        all_options = [opt for opt in all_options if opt.lower() != entity_name.lower()]
        additional_options = random.sample(all_options, 3 - len(options))
        selected_options = options + additional_options
        selected_options = selected_options[:3]
    
    # Add the entity name as the correct answer
    all_options = [entity_name] + selected_options
    
    # Shuffle the options
    random.shuffle(all_options)
    
    return all_options
