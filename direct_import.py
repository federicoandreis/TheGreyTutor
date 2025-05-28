import os
import asyncio
import logging
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load environment variables
load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

# Import the OpenAI LLM
from neo4j_graphrag.llm.openai_llm import OpenAILLM
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings

# Import schema from prompting_example
def safe_import_prompting_example():
    import importlib.util, sys
    path = os.path.join(os.path.dirname(__file__), 'prompting_example.py')
    spec = importlib.util.spec_from_file_location('prompting_example', path)
    prompting_example = importlib.util.module_from_spec(spec)
    sys.modules['prompting_example'] = prompting_example
    spec.loader.exec_module(prompting_example)
    return prompting_example

prompting_example = safe_import_prompting_example()
ENTITIES = prompting_example.ENTITIES
RELATIONS = prompting_example.RELATIONS
CUSTOM_PROMPT = prompting_example.CUSTOM_PROMPT

# LLM setup
llm = OpenAILLM(model_name="gpt-3.5-turbo")

# Simple extraction function without Neo4j GraphRAG
async def extract_entities_from_text(text):
    """Extract entities directly using the LLM without Neo4j GraphRAG pipeline"""
    
    # Create a schema prompt for the LLM
    schema_prompt = "Extract entities from the text according to this schema:\n"
    for entity in ENTITIES:
        schema_prompt += f"\n- {entity['label']}: {entity['description']}\n  Properties: "
        for prop in entity['properties']:
            schema_prompt += f"{prop['name']} ({prop['type']}), "
    
    # Create the full prompt
    prompt = f"""
{schema_prompt}

Extract entities from the following text. For each entity, provide its type (from the schema above) and properties:

TEXT:
{text}

Return the results as a JSON object with the following structure:
{{
  "entities": [
    {{
      "entity_type": "Entity Type Name",
      "properties": {{
        "property_name": "property_value",
        ...
      }}
    }},
    ...
  ]
}}

Only include properties mentioned in the text. If a property is not mentioned, omit it.
"""
    
    # Call the LLM
    response = await llm.ainvoke(prompt)
    
    # Parse the response
    try:
        result = json.loads(response.content)
        return result
    except json.JSONDecodeError:
        logging.error(f"Failed to parse LLM response as JSON: {response.content}")
        return {"entities": []}

# Create Neo4j Cypher queries from extracted entities
def create_cypher_queries(entities):
    """Create Cypher queries to insert entities into Neo4j"""
    queries = []
    
    for entity in entities:
        entity_type = entity.get('entity_type')
        if not entity_type:
            continue
            
        # Escape properties for Cypher
        props = {}
        for key, value in entity.get('properties', {}).items():
            if value is not None:
                props[key] = value
        
        # Create the Cypher query
        props_string = ", ".join([f"{k}: '{v.replace("'", "\\'")}'" for k, v in props.items()])
        query = f"CREATE (e:{entity_type} {{{props_string}}})"
        queries.append(query)
    
    return queries

# Insert entities into Neo4j
def insert_into_neo4j(queries):
    """Execute Cypher queries to insert entities into Neo4j"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    session = driver.session()
    
    try:
        for query in queries:
            session.run(query)
        logging.info(f"Successfully inserted {len(queries)} entities into Neo4j")
    except Exception as e:
        logging.error(f"Failed to insert entities into Neo4j: {e}")
    finally:
        session.close()
        driver.close()

async def main():
    # Process each file in the input directory
    import glob
    file_list = glob.glob("input/*.txt")
    
    for file_path in file_list:
        logging.info(f"Processing {file_path}")
        
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Extract entities
        result = await extract_entities_from_text(text)
        
        # Log the extracted entities
        entities = result.get('entities', [])
        logging.info(f"Extracted {len(entities)} entities from {file_path}")
        
        if entities:
            # Create and execute Cypher queries
            queries = create_cypher_queries(entities)
            insert_into_neo4j(queries)

if __name__ == "__main__":
    asyncio.run(main())
