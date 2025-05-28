import os
import logging
import asyncio
from dotenv import load_dotenv

# Import the main module
import import_to_neo4j

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

async def test_pdf_ingestion():
    """Test function to verify PDF ingestion functionality."""
    
    # Initialize Neo4j driver
    from neo4j import GraphDatabase
    
    # Configuration from environment variables
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
    
    # Initialize driver
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    # Initialize LLM and embedder
    from neo4j_graphrag.llm.openai_llm import OpenAILLM
    from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
    from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
    
    llm = OpenAILLM(model_name=LLM_MODEL)
    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    text_splitter = FixedSizeSplitter(chunk_size=500, chunk_overlap=100)
    
    # Create a PDF-specific pipeline
    from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
    
    pdf_pipeline = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        entities=import_to_neo4j.ENTITIES,
        relations=import_to_neo4j.RELATIONS,
        potential_schema=import_to_neo4j.POTENTIAL_SCHEMA,
        text_splitter=text_splitter,
        perform_entity_resolution=True,
        neo4j_database="neo4j",
        from_pdf=True  # Set to True for PDF processing
    )
    
    # Find PDF files in the input directory
    pdf_files = [f for f in os.listdir("input") if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        logging.warning("No PDF files found in input/ directory")
        return
    
    # Process the first PDF file
    pdf_file = os.path.join("input", pdf_files[0])
    logging.info(f"Testing PDF ingestion with file: {pdf_file}")
    
    try:
        # Verify the file is a PDF
        if import_to_neo4j.is_pdf_file(pdf_file):
            logging.info("File confirmed as PDF")
        else:
            logging.error(f"File {pdf_file} is not detected as a PDF")
            return
        
        # Process the PDF file
        logging.info("Running pipeline on PDF file...")
        result = await pdf_pipeline.run_async(file_path=pdf_file)
        
        logging.info("PDF ingestion test completed successfully")
        logging.info(f"Pipeline result: {result}")
        
    except Exception as e:
        logging.error(f"PDF ingestion test failed: {e}")
    
    finally:
        # Close the driver
        driver.close()

if __name__ == "__main__":
    asyncio.run(test_pdf_ingestion())
