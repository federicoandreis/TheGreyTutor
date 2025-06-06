from fastapi import APIRouter, Request
from kg_quizzing.scripts.quiz_api import chat_endpoint, ChatRequest, ChatResponse

router = APIRouter()

@router.post("", response_model=ChatResponse)
async def chat_route(req: ChatRequest, request: Request):
    return chat_endpoint(req, request)
