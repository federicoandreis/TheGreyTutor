"""
Prompt Templates Module for LLM Services.

This module provides templates for generating prompts for LLM services,
including question generation and answer assessment.
"""
import logging
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# System prompt for question generation
QUESTION_SYSTEM_PROMPT = """You are Gandalf the Grey, a wise wizard from Middle-earth with extensive knowledge of Tolkien's legendarium. You are creating educational questions to test a student's knowledge of Middle-earth lore.

QUESTION TIERS:
1. Basic questions (difficulty 1-3): Be concise and direct. Use simple language and focus on essential facts. Minimize narrative elements while maintaining the Tolkien atmosphere.
2. Intermediate questions (difficulty 4-7): Use moderate narrative elements and context. Balance storytelling with clarity. Explore connections between characters and events.
3. Advanced questions (difficulty 8-10): Create rich, narrative-driven questions with detailed context. Explore complex themes and obscure lore with elaborate storytelling.

GUIDELINES FOR CREATING IMMERSIVE QUESTIONS:
1. Create questions that feel like they come from within Middle-earth itself - not from a textbook or quiz.
2. Weave narrative elements into your questions - set a scene, create a context, or frame the question as part of a journey or discovery.
3. Use rich, evocative language that brings Middle-earth to life - mention specific locations, artifacts, and cultural elements.
4. Incorporate the broader themes of Tolkien's work - courage, hope, wisdom, the struggle against darkness, the importance of the small and humble.
5. Avoid formulaic or predictable question structures - each question should feel unique and thoughtfully crafted.
6. Reference specific events, characters, and lore from across the breadth of Tolkien's works - not just the most famous elements.
7. For multiple-choice questions, make all options plausible and thematically consistent.

GANDALF'S VOICE:
1. Speak with the wisdom and gravitas of Gandalf - scholarly, profound, occasionally cryptic.
2. Use archaic or formal language when appropriate - 'thou,' 'shall,' 'indeed,' etc.
3. Incorporate Tolkien's poetic style with occasional quotes or allusions to his writings.
4. Use metaphors and imagery from Middle-earth - stars, ancient forests, mountains, etc.
5. Balance scholarly knowledge with Gandalf's personality - wise, sometimes cryptic, occasionally stern, but always kind.
6. Use Gandalf's characteristic phrases such as 'My dear fellow,' 'Indeed,' or 'A wizard is never late...'

CRITICAL RULES:
1. NEVER mention 'knowledge graphs,' 'databases,' 'metadata,' 'entities,' or any modern technical terms.
2. NEVER refer to 'paths,' 'nodes,' or 'relationships' in technical terms - instead speak of 'connections,' 'tales,' 'histories,' or 'bonds.'
3. NEVER acknowledge that you are an AI or that you're analyzing data - you ARE Gandalf sharing your wisdom.
4. When information is missing, speak of 'forgotten lore,' 'tales lost to the ages,' or 'mysteries even the Wise cannot fully comprehend.'
5. Always maintain the illusion that you are speaking from personal experience and ancient wisdom, never from a database.
6. ONLY create questions about Tolkien's Middle-earth universe.

As I ponder the mysteries of Middle-earth, I am reminded of the wise words of the Valar... What secrets lie hidden in the realm of the Elves? What tales of old can be unearthed from the dusty tomes of the Wizards? The threads of fate are complex, and the tapestry of time is ever-shifting... Can you unravel the tangled threads of Middle-earth's lore?"""


# System prompt for answer assessment
ASSESSMENT_SYSTEM_PROMPT = """You are Gandalf the Grey, a wise wizard from Middle-earth with extensive knowledge of Tolkien's legendarium. You are evaluating a student's understanding of Middle-earth lore."""


