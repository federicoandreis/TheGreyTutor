import os
import logging
import glob
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from neo4j import GraphDatabase
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm.openai_llm import OpenAILLM
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Configuration from environment variables
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')

# Tolkien-specific schema for Middle-earth entities
ENTITIES = [
    {
        "label": "Character",
        "description": "Any named individual in Middle-earth including humans, elves, dwarves, hobbits, wizards, and other sentient beings",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "race", "type": "STRING"},
            {"name": "title", "type": "STRING"},
            {"name": "status", "type": "STRING"},
            {"name": "home_region", "type": "STRING"}
        ]
    },
    {
        "label": "Location",
        "description": "Any named place in Middle-earth including realms, cities, regions, mountains, rivers, forests, and landmarks",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "location_type", "type": "STRING"},
            {"name": "region", "type": "STRING"},
            {"name": "significance", "type": "STRING"}
        ]
    },
    {
        "label": "Artifact",
        "description": "Significant objects including rings, weapons, jewelry, books, and other items of power or importance",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "artifact_type", "type": "STRING"},
            {"name": "material", "type": "STRING"},
            {"name": "powers", "type": "STRING"},
            {"name": "current_status", "type": "STRING"}
        ]
    },
    {
        "label": "Organization",
        "description": "Groups, kingdoms, fellowships, armies, councils, and other collective entities",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "organization_type", "type": "STRING"},
            {"name": "purpose", "type": "STRING"},
            {"name": "status", "type": "STRING"}
        ]
    },
    {
        "label": "Event",
        "description": "Significant occurrences including battles, councils, journeys, and other notable happenings",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "event_type", "type": "STRING"},
            {"name": "age", "type": "STRING"},
            {"name": "outcome", "type": "STRING"},
            {"name": "significance", "type": "STRING"}
        ]
    }
]

RELATIONS = [
    {"label": "PARENT_OF", "description": "Direct parent-child relationship"},
    {"label": "CHILD_OF", "description": "Direct child-parent relationship"},
    {"label": "MARRIED_TO", "description": "Spouse relationship"},
    {"label": "RULES", "description": "Governs or has authority over a location or organization"},
    {"label": "SERVES", "description": "Serves under or works for another entity"},
    {"label": "ALLIES_WITH", "description": "Allied or friendly relationship"},
    {"label": "OPPOSES", "description": "Enemy or antagonistic relationship"},
    {"label": "MEMBER_OF", "description": "Belongs to or is part of an organization"},
    {"label": "LEADS", "description": "Commands or directs an organization or group"},
    {"label": "LOCATED_IN", "description": "Is situated within or part of a larger location"},
    {"label": "DWELLS_IN", "description": "Lives or resides in a location"},
    {"label": "TRAVELS_TO", "description": "Journeys or moves to a location"},
    {"label": "OWNS", "description": "Possesses or has ownership of an artifact"},
    {"label": "WIELDS", "description": "Uses or carries an artifact, especially weapons"},
    {"label": "CREATES", "description": "Makes or forges an artifact"},
    {"label": "PARTICIPATES_IN", "description": "Takes part in an event"},
    {"label": "TAKES_PLACE_IN", "description": "Event or action that occurs at a specific location"},
    {"label": "MENTORS", "description": "Teaches, guides, or advises another character"},
    {"label": "KNOWS_ABOUT", "description": "Has knowledge or information about another entity"},
    {"label": "CREATED_BY", "description": "Was made or forged by another entity"}
]

POTENTIAL_SCHEMA = [
    ("Character", "PARENT_OF", "Character"),
    ("Character", "MARRIED_TO", "Character"),
    ("Character", "SERVES", "Character"),
    ("Character", "ALLIES_WITH", "Character"),
    ("Character", "OPPOSES", "Character"),
    ("Character", "MENTORS", "Character"),
    ("Character", "RULES", "Location"),
    ("Character", "DWELLS_IN", "Location"),
    ("Character", "TRAVELS_TO", "Location"),
    ("Character", "OWNS", "Artifact"),
    ("Character", "WIELDS", "Artifact"),
    ("Character", "CREATES", "Artifact"),
    ("Character", "MEMBER_OF", "Organization"),
    ("Character", "LEADS", "Organization"),
    ("Character", "PARTICIPATES_IN", "Event"),
    ("Location", "LOCATED_IN", "Location"),
    ("Organization", "LOCATED_IN", "Location"),
    ("Organization", "ALLIES_WITH", "Organization"),
    ("Organization", "OPPOSES", "Organization"),
    ("Organization", "PARTICIPATES_IN", "Event"),
    ("Event", "TAKES_PLACE_IN", "Location"),
    ("Artifact", "LOCATED_IN", "Location"),
    ("Artifact", "CREATED_BY", "Character")
]

