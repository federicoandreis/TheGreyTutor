"""
Quiz API for Adaptive Quizzing System

This FastAPI app exposes endpoints for managing quiz sessions, retrieving questions, submitting answers, and checking session state.

- Modular: Delegates logic to QuizOrchestrator and QuizSession
- In-memory session store (no backend coupling)
- Aligned with kg_queries/scripts approach

Usage:
    uvicorn quiz_api:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import logging
import sys
import os
from pydantic import BaseModel

# Add kg_queries/scripts to sys.path for import
KG_QUERY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../kg_queries/scripts'))
if KG_QUERY_PATH not in sys.path:
    sys.path.insert(0, KG_QUERY_PATH)

try:
    from graphrag_retriever import GraphRAGRetriever
except ImportError as e:
    GraphRAGRetriever = None
    import_error = str(e)

try:
    # Use the in-character Gandalf retriever from run_pathrag.py
    from run_pathrag import process_query
except ImportError as e:
    process_query = None
    llm_import_error = str(e)

# Import orchestrator and session logic
from .quiz_orchestrator import QuizOrchestrator
from .llm_assessment import assess_answer
from .conversation_history import ConversationHistoryManager, QuizConversation

app = FastAPI(title="Quiz API", description="API for Adaptive Quizzing System", version="0.1.0")

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standalone conversation history manager for assessments
assessment_convo_dir = "assessment_conversations"
# Check if database should be used
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() in ("true", "1", "yes")
assessment_history_manager = ConversationHistoryManager(assessment_convo_dir, use_database=USE_DATABASE)


# In-memory session storage (for demonstration/testing)
sessions: Dict[str, QuizOrchestrator] = {}

# Request/Response Models

class QueryRequest(BaseModel):
    query: str
    strategy: Optional[str] = "hybrid"
    max_results: Optional[int] = 10

class QueryResponse(BaseModel):
    strategy: str
    query: str
    nodes: Any
    relationships: Any
    paths: Any
    execution_time: float
    total_results: int
    metadata: Any

class ChatRequest(BaseModel):
    question: str
    verbose: Optional[bool] = False
    use_cache: Optional[bool] = True
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[dict] = None

class ChatResponse(BaseModel):
    answer: str

class StartSessionRequest(BaseModel):
    student_id: str
    student_name: str
    strategy: Optional[str] = "adaptive"
    use_llm: Optional[bool] = True
    tier: Optional[str] = None
    fussiness: Optional[int] = 3
    theme: Optional[str] = None
    conversation_dir: Optional[str] = "conversation_history"

class StartSessionResponse(BaseModel):
    session_id: str
    student_id: str
    student_name: str
    strategy: str
    use_llm: bool
    tier: Optional[str]
    fussiness: int
    theme: Optional[str]
    conversation_dir: Optional[str]

class QuestionResponse(BaseModel):
    question: Any
    session_id: str
    question_number: int

class SubmitAnswerRequest(BaseModel):
    answer: Any

class SubmitAnswerResponse(BaseModel):
    correct: bool
    quality: Optional[int] = None
    feedback: Optional[dict] = None
    next_question: Optional[Any] = None
    session_complete: bool
    session_id: str

class AssessAnswerRequest(BaseModel):
    question: dict
    answer: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None

class AssessAnswerResponse(BaseModel):
    correct: bool
    quality: Optional[int] = None
    feedback: Optional[dict] = None
    conversation_id: Optional[str] = None

class SessionStateResponse(BaseModel):
    session_id: str
    student_id: str
    student_name: str
    questions_asked: int
    correct: int
    incorrect: int
    current_question: Optional[Any]
    finished: bool

# Endpoint: Start a new quiz session
@app.post("/session", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest):
    session_id = str(uuid.uuid4())
    
    # Check if we should use the database
    use_database = os.getenv("USE_DATABASE", "false").lower() in ("true", "1", "yes")
    
    orchestrator = QuizOrchestrator(
        student_id=req.student_id,
        student_name=req.student_name,
        strategy=req.strategy,
        conversation_dir=req.conversation_dir,
        use_llm=req.use_llm,
        tier=req.tier,
        fussiness=req.fussiness,
        theme=req.theme,
        use_database=use_database
    )
    orchestrator.start_session()
    sessions[session_id] = orchestrator
    return StartSessionResponse(
        session_id=session_id,
        student_id=req.student_id,
        student_name=req.student_name,
        strategy=req.strategy,
        use_llm=req.use_llm,
        tier=req.tier,
        fussiness=req.fussiness,
        theme=req.theme,
        conversation_dir=req.conversation_dir
    )

# Endpoint: Get the next question
@app.get("/session/{session_id}/question", response_model=QuestionResponse)
def get_next_question(session_id: str):
    orchestrator = sessions.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="Session not found")
    session = orchestrator.current_session
    if session is None:
        raise HTTPException(status_code=400, detail="Session not initialized")
    question = session.next_question()
    if question is None:
        raise HTTPException(status_code=404, detail="No more questions available")
    return QuestionResponse(
        question=question,
        session_id=session_id,
        question_number=session.session_stats.get("questions_asked", 0)
    )

# Endpoint: Submit an answer
@app.post("/session/{session_id}/answer", response_model=SubmitAnswerResponse)
def submit_answer(session_id: str, req: SubmitAnswerRequest):
    orchestrator = sessions.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="Session not found")
    session = orchestrator.current_session
    if session is None:
        raise HTTPException(status_code=400, detail="Session not initialized")
    correct, quality, feedback = session.process_answer(req.answer)
    next_question = session.next_question() if not session.session_stats.get("end_time") else None
    return SubmitAnswerResponse(
        correct=correct,
        quality=quality,
        feedback=feedback,
        next_question=next_question,
        session_complete=session.session_stats.get("end_time") is not None,
        session_id=session_id
    )

# Endpoint: Get session state/progress
@app.get("/session/{session_id}", response_model=SessionStateResponse)
def get_session_state(session_id: str):
    orchestrator = sessions.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="Session not found")
    session = orchestrator.current_session
    if session is None:
        raise HTTPException(status_code=400, detail="Session not initialized")
    stats = session.session_stats
    return SessionStateResponse(
        session_id=session_id,
        student_id=session.student_id,
        student_name=session.student_name,
        questions_asked=stats.get("questions_asked", 0),
        correct=stats.get("correct", 0),
        incorrect=stats.get("incorrect", 0),
        current_question=session.current_question,
        finished=stats.get("end_time") is not None
    )

# Endpoint: Standalone answer assessment
@app.post("/assess", response_model=AssessAnswerResponse)
def assess_endpoint(req: AssessAnswerRequest):
    # Assess the answer
    correct, quality, feedback = assess_answer(req.question, req.answer)
    # Record in conversation history
    conversation_id = req.conversation_id or f"assessment_{uuid.uuid4()}"
    convo = QuizConversation(
        student_id=req.user_id or "anonymous",
        quiz_id=conversation_id,
        metadata={"mode": "assessment"}
    )
    # Add system message (question)
    convo.add_system_message(req.question.get("text") or req.question.get("question"))
    # Add user message (answer)
    convo.add_user_message(req.answer)
    # Add feedback (Gandalf's wisdom)
    convo.add_feedback(feedback)
    assessment_history_manager.save_conversation(convo)
    return AssessAnswerResponse(
        correct=correct,
        quality=quality,
        feedback=feedback,
        conversation_id=conversation_id
    )

@app.post("/query", response_model=QueryResponse)
def query_kg(req: QueryRequest):
    if GraphRAGRetriever is None:
        raise HTTPException(status_code=500, detail=f"Could not import GraphRAGRetriever: {import_error}")
    retriever = GraphRAGRetriever()
    try:
        result = retriever.retrieve(
            query=req.query,
            strategy=req.strategy,
            max_results=req.max_results
        )
        return QueryResponse(
            strategy=result.strategy,
            query=result.query,
            nodes=result.nodes,
            relationships=result.relationships,
            paths=result.paths,
            execution_time=result.execution_time,
            total_results=result.total_results,
            metadata=result.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Request

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, request: Request):
    if process_query is None:
        raise HTTPException(status_code=500, detail=f"Could not import process_query from run_pathrag: {llm_import_error}")
    try:
        # Use Gandalf in-character retriever; match run_pathrag.py signature
        result = process_query(req.question, use_cache=req.use_cache, verbose=req.verbose)
        answer = result["answer"]

        # Gather metadata
        user_id = req.user_id or "anonymous"
        session_id = req.session_id or str(uuid.uuid4())
        user_agent = request.headers.get("user-agent", "unknown")
        client_host = request.client.host if request.client else "unknown"
        base_metadata = req.metadata or {}
        convo_metadata = {
            "mode": "chat",
            "user_id": user_id,
            "session_id": session_id,
            "user_agent": user_agent,
            "client_host": client_host,
            **base_metadata
        }

        convo = QuizConversation(
            student_id=user_id,
            quiz_id=session_id,
            metadata=convo_metadata
        )
        from .conversation_history import ConversationMessage
        user_msg = ConversationMessage(role="user", content=req.question, metadata={"user_agent": user_agent, "client_host": client_host, **base_metadata})
        assistant_msg = ConversationMessage(role="assistant", content=answer, metadata={"user_agent": user_agent, "client_host": client_host})
        convo.messages.append(user_msg)
        convo.messages.append(assistant_msg)
        assessment_history_manager.save_conversation(convo)

        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("quiz_api:app", host="0.0.0.0", port=8000, reload=True)
