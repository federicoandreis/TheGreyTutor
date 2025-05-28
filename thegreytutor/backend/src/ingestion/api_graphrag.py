"""
API router for minimal GraphRag ingestion pipeline.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .graphrag_minimal import ingest_text_with_graphrag

router = APIRouter()

class IngestRequest(BaseModel):
    text: str

class IngestResponse(BaseModel):
    result: str

@router.post("/graphrag/ingest", response_model=IngestResponse)
def ingest_graphrag(request: IngestRequest):
    """Ingest text into Neo4j via GraphRag."""
    result = ingest_text_with_graphrag(request.text)
    if result is None:
        raise HTTPException(status_code=500, detail="GraphRag ingestion failed.")
    return IngestResponse(result=result)
