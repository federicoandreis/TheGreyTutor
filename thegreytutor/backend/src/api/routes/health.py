from fastapi import APIRouter

router = APIRouter()

@router.get("")
def health_stub():
    return {"status": "ok"}