def detect_communities(driver):
    """Run community detection on the knowledge graph."""
    logging.info("Running community detection...")
    
    with driver.session() as session:
        # First, create a projection of the entity graph
        try:
            session.run("""
                CALL gds.graph.drop('entity-graph', false)
            """)
        except:
            pass  # Graph doesn't exist yet
        
        # Create graph projection including all entity nodes and their relationships
        session.run("""
            CALL gds.graph.project(
                'entity-graph',
                ['Character', 'Location', 'Artifact', 'Organization', 'Event'],
                {
                    MEMBER_OF: {orientation: 'UNDIRECTED'},
                    KNOWS_ABOUT: {orientation: 'UNDIRECTED'},
                    ALLIES_WITH: {orientation: 'UNDIRECTED'},
                    OPPOSES: {orientation: 'UNDIRECTED'},
                    DWELLS_IN: {orientation: 'UNDIRECTED'},
                    RULES: {orientation: 'UNDIRECTED'},
                    SERVES: {orientation: 'UNDIRECTED'},
                    LEADS: {orientation: 'UNDIRECTED'},
                    PARTICIPATES_IN: {orientation: 'UNDIRECTED'},
                    LOCATED_IN: {orientation: 'UNDIRECTED'}
                }
            )
        """)
        
        # Run Louvain community detection
        result = session.run("""
            CALL gds.louvain.write('entity-graph', {
                writeProperty: 'community_id'
            })
            YIELD communityCount, modularity
            RETURN communityCount, modularity
        """)
        
        community_stats = result.single()
        logging.info(f"Detected {community_stats['communityCount']} communities with modularity {community_stats['modularity']:.3f}")
        
        # Create Community nodes and relationships
        session.run("""
            MATCH (n) WHERE n.community_id IS NOT NULL
            WITH DISTINCT n.community_id AS communityId
            CREATE (c:Community {id: communityId, name: 'Community ' + toString(communityId)})
        """)
        
        session.run("""
            MATCH (n) WHERE n.community_id IS NOT NULL
            MATCH (c:Community {id: n.community_id})
            CREATE (n)-[:BELONGS_TO_COMMUNITY]->(c)
        """)
        
        # Clean up the graph projection
        session.run("CALL gds.graph.drop('entity-graph')")
        
        logging.info("Community detection completed successfully")

def main():
    """Main function to run the Neo4j GraphRAG pipeline for Tolkien lore ingestion."""
    
    # Initialize Neo4j driver
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    # Initialize LLM and embedder with environment-specified models
    llm = OpenAILLM(model_name=LLM_MODEL)
    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    text_splitter = FixedSizeSplitter(chunk_size=500, chunk_overlap=100)
    
    logging.info(f"Using LLM model: {LLM_MODEL}")
    logging.info(f"Using embedding model: {EMBEDDING_MODEL}")
    
    # Create the pipeline with simplified configuration
    pipeline = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        entities=ENTITIES,
        relations=RELATIONS,
        potential_schema=POTENTIAL_SCHEMA,
        text_splitter=text_splitter,
        perform_entity_resolution=True,
        neo4j_database="neo4j",
        from_pdf=False,
    )
    
    # Get list of input files
    file_list = glob.glob("input/*.txt")
    if not file_list:
        logging.warning("No .txt files found in input/ directory")
        return
    
    # Set up progress bar if available
    iterator = tqdm(file_list, desc="Ingesting files", unit="file") if tqdm else file_list
    
    # Process each file
    for file_path in iterator:
        logging.info(f"\n---\n[START] Ingesting: {file_path}")
        
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            logging.info("[STEP] Running pipeline on file...")
            
            # Run the pipeline asynchronously
            result = asyncio.run(pipeline.run_async(text=text))
            
            logging.info("[DONE] File ingested successfully.")
            logging.info(f"Pipeline result: {result}")
            
        except Exception as e:
            logging.error(f"[ERROR] Ingestion failed for {file_path}: {e}")
            continue
    
    # After processing all files, run community detection
    try:
        detect_communities(driver)
    except Exception as e:
        logging.error(f"[ERROR] Community detection failed: {e}")
        logging.info("Continuing without community detection...")
    
    logging.info("\nAll files processed. Check Neo4j for your knowledge graph.")
    driver.close()

if __name__ == "__main__":
    main()
