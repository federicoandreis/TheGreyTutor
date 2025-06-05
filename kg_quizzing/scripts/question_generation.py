"""
Question Generation Module for Adaptive Quizzing.

This module implements various strategies for generating questions from the knowledge graph,
including factual, relationship, multiple-choice, synthesis, and application questions.
"""
import os
import logging
import random
import argparse
from typing import Dict, List, Any, Optional, Tuple
import re

from quiz_utils import (
    execute_query, 
    get_entity_by_name, 
    get_entity_relationships,
    get_entities_in_community,
    get_available_communities
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuestionGenerator:
    """Base class for question generators."""
    
    def __init__(self):
        """Initialize the question generator."""
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load question templates from the database.
        
        Returns:
            Dictionary of templates grouped by type
        """
        query = """
        MATCH (qt:QuestionTemplate)
        RETURN qt.id AS id, qt.type AS type, qt.difficulty AS difficulty, 
               qt.template AS template, qt.applicable_labels AS applicable_labels
        """
        
        results = execute_query(query)
        
        # Group templates by type
        templates = {}
        for result in results:
            template_type = result["type"]
            if template_type not in templates:
                templates[template_type] = []
            
            templates[template_type].append({
                "id": result["id"],
                "difficulty": result["difficulty"],
                "template": result["template"],
                "applicable_labels": result["applicable_labels"]
            })
        
        return templates
    
    def get_template_by_type_and_difficulty(self, 
                                           template_type: str, 
                                           difficulty: int,
                                           applicable_labels: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Get a template of the specified type and closest to the specified difficulty.
        
        Args:
            template_type: Type of template to get
            difficulty: Target difficulty level (1-10)
            applicable_labels: Optional list of labels that must be applicable
            
        Returns:
            Template dictionary if found, None otherwise
        """
        if template_type not in self.templates or not self.templates[template_type]:
            return None
        
        # Filter by applicable labels if provided
        filtered_templates = self.templates[template_type]
        if applicable_labels:
            filtered_templates = [
                t for t in filtered_templates 
                if any(label in t.get("applicable_labels", []) for label in applicable_labels)
            ]
        
        if not filtered_templates:
            return None
        
        # Find the template with the closest difficulty
        closest_template = min(
            filtered_templates, 
            key=lambda t: abs(t.get("difficulty", 5) - difficulty)
        )
        
        return closest_template
    
    def generate_question(self, 
                         template_type: str, 
                         difficulty: int,
                         entity_data: Optional[Dict[str, Any]] = None,
                         community_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate a question using the specified template type and difficulty.
        
        Args:
            template_type: Type of template to use
            difficulty: Target difficulty level (1-10)
            entity_data: Optional entity data to use for the question
            community_id: Optional community ID to use for the question
            
        Returns:
            Dictionary containing the generated question
        """
        # This is a base implementation that should be overridden by subclasses
        raise NotImplementedError("Subclasses must implement generate_question")


class FactualQuestionGenerator(QuestionGenerator):
    """Generator for factual questions about entity properties."""
    
    def generate_question(self, 
                         template_type: str = "factual", 
                         difficulty: int = 1,
                         entity_data: Optional[Dict[str, Any]] = None,
                         community_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a factual question about an entity property.
        
        Args:
            template_type: Type of template to use (default: "factual")
            difficulty: Target difficulty level (1-10)
            entity_data: Optional entity data to use for the question
            community_id: Optional community ID to use for the question
            
        Returns:
            Dictionary containing the generated question
        """
        # If no entity data is provided, get a random entity from the specified community
        if not entity_data:
            if community_id is None:
                # Get a random community
                communities = get_available_communities()
                if not communities:
                    raise ValueError("No communities found in the knowledge graph")
                
                community = random.choice(communities)
                community_id = community["id"]
            
            # Get entities in the community
            entities = get_entities_in_community(community_id)
            if not entities:
                raise ValueError(f"No entities found in community {community_id}")
            
            # Select a random entity
            entity = random.choice(entities)
            entity_name = entity["name"]
            entity_labels = entity["labels"]
            
            # Get full entity data
            entity_data = get_entity_by_name(entity_name)
            if not entity_data:
                raise ValueError(f"Entity {entity_name} not found")
        else:
            entity_name = entity_data.get("n", {}).get("name", "Unknown")
            entity_labels = entity_data.get("labels", [])
        
        # Get a template of the appropriate type and difficulty
        template = self.get_template_by_type_and_difficulty(
            template_type, difficulty, entity_labels
        )
        
        if not template:
            raise ValueError(f"No suitable template found for type {template_type} and difficulty {difficulty}")
        
        # Get entity properties
        entity_properties = entity_data.get("n", {})
        
        # Select a property to ask about
        # Exclude technical properties that are not thematic or interesting for the user
        excluded_properties = [
            # Database technical properties
            "complexity", "is_bridge", "bridge_communities", "id", "community_id",
            "identifier", "community", "belongs_to_community", "community_membership"
        ]
        
        available_properties = []
        for prop in entity_properties.keys():
            # Skip technical properties
            if prop in ["id", "name", "community_id"]:
                continue
                
            # Skip properties with 'id' or 'community' in the name
            if "id" in prop.lower() or "community" in prop.lower():
                continue
                
            # Skip properties with None values
            if entity_properties[prop] is None:
                continue
                
            # Skip properties where the value contains 'None'
            if "None" in str(entity_properties[prop]):
                continue
                
            # Skip empty values
            if isinstance(entity_properties[prop], str) and not entity_properties[prop].strip():
                continue
                
            # Skip empty lists
            if isinstance(entity_properties[prop], list) and not entity_properties[prop]:
                continue
                
            # Skip properties that are just generic labels or don't make sense as questions
            if prop.lower() in ["label", "type", "class", "category", "tags", "keywords", "status"]:
                continue
                
            # Skip properties that are too short
            if len(prop) < 3:
                continue
                
            # Add to available properties
            available_properties.append(prop)
        
        if not available_properties:
            # If no suitable properties are found, use a fallback question about the entity's description
            logger.warning(f"No suitable properties found for entity {entity_name}, using fallback question")
            property_name = "description"
            property_value = "This information is not recorded in the archives of Middle-earth."
        else:
            # Select a property that is likely to be meaningful
            # Prioritize these properties if available
            preferred_properties = ["description", "origin", "history", "purpose", "significance", "role"]
            
            # Filter for preferred properties that are available
            preferred_available = [p for p in preferred_properties if p in available_properties]
            
            if preferred_available:
                property_name = random.choice(preferred_available)
            else:
                property_name = random.choice(available_properties)
                
            property_value = entity_properties[property_name]
            
            # If property value is empty or None, provide a fallback
            if not property_value or property_value is None:
                property_value = "This information is not recorded in the archives of Middle-earth."
        
        # Ensure property value is properly formatted
        if isinstance(property_value, list):
            if len(property_value) == 1:
                property_value = property_value[0]
            elif len(property_value) > 1:
                property_value = ", ".join(str(v) for v in property_value[:-1]) + f", and {property_value[-1]}"
            else:
                # Empty list - shouldn't happen due to filtering above
                raise ValueError(f"Empty property value for {property_name} on entity {entity_name}")
        
        # Format entity and property names properly for display
        def format_entity(entity):
            if isinstance(entity, list):
                if len(entity) == 1:
                    return entity[0]
                elif len(entity) == 2:
                    return f"{entity[0]} and {entity[1]}"
                else:
                    return ", ".join(entity[:-1]) + f", and {entity[-1]}"
            return entity
        
        # Format property name to be more natural and descriptive
        def format_property(prop):
            # Replace underscores with spaces
            formatted = prop.replace("_", " ")
            
            # Capitalize first letter of each word
            formatted = " ".join(word.capitalize() for word in formatted.split())
            
            # Special case handling for common properties
            if formatted.lower() == "name":
                return "true name"
            elif formatted.lower() == "description":
                return "nature and description"
            elif formatted.lower() == "type":
                return "classification"
            elif formatted.lower() == "location":
                return "dwelling place"
            elif formatted.lower() == "origin":
                return "origins"
            
            return formatted
        
        display_entity = format_entity(entity_name)
        display_property = format_property(property_name)
        
        # Format the question with proper entity and property display
        question_text = template["template"].format(
            entity=entity_name,
            property=property_name
        )
        import re
        question_text = re.sub(r"(Is it:|Which of the following|Choose one:)[^?]*[?]", "", question_text, flags=re.IGNORECASE).strip()
        if not question_text.endswith('?'):
            question_text += '?'
        if len(question_text) < 10:
            question_text = f"What is {entity_name}?"
        
        # Create the question object
        question = {
            "text": question_text,
            "type": template_type,
            "difficulty": template["difficulty"],
            "template_id": template["id"],
            "entity": entity_name,
            "property": property_name,
            "answer": property_value,
            "community_id": community_id
        }
        
        return question


class RelationshipQuestionGenerator(QuestionGenerator):
    """Generator for questions about relationships between entities."""
    
    def generate_question(self, 
                         template_type: str = "relationship", 
                         difficulty: int = 3,
                         entity_data: Optional[Dict[str, Any]] = None,
                         community_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a question about relationships between entities.
        
        Args:
            template_type: Type of template to use (default: "relationship")
            difficulty: Target difficulty level (1-10)
            entity_data: Optional entity data to use for the question
            community_id: Optional community ID to use for the question
            
        Returns:
            Dictionary containing the generated question
        """
        # If no entity data is provided, get a random entity from the specified community
        if not entity_data:
            if community_id is None:
                # Get a random community
                communities = get_available_communities()
                if not communities:
                    raise ValueError("No communities found in the knowledge graph")
                
                community = random.choice(communities)
                community_id = community["id"]
            
            # Get entities in the community
            entities = get_entities_in_community(community_id)
            if not entities:
                raise ValueError(f"No entities found in community {community_id}")
            
            # Select a random entity
            entity = random.choice(entities)
            entity_name = entity["name"]
            entity_labels = entity["labels"]
            
            # Get full entity data
            entity_data = get_entity_by_name(entity_name)
            if not entity_data:
                raise ValueError(f"Entity {entity_name} not found")
        else:
            entity_name = entity_data.get("n", {}).get("name", "Unknown")
            entity_labels = entity_data.get("labels", [])
        
        # Get a template of the appropriate type and difficulty
        template = self.get_template_by_type_and_difficulty(
            template_type, difficulty, entity_labels
        )
        
        if not template:
            raise ValueError(f"No suitable template found for type {template_type} and difficulty {difficulty}")
        
        # Get entity relationships
        entity_id = entity_data.get("n", {}).element_id
        relationships = get_entity_relationships(entity_id)
        
        if not relationships:
            raise ValueError(f"No relationships found for entity {entity_name}")
        
        # Filter out technical relationships and None values
        filtered_relationships = []
        for rel in relationships:
            # Skip if relationship_type or related_entity_name is None
            if rel["relationship_type"] is None or rel["related_entity_name"] is None:
                continue
                
            rel_type = rel["relationship_type"].lower()
            
            # Skip if None appears in the string representation
            if "None" in str(rel_type) or "None" in str(rel["related_entity_name"]):
                continue
                
            # Skip technical relationships
            if not any(term in rel_type for term in ["id", "community", "identifier", "belongs_to", "member_of"]):
                filtered_relationships.append(rel)
        
        # If no suitable relationships are found, raise an error
        if not filtered_relationships:
            logger.warning(f"No suitable relationships found for entity {entity_name}, falling back to factual question")
            # Create a factual question generator and use it instead
            factual_generator = FactualQuestionGenerator()
            return factual_generator.generate_question(difficulty=difficulty, community_id=community_id)
        
        # Select a random relationship
        relationship = random.choice(filtered_relationships)
        related_entity_name = relationship["related_entity_name"]
        relationship_type = relationship["relationship_type"]
        
        # Final check for None values
        if related_entity_name is None or relationship_type is None or \
           "None" in str(related_entity_name) or "None" in str(relationship_type):
            raise ValueError(f"Invalid relationship data for entity {entity_name}")
        
        # Format the question template
        # Format entity names properly for display
        def format_entity(entity):
            if isinstance(entity, list):
                if len(entity) == 1:
                    return entity[0]
                elif len(entity) == 2:
                    return f"{entity[0]} and {entity[1]}"
                else:
                    return ", ".join(entity[:-1]) + f", and {entity[-1]}"
            return entity
        
        display_entity1 = format_entity(entity_name)
        display_entity2 = format_entity(related_entity_name)
        
        # Format the question with proper entity display
        try:
            question_text = template["template"].format(
                entity1=display_entity1,
                entity2=display_entity2
            )
            
            # Validate the question text
            if not question_text.endswith('?'):
                question_text += '?'
                
            # Check for malformed questions
            if len(question_text.strip()) < 10 or '?' not in question_text:
                # Use a fallback template
                question_text = f"According to the lore of Middle-earth, how is {display_entity1} connected to {display_entity2}?"
        except Exception as e:
            logger.warning(f"Error formatting relationship question: {e}")
            # Use a fallback template
            question_text = f"According to the lore of Middle-earth, how is {display_entity1} connected to {display_entity2}?"
        
        # Create a more natural, Tolkien-themed answer format
        relationship_display = relationship_type.lower().replace('_', ' ')
        
        # Create more natural phrasing based on relationship type
        if "has" in relationship_display or "contains" in relationship_display:
            answer_text = f"{entity_name} includes {related_entity_name} in its lore."
        elif "is" in relationship_display:
            answer_text = f"In the scrolls of Middle-earth, {entity_name} is described as {related_entity_name}."
        elif "created" in relationship_display or "made" in relationship_display:
            answer_text = f"The ancient texts reveal that {entity_name} crafted {related_entity_name}."
        elif "part" in relationship_display or "member" in relationship_display:
            answer_text = f"{entity_name} is part of the greater tale of {related_entity_name}."
        else:
            answer_text = f"The lore of Middle-earth connects {entity_name} with {related_entity_name} through {relationship_display}."
        
        # Create the question object
        question = {
            "text": question_text,
            "type": template_type,
            "difficulty": template["difficulty"],
            "template_id": template["id"],
            "entity1": entity_name,
            "entity2": related_entity_name,
            "relationship_type": relationship_type,
            "answer": answer_text,
            "community_id": community_id
        }
        
        return question


class MultipleChoiceQuestionGenerator(QuestionGenerator):
    """Generator for multiple-choice questions."""
    
    def generate_question(self, 
                         template_type: str = "multiple_choice", 
                         difficulty: int = 2,
                         entity_data: Optional[Dict[str, Any]] = None,
                         community_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a multiple-choice question.
        
        Args:
            template_type: Type of template to use (default: "multiple_choice")
            difficulty: Target difficulty level (1-10)
            entity_data: Optional entity data to use for the question
            community_id: Optional community ID to use for the question
            
        Returns:
            Dictionary containing the generated question
        """
        # If no entity data is provided, get a random entity from the specified community
        if not entity_data:
            if community_id is None:
                # Get a random community
                communities = get_available_communities()
                if not communities:
                    raise ValueError("No communities found in the knowledge graph")
                
                community = random.choice(communities)
                community_id = community["id"]
            
            # Get entities in the community
            entities = get_entities_in_community(community_id)
            if not entities:
                raise ValueError(f"No entities found in community {community_id}")
            
            # Select a random entity
            entity = random.choice(entities)
            entity_name = entity["name"]
            entity_labels = entity["labels"]
            
            # Get full entity data
            entity_data = get_entity_by_name(entity_name)
            if not entity_data:
                raise ValueError(f"Entity {entity_name} not found")
        else:
            entity_name = entity_data.get("n", {}).get("name", "Unknown")
            entity_labels = entity_data.get("labels", [])
        
        # Get a template of the appropriate type and difficulty
        template = self.get_template_by_type_and_difficulty(
            template_type, difficulty, entity_labels
        )
        
        if not template:
            raise ValueError(f"No suitable template found for type {template_type} and difficulty {difficulty}")
        
        # Get entity relationships
        entity_id = entity_data.get("n", {}).element_id
        relationships = get_entity_relationships(entity_id)
        
        if not relationships:
            raise ValueError(f"No relationships found for entity {entity_name}")
        
        # Filter out relationships with None values
        valid_relationships = []
        for rel in relationships:
            if (rel["related_entity_name"] is not None and 
                rel["relationship_type"] is not None and
                "None" not in str(rel["related_entity_name"]) and
                "None" not in str(rel["relationship_type"])):
                valid_relationships.append(rel)
        
        if not valid_relationships:
            raise ValueError(f"No valid relationships found for entity {entity_name}")
        
        # Select a random relationship
        relationship = random.choice(valid_relationships)
        correct_answer = relationship["related_entity_name"]
        relationship_type = relationship["relationship_type"]
        
        # Convert list values to strings
        if isinstance(correct_answer, list):
            correct_answer = correct_answer[0] if correct_answer else "Unknown"
        
        if isinstance(relationship_type, list):
            relationship_type = relationship_type[0] if relationship_type else "related to"
        
        # Get distractors (other entities that are not related to the entity in this way)
        # First, get other entities in the same community
        other_entities = get_entities_in_community(community_id, limit=20)
        
        # Filter out the correct answer, the original entity, and any None values
        distractors = []
        for e in other_entities:
            name = e["name"]
            
            # Skip if it's the correct answer or original entity
            if name == correct_answer or name == entity_name:
                continue
                
            # Skip None values
            if name is None or "None" in str(name):
                continue
                
            # Handle list values
            if isinstance(name, list):
                if name:  # If the list is not empty
                    name = name[0]  # Take the first item
                else:
                    continue  # Skip empty lists
            
            distractors.append(name)
        
        # If we don't have enough distractors, get entities from other communities
        if len(distractors) < 3:
            # Get entities from other communities
            other_communities = [
                c["id"] for c in get_available_communities() 
                if c["id"] != community_id
            ]
            
            for other_community_id in other_communities:
                if len(distractors) >= 3:
                    break
                
                other_community_entities = get_entities_in_community(other_community_id, limit=10)
                distractors.extend([
                    e["name"] for e in other_community_entities 
                    if e["name"] != correct_answer and e["name"] != entity_name
                    and e["name"] not in distractors
                    and e["name"] is not None and "None" not in str(e["name"])
                ])
        
        # Select 3 distractors
        if len(distractors) < 3:
            # If we still don't have enough distractors, duplicate some
            distractors = distractors * (3 // len(distractors) + 1)
        
        selected_distractors = random.sample(distractors, min(3, len(distractors)))
        
        # Check if the correct answer is the same as the entity (self-reference)
        if correct_answer == entity_name:
            # This is a self-reference, which doesn't make sense in a relationship question
            # Try to find a different relationship
            for alt_rel in valid_relationships:
                if alt_rel["related_entity_name"] != entity_name:
                    correct_answer = alt_rel["related_entity_name"]
                    relationship_type = alt_rel["relationship_type"]
                    break
            else:
                # If we couldn't find a non-self-reference, raise an error
                raise ValueError(f"All relationships for {entity_name} are self-references")
        
        # Filter out any distractors that match the entity name (to avoid self-references)
        selected_distractors = [d for d in selected_distractors if d != entity_name]
        
        # If we don't have enough distractors after filtering, get more
        while len(selected_distractors) < 3 and len(distractors) > len(selected_distractors):
            additional_distractors = [d for d in distractors if d not in selected_distractors and d != entity_name]
            if not additional_distractors:
                break
            selected_distractors.append(random.choice(additional_distractors))
        
        # Create the options (correct answer + distractors)
        options = [correct_answer] + selected_distractors
        # Deduplicate while preserving order
        seen = set()
        deduped_options = []
        for opt in options:
            if opt not in seen:
                deduped_options.append(opt)
                seen.add(opt)
        # If fewer than 4, fill with more unique distractors if possible
        all_distractors = [d for d in distractors if d not in deduped_options and d != correct_answer]
        while len(deduped_options) < 4 and all_distractors:
            next_opt = all_distractors.pop(0)
            deduped_options.append(next_opt)
        # If still fewer than 4, repeat distractors (last resort)
        while len(deduped_options) < 4:
            for d in distractors:
                if len(deduped_options) >= 4:
                    break
                deduped_options.append(d)
        random.shuffle(deduped_options)
        options = deduped_options[:4]
        
        # Format the question template
        # Ensure we're not asking about technical properties
        relationship_display = relationship_type.lower().replace('_', ' ')
        
        # Filter out any technical relationship types
        technical_terms = ["id", "community", "identifier", "belongs to", "member of"]
        
        if any(term in relationship_display for term in technical_terms):
            # Use a more thematic relationship description instead
            relationship_display = "connected to"
        
        # Format entity name properly for display
        if isinstance(entity_name, list):
            # If entity name is a list, format it properly
            if len(entity_name) == 1:
                display_entity = entity_name[0]
            elif len(entity_name) == 2:
                display_entity = f"{entity_name[0]} and {entity_name[1]}"
            else:
                display_entity = ", ".join(entity_name[:-1]) + f", and {entity_name[-1]}"
        else:
            display_entity = entity_name
        
        # Adjust the relationship phrasing to ensure grammatical correctness
        if "dwells in" in relationship_display or "lives in" in relationship_display:
            relationship_phrase = "dwells within"
        elif "located in" in relationship_display:
            relationship_phrase = "located within"
        elif "part of" in relationship_display:
            relationship_phrase = "part of"
        elif "member of" in relationship_display:
            relationship_phrase = "a member of"
        elif "created" in relationship_display:
            relationship_phrase = "created by"
        elif "owned by" in relationship_display:
            relationship_phrase = "owned by"
        elif "rules" in relationship_display:
            relationship_phrase = "ruled by"
        elif "contains" in relationship_display or "has" in relationship_display:
            relationship_phrase = "contains"
        else:
            # Default case - use 'connected to' for unclear relationships
            relationship_phrase = "connected to"
            
        # Format the question with proper entity display and grammatical relationship
        question_text = template["template"].format(
            entity=display_entity,
            relationship_type=relationship_phrase
        )
        
        # Create the question object
        question = {
            "text": question_text,
            "type": template_type,
            "difficulty": template["difficulty"],
            "template_id": template["id"],
            "entity": entity_name,
            "relationship_type": relationship_type,
            "options": options,
            "correct_answer": correct_answer,
            "community_id": community_id
        }
        
        return question


class SynthesisQuestionGenerator(QuestionGenerator):
    """Generator for synthesis questions that span multiple communities."""
    
    def generate_question(self, 
                         template_type: str = "synthesis", 
                         difficulty: int = 7,
                         entity_data: Optional[Dict[str, Any]] = None,
                         community_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a synthesis question that spans multiple communities.
        
        Args:
            template_type: Type of template to use (default: "synthesis")
            difficulty: Target difficulty level (1-10)
            entity_data: Optional entity data to use for the question
            community_id: Optional community ID to use for the question
            
        Returns:
            Dictionary containing the generated question
        """
        # For synthesis questions, we need entities from different communities
        # First, get available communities
        communities = get_available_communities()
        if len(communities) < 2:
            raise ValueError("Need at least 2 communities for synthesis questions")
        
        # Select two different communities
        if community_id is not None:
            # Use the specified community as one of the two
            community1_id = community_id
            other_communities = [c["id"] for c in communities if c["id"] != community_id]
            if not other_communities:
                raise ValueError("No other communities available for synthesis question")
            community2_id = random.choice(other_communities)
        else:
            # Select two random communities
            selected_communities = random.sample([c["id"] for c in communities], 2)
            community1_id, community2_id = selected_communities
        
        # Get entities from each community
        entities1 = get_entities_in_community(community1_id)
        entities2 = get_entities_in_community(community2_id)
        
        if not entities1 or not entities2:
            raise ValueError("Not enough entities in the selected communities")
        
        # Select a random entity from each community
        entity1 = random.choice(entities1)
        entity2 = random.choice(entities2)
        
        entity1_name = entity1["name"]
        entity2_name = entity2["name"]
        
        # Get a template of the appropriate type and difficulty
        template = self.get_template_by_type_and_difficulty(
            template_type, difficulty
        )
        
        if not template:
            raise ValueError(f"No suitable template found for type {template_type} and difficulty {difficulty}")
        
        # Format the question template
        question_text = template["template"].format(
            entity1=entity1_name,
            entity2=entity2_name
        )
        
        # For synthesis questions, the answer is more complex and would typically
        # be evaluated by an LLM rather than having a simple correct answer
        
        # Create the question object
        question = {
            "text": question_text,
            "type": template_type,
            "difficulty": template["difficulty"],
            "template_id": template["id"],
            "entity1": entity1_name,
            "entity2": entity2_name,
            "community1_id": community1_id,
            "community2_id": community2_id,
            "requires_llm_evaluation": True
        }
        
        return question


class ApplicationQuestionGenerator(QuestionGenerator):
    """Generator for application questions that require creative thinking."""
    
    def generate_question(self, 
                         template_type: str = "application", 
                         difficulty: int = 8,
                         entity_data: Optional[Dict[str, Any]] = None,
                         community_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate an application question that requires creative thinking.
        
        Args:
            template_type: Type of template to use (default: "application")
            difficulty: Target difficulty level (1-10)
            entity_data: Optional entity data to use for the question
            community_id: Optional community ID to use for the question
            
        Returns:
            Dictionary containing the generated question
        """
        # For application questions, we often want entities that don't normally interact
        # First, get available communities
        communities = get_available_communities()
        
        # Select a community (either the specified one or a random one)
        if community_id is not None:
            selected_community_id = community_id
        else:
            selected_community = random.choice(communities)
            selected_community_id = selected_community["id"]
        
        # Get entities from the community
        entities = get_entities_in_community(selected_community_id)
        
        if len(entities) < 2:
            raise ValueError("Not enough entities in the selected community")
        
        # Select two different entities
        entity1, entity2 = random.sample(entities, 2)
        
        entity1_name = entity1["name"]
        entity2_name = entity2["name"]
        
        # Get a template of the appropriate type and difficulty
        template = self.get_template_by_type_and_difficulty(
            template_type, difficulty
        )
        
        if not template:
            raise ValueError(f"No suitable template found for type {template_type} and difficulty {difficulty}")
        
        # Format the question template
        question_text = template["template"].format(
            entity1=entity1_name,
            entity2=entity2_name
        )
        
        # For application questions, the answer requires creative thinking
        # and would typically be evaluated by an LLM
        
        # Create the question object
        question = {
            "text": question_text,
            "type": template_type,
            "difficulty": template["difficulty"],
            "template_id": template["id"],
            "entity1": entity1_name,
            "entity2": entity2_name,
            "community_id": selected_community_id,
            "requires_llm_evaluation": True
        }
        
        return question


class QuestionGeneratorFactory:
    """Factory for creating question generators of different types."""
    
    @staticmethod
    def create_generator(question_type: str) -> QuestionGenerator:
        """
        Create a question generator of the specified type.
        
        Args:
            question_type: Type of question generator to create
            
        Returns:
            QuestionGenerator instance
        """
        generators = {
            "factual": FactualQuestionGenerator,
            "relationship": RelationshipQuestionGenerator,
            "multiple_choice": MultipleChoiceQuestionGenerator,
            "synthesis": SynthesisQuestionGenerator,
            "application": ApplicationQuestionGenerator
        }
        
        if question_type not in generators:
            raise ValueError(f"Unknown question type: {question_type}")
        
        return generators[question_type]()


def generate_question(question_type: str, 
                     difficulty: int = None, 
                     community_id: int = None,
                     recursion_depth: int = 0) -> Dict[str, Any]:
    """
    Generate a question of the specified type and difficulty.
    
    Args:
        question_type (str): Type of question to generate (factual, relationship, etc.)
        difficulty (int, optional): Difficulty level (1-10). Defaults to None.
        community_id (int, optional): Community ID to focus on. Defaults to None.
        
    Returns:
        Dict[str, Any]: Question object with text, answer, etc.
    """
    # Create the appropriate question generator
    generator = QuestionGeneratorFactory.create_generator(question_type)
    
    if generator is None:
        logger.error(f"Unknown question type: {question_type}")
        return None
    
    # Generate the question
    question = generator.generate_question(difficulty=difficulty, community_id=community_id)
    
    # Check recursion depth to prevent infinite recursion
    if recursion_depth >= 5:
        logger.warning(f"Maximum recursion depth reached for question generation of type {question_type}")
        return None
        
    # Filter out questions about communities or technical IDs
    if question and "text" in question:
        if ("community id" in question["text"].lower() or 
            "belongs to community" in question["text"].lower() or
            "id" in question["text"].lower() or
            "identifier" in question["text"].lower() or
            "none" in question["text"].lower()):
            # Try to generate a different question instead
            logger.info("Filtering out technical question about communities, IDs, or containing None values")
            return generate_question(question_type, difficulty, community_id, recursion_depth + 1)
    
    # Check for None values in the question or answer
    if question:
        if "text" in question and (question["text"] is None or "None" in question["text"]):
            logger.info("Filtering out question with None in text")
            return generate_question(question_type, difficulty, community_id, recursion_depth + 1)
        
        if "answer" in question and (question["answer"] is None or (isinstance(question["answer"], str) and "None" in question["answer"])):
            logger.info("Filtering out question with None in answer")
            return generate_question(question_type, difficulty, community_id, recursion_depth + 1)
        
        if "options" in question and any(opt is None or "None" in str(opt) for opt in question["options"]):
            logger.info("Filtering out question with None in options")
            return generate_question(question_type, difficulty, community_id, recursion_depth + 1)
        
        # If we still have a question with None values, create a generic lore question
        if ("text" in question and "None" in question["text"]) or \
           ("answer" in question and isinstance(question["answer"], str) and "None" in question["answer"]) or \
           ("options" in question and any(isinstance(opt, str) and "None" in opt for opt in question["options"])):
            
            entity_name = question.get("entity", "Unknown entity")
            if entity_name == "None" or entity_name is None:
                entity_name = "this mysterious element"
                
            question["text"] = f"What significance does {entity_name} hold in the lore of Middle-earth?"
            if "answer" in question:
                question["answer"] = f"The significance of {entity_name} is revealed through its connections to other elements of Middle-earth's history."
    
    return question


def main():
    """Main function to generate questions for testing."""
    parser = argparse.ArgumentParser(description="Generate questions for adaptive quizzing")
    parser.add_argument("--type", choices=["factual", "relationship", "multiple_choice", "synthesis", "application"],
                       default="factual", help="Type of question to generate")
    parser.add_argument("--difficulty", type=int, choices=range(1, 11),
                       help="Difficulty level (1-10)")
    parser.add_argument("--community", type=int,
                       help="Community ID to use for the question")
    parser.add_argument("--count", type=int, default=1,
                       help="Number of questions to generate")
    args = parser.parse_args()
    
    for i in range(args.count):
        try:
            question = generate_question(
                question_type=args.type,
                difficulty=args.difficulty,
                community_id=args.community
            )
            
            print(f"\nQuestion {i+1}:")
            print(f"Text: {question['text']}")
            print(f"Type: {question['type']}")
            print(f"Difficulty: {question['difficulty']}")
            
            if "options" in question:
                print(f"Options: {question['options']}")
                print(f"Correct Answer: {question['correct_answer']}")
            elif "answer" in question:
                print(f"Answer: {question['answer']}")
            else:
                print("This question requires LLM evaluation.")
            
            print(f"Community ID: {question.get('community_id')}")
        except Exception as e:
            logger.error(f"Failed to generate question: {e}")

if __name__ == "__main__":
    main()
