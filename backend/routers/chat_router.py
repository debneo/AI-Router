from fastapi import APIRouter
from pydantic import BaseModel,Field

from lib.connectors.llm import get_llm
from services.rag import answer_question

# router is a mini app
router = APIRouter(tags=["Chat"])

class ChatRequest(BaseModel):
    """Pydantic validates the request body at the door.
    If 'message' is missing, FastAPI returns a clear 422 automatically."""

    message: str = Field(...,description="User's question")
    session_id: str = Field(default="default",description="which conversation this belongs to")

@router.post("/chat")
def chat(req:ChatRequest):
    result = answer_question(req.message)
    return {"response":result["answer"],"sources":result["sources"]}

@router.post("/greet")
def greet(req:ChatRequest):
    llm = get_llm()
    answer = llm.complete(
        [
            {"role":"system","content":"You are a concise, helpful assistant"},
            {"role":"user","content":req.message},
        ]
    )
    return {"response":answer}