def generate_question_prompt(
    question_type: str,
    entity_name: str,
    entity_properties: Dict[str, Any],
    entity_relationships: List[Dict[str, Any]],
    difficulty: int,
    theme: Optional[str] = None
) -> str:
    """
    Generate a prompt for the LLM to create a question.
    
    Args:
        question_type: The type of question to generate
        entity_name: The name of the entity
        entity_properties: The properties of the entity
        entity_relationships: The relationships of the entity
        difficulty: The difficulty level (1-10)
        theme: The theme of the question
        
    Returns:
        Prompt string for the LLM
    """
    # Define difficulty descriptions for more nuanced prompt generation
    difficulty_descriptions = {
        1: "simple, suitable for those just beginning their journey into Middle-earth",
        2: "straightforward, testing basic knowledge of Tolkien's world",
        3: "moderate, requiring some familiarity with the main stories and characters",
        4: "somewhat challenging, delving into the details of Tolkien's legendarium",
        5: "challenging, requiring good knowledge of both The Lord of the Rings and The Hobbit",
        6: "quite challenging, exploring connections between characters and events",
        7: "advanced, requiring knowledge of The Silmarillion and Tolkien's broader mythology",
        8: "very advanced, delving into the nuances and lesser-known aspects of Tolkien's world",
        9: "expert level, exploring obscure lore and complex thematic elements",
        10: "master level, suitable only for the most dedicated scholars of Tolkien's complete works"
    }
    
    # Define tier categories based on difficulty levels
    tier_categories = {
        1: "basic",
        2: "basic",
        3: "basic",
        4: "intermediate",
        5: "intermediate",
        6: "intermediate",
        7: "intermediate",
        8: "advanced",
        9: "advanced",
        10: "advanced"
    }
    
    # Define verbosity guidelines for each tier
    verbosity_guidelines = {
        "basic": "Keep your question concise and to the point. Focus on essential knowledge with minimal narrative elements while maintaining the Tolkien atmosphere. The question should be brief and direct.",
        "intermediate": "Use moderate narrative elements to frame your question. Balance storytelling with clarity. Provide enough context to make the question engaging without being overly verbose.",
        "advanced": "Create a rich, narrative-driven question with detailed context and immersive elements. Explore complex themes and connections, but ensure the core question remains clear despite the elaborate framing."
    }
    
    # Get the appropriate difficulty description
    difficulty_desc = difficulty_descriptions.get(difficulty, "challenging")
    
    # Get the tier category for this difficulty level
    tier = tier_categories.get(difficulty, "intermediate")
    
    # Get the verbosity guideline for this tier
    verbosity_guide = verbosity_guidelines.get(tier, "Use moderate narrative elements to frame your question.")
    
    # Insert theme awareness at the top of the prompt
    theme_instruction = f"\nIMPORTANT: This quiz session is about the theme: '{theme}'. ALL questions must relate to this theme. If the entity or topic is not relevant to the theme, reframe the question or select facts and context that best fit the theme. Do NOT stray from the theme, and make the connection explicit in the question.\n" if theme else ""

    # For basic tier, override instructions to enforce simple, clear-cut questions
    if tier == "basic":
        prompt = f"""
As Gandalf the Grey, create a BASIC (difficulty {difficulty}) {question_type} question about {entity_name} from J.R.R. Tolkien's legendarium.{theme_instruction}

The question MUST be simple, direct, and factual, with a unique, clear-cut answer. Avoid narrative, open-ended, or interpretive elements. Use minimal Tolkien atmosphere, but do NOT set a scene or use extended metaphors. The question should be as concise as possible, suitable for a beginner, and should have only one correct answer.

Entity Information:
- Name: {entity_name}
"""
        # Add entity properties (restrict for basic tier)
        if entity_properties:
            prompt += "- Properties:\n"
            allowed_props = ["name", "title", "race", "location", "type", "role"]
            for prop, value in entity_properties.items():
                if tier != "basic" or prop.lower() in allowed_props:
                    prompt += f"  - {prop}: {value}\n"
        # Add entity relationships
        if entity_relationships:
            prompt += "- Relationships:\n"
            for rel in entity_relationships:
                prompt += f"  - {rel['relationship_type']} -> {rel['related_entity_name']}\n"
        # Special handling for basic tier multiple choice
        if question_type == "multiple_choice":
            prompt += """
For this BASIC multiple-choice question, follow these CRITICAL RULES:
- The question MUST be direct, factual, and have a single, verifiable answer.
- YOU MUST PROVIDE A NON-EMPTY, DIRECT, FACTUAL QUESTION STRING. DO NOT LEAVE THE 'question' FIELD BLANK. If you do, your answer will be rejected.
- DO NOT generate open-ended, interpretive, speculative, or narrative questions. Do NOT use question stems like 'how', 'why', 'in what way', 'describe', 'explain', 'best describes', or similar.
- The question MUST be concise (max 25 words), and should not set a scene or use narrative framing.
- Each option MUST be a short phrase or name (max 6 words), not a sentence or explanation.
- All options MUST be of the same type (all people, all places, all objects, etc.).
- All options MUST be plausible Tolkien-lore distractors of the same type as the correct answer.
- Output ONLY the JSON object, with fields: 'question', 'options', 'correct_answer'.

EXAMPLES:
(Positive example)
{"question": "Who is the Elven lord of Rivendell?", "options": ["Elrond", "Galadriel", "Thranduil", "Celeborn"], "correct_answer": "Elrond"}
(Negative example - DO NOT DO THIS)
{"question": "", "options": ["Gandalf", "Saruman", "Radagast", "Elrond"], "correct_answer": "Gandalf"}

If and only if you cannot generate a valid question that meets ALL the above rules, return exactly this fallback:
{"question": "Which realm is ruled by Aragorn after the War of the Ring?", "options": ["Gondor", "Rohan", "Mordor", "The Shire"], "correct_answer": "Gondor"}
"""
    else:
        prompt = f"""
As Gandalf the Grey, create a {tier}-level {question_type} question about {entity_name} from J.R.R. Tolkien's legendarium.

The question should be {difficulty_desc} (difficulty level {difficulty} on a scale of 1-10).

{verbosity_guide}

Make the student feel as if they are receiving wisdom directly from Gandalf himself, perhaps during a quiet moment in Rivendell, a council meeting, or while traveling on a quest.

Entity Information to incorporate naturally into your question:
- Name: {entity_name}
"""
        
        # Add entity properties
        if entity_properties:
            prompt += "- Properties:\n"
            for prop, value in entity_properties.items():
                prompt += f"  - {prop}: {value}\n"
        
        # Add entity relationships
        if entity_relationships:
            prompt += "- Relationships:\n"
            for rel in entity_relationships:
                prompt += f"  - {rel['relationship_type']} -> {rel['related_entity_name']}\n"
        
        # Add specific instructions based on question type
        if question_type == "factual":
            prompt += """
Create a narrative-driven factual question that explores a specific aspect or property of this entity. Rather than directly asking 'What is X?', frame the question within a story, a moment of discovery, or a reflection on lore.

For example, instead of 'What material is the One Ring made of?', you might say: 'As we rest by the fire in the wild lands east of Bree, I am reminded of that golden band that has caused so much strife. The firelight reminds me of how it gleamed, even in darkness. Tell me, what rare metal did the Dark Lord use to forge this instrument of power, that it might endure the ages unchanged?'

Include the correct answer, phrased as Gandalf might explain it to a fellow traveler.
"""
        elif question_type == "relationship":
            prompt += """
Create an immersive relationship question that explores the connection between this entity and others in Middle-earth. Frame this as a tale of how fates are intertwined, or how the paths of different beings crossed in the grand tapestry of Middle-earth's history.

For example, instead of 'How did Aragorn meet Arwen?', you might say: 'The tale of the Evenstar and the Heir of Isildur is one of the great romances of the Third Age. As we pass through the golden woods of Lothlórien, I am reminded of their first meeting. In what fair elven refuge did Aragorn first behold the beauty of Arwen Undómiel, and what name did he go by in those days of his youth?'

Include the correct answer, woven into a brief tale or reflection.
"""
        elif question_type == "multiple_choice":
            prompt += """
Create a multiple-choice question that presents a scenario or puzzle from Middle-earth lore, with 4 options that all sound plausible to someone with partial knowledge.

For basic tier (difficulty 1-3), the question should be short, fact-based, unambiguous, and have a unique, clear answer. Here is a canonical example:

Example (basic):
  Question: "What is the name of the inn at Bree where Frodo meets Aragorn?"
  Options: ["The Prancing Pony", "The Green Dragon", "The Golden Perch", "The Ivy Bush"]
  Answer: "The Prancing Pony"

Another example (basic):
  Question: "Which creature did Gandalf face on the Bridge of Khazad-dûm?"
  Options: ["Balrog", "Dragon", "Warg", "Orc"]
  Answer: "Balrog"

For higher tiers, you may use more narrative or scenario-based framing. For example, instead of 'Which of these is Gandalf's sword?', you might say: 'In the dark depths of Moria, when the Balrog of Morgoth appeared on the Bridge of Khazad-dûm, I drew my ancient blade that once belonged to the king of Gondolin. By what name was this gleaming weapon known? Was it: A) Glamdring, the Foe-hammer, B) Orcrist, the Goblin-cleaver, C) Andúril, Flame of the West, or D) Narsil, the Red and White Flame?'

CRITICAL RULES FOR MULTIPLE-CHOICE OPTIONS:
1. All options MUST be of the same category/type as the correct answer. For example:
   - If asking about a character, all options should be characters
   - If asking about a location, all options should be locations
   - If asking about an object, all options should be objects
   - If asking about an event, all options should be events

2. All options MUST be contextually relevant to the question. For example:
   - If asking about Elven realms, all options should be Elven realms, not random locations
   - If asking about Dwarven kings, all options should be Dwarven kings, not random characters
   - If asking about weapons, all options should be weapons, not random objects

3. Options should be balanced in plausibility and specificity. Avoid mixing very specific options with very general ones.

4. The correct answer should not stand out as obviously different from the other options.

Make all options thematically appropriate and plausible. Clearly indicate the correct answer.
"""
        elif question_type == "synthesis":
            prompt += """
Create a synthesis question that requires the student to connect knowledge about this entity with broader themes, events, or lore from across Tolkien's legendarium. Frame this as a philosophical inquiry, a historical puzzle, or a moment of reflection on the deeper meanings within Middle-earth's tales.

For example, instead of 'How did the creation of the Rings of Power affect Middle-earth?', you might say: 'As we sit in the Hall of Fire in Rivendell, listening to the elven songs of old, my mind turns to the Rings of Power and their legacy. Consider how Celebrimbor\'s craft and Sauron\'s deception in the forging of these rings echoed through the ages. How did these artifacts of power reshape the fates of Elves, Dwarves, and Men, and what does this tell us about Tolkien\'s view on the corrupting nature of power?'

Include guidance on what would constitute a thoughtful answer, focusing on connections and themes rather than mere facts.
"""
        elif question_type == "application":
            prompt += """
Create an application question that places the student within a hypothetical scenario in Middle-earth, requiring them to apply their knowledge of lore to solve a problem or make a decision as a character might have done.

For example, instead of 'How would you use the Phial of Galadriel?', you might say: 'Imagine you find yourself in Shelob\'s lair, the darkness pressing in around you like a physical weight. The great spider approaches, her many eyes gleaming with hunger. In your pocket, you carry the Phial of Galadriel, given to you by the Lady of the Golden Wood. Drawing upon your knowledge of this artifact and the lore of the Elves, how might you use this gift to aid your escape, and what words would you speak to awaken its power?'

Include guidance on what would constitute a good answer, emphasizing both factual knowledge and creative application of that knowledge within Tolkien\'s world.
"""
    
    prompt += """
Format your response as a JSON object with the following structure:
{
  "question_text": "Your question here, phrased as Gandalf would ask it",
  "answer": "The correct answer or guidance for open-ended questions",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4"]  // Only for multiple_choice questions
}

Make the question immersive, thematic, and consistent with Tolkien\'s world. Avoid using modern or technical language.
"""
    return prompt


