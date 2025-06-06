from fastapi import APIRouter, Request
from kg_quizzing.scripts.quiz_api import (
    start_session, get_next_question, submit_answer, get_session_state,
    StartSessionRequest, StartSessionResponse,
    QuestionResponse, SubmitAnswerRequest, SubmitAnswerResponse,
    SessionStateResponse
)

router = APIRouter()

@router.post("", response_model=StartSessionResponse)
def session_start(req: StartSessionRequest):
    return start_session(req)

@router.get("/{session_id}/question", response_model=QuestionResponse)
def session_next_question(session_id: str):
    return get_next_question(session_id)

@router.post("/{session_id}/answer", response_model=SubmitAnswerResponse)
def session_submit_answer(session_id: str, req: SubmitAnswerRequest):
    return submit_answer(session_id, req)

@router.get("/{session_id}", response_model=SessionStateResponse)
def session_state(session_id: str):
    return get_session_state(session_id)
