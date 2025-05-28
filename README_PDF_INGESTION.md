# Tolkien Knowledge Graph - PDF Ingestion

This document explains how to use the updated `import_to_neo4j.py` script to ingest both text and PDF files into a Neo4j knowledge graph.

## Overview

The system has been enhanced to support both text (.txt) and PDF (.pdf) files. The script automatically detects the file type and processes it accordingly:

- Text files are read directly and their content is passed to the knowledge graph pipeline
- PDF files are processed using the PDF extraction capabilities of the Neo4j GraphRAG library

## Requirements

- Python 3.8+
- Neo4j database (running locally or remotely)
- OpenAI API key (for LLM and embeddings)
- Required Python packages:
  - neo4j
  - neo4j-graphrag
  - openai
  - python-dotenv
  - tqdm (optional, for progress bars)

## Configuration

Create a `.env` file in the project root with the following variables:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your_openai_api_key
```

## File Organization

Place your input files in the `input/` directory:
- Text files should have a `.txt` extension
- PDF files should have a `.pdf` extension

The script will automatically detect and process all files in this directory.

## Running the Ingestion

To ingest all files (both text and PDF):

```bash
python import_to_neo4j.py
```

To test PDF ingestion specifically:

```bash
python test_pdf_ingestion.py
```

## How It Works

1. The script scans the `input/` directory for both `.txt` and `.pdf` files
2. For each file:
   - It determines the file type using extension and content analysis
   - For text files, it reads the content and passes it to the pipeline
   - For PDF files, it creates a PDF-specific pipeline with `from_pdf=True` and passes the file path
3. After ingestion, it performs:
   - Entity resolution to merge duplicate entities
   - Community detection to identify related entities
   - Community summarization to provide context

## PDF Processing Details

When processing PDF files:

1. The `from_pdf=True` parameter tells the GraphRAG pipeline to use its built-in PDF extraction capabilities
2. The pipeline is called with `file_path` instead of `text` parameter
3. The PDF extraction handles:
   - Text extraction from the PDF
   - Layout analysis
   - Table detection
   - Image extraction (if configured)

## Troubleshooting

If you encounter issues with PDF ingestion:

1. Verify the PDF file is not corrupted or password-protected
2. Check that you have the necessary PDF processing libraries installed:
   ```bash
   pip install pdfminer.six pdf2image pytesseract
   ```
3. For image-based PDFs, ensure you have Tesseract OCR installed on your system
4. Check the logs for specific error messages

## Limitations

- Very large PDFs may require more memory and processing time
- Image-based PDFs require OCR capabilities
- Complex layouts may not be perfectly preserved
- Tables and charts may not be fully extracted in their original structure