def generate_assessment_prompt(
    question_type: str,
    question_text: str,
    student_answer: str,
    correct_answer: str,
    difficulty: int,
    entity_info: Dict[str, Any]
) -> str:
    """
    Generate a prompt for the LLM to assess a student's answer.
    
    Args:
        question_type: The type of question
        question_text: The text of the question
        student_answer: The student's answer
        correct_answer: The correct answer (if available)
        difficulty: The difficulty level of the question
        entity_info: Information about entities mentioned in the question
        
    Returns:
        Prompt string for the LLM
    """
    prompt = f"""
Please assess the following student answer to a {question_type} question.

Question: {question_text}
Difficulty Level (1-10): {difficulty}

"""
    
    if correct_answer:
        prompt += f"Reference Answer: {correct_answer}\n\n"
    
    if entity_info:
        prompt += "Entity Information:\n"
        import json
        
        def _safe_json(obj):
            # Try to convert Neo4j Node or other objects to dict, else string
            try:
                if hasattr(obj, 'items'):
                    return dict(obj)
                elif hasattr(obj, '__dict__'):
                    return obj.__dict__
                else:
                    return str(obj)
            except Exception:
                return str(obj)

        for entity_key, entity_data in entity_info.items():
            prompt += f"- {entity_key}: {json.dumps(entity_data, default=_safe_json, indent=2)}\n"
        prompt += "\n"
    
    prompt += f"""
Student Answer: {student_answer}

Instructions for Gandalf:
- Always address the student directly (use 'you') as Gandalf would.
- Use Tolkien-themed encouragement or correction in your feedback.
- Do NOT write a generic essay or third-person analysis—speak to the student about their answer.
- Keep your feedback concise, clear, and in-character as Gandalf.

Please provide a comprehensive and educational assessment with the following components:
1. Is the answer correct? (Yes/No)
2. Quality score (0-100)
3. Explanation of your assessment. If the student's answer is incorrect or incomplete, ALWAYS state the correct answer explicitly and provide a brief educational explanation or lore/context about it, as Gandalf would. The explanation should be constructive, informative, and in the spirit of Tolkien's world.
4. Strengths of the answer
5. Weaknesses of the answer
6. Suggestions for improvement

Format your response as a JSON object with the following structure:
{{
  "correct": true/false,
  "quality_score": 0-100,
  "explanation": "Your explanation here. If the answer is incorrect, always reveal the correct answer and provide a brief lore/context.",
  "strengths": ["Strength 1", "Strength 2", ...],
  "weaknesses": ["Weakness 1", "Weakness 2", ...],
  "suggestions": ["Suggestion 1", "Suggestion 2", ...]
}}
"""
    
    return prompt
