from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel,Field
import json

from lib.connectors.llm import get_llm
from services.retrieval import retrieve
from services.rag import SYSTEM, build_context, answer_question
from solutions.qa.agents.answer_agent import followups_agent

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

@router.post("/chat/stream")
def chat_stream(req:ChatRequest):
    # Retrieve context upfront and then stream the answer as it is generated
    chunks = retrieve(req.message)
    context = build_context(chunks) if chunks else "(no relevant docs found)"
    sources = sorted({c["metadata"]["filename"] for c in chunks})

    def event_stream():
        # First event : Sources(metadata) so UI can show citations before answer is complete
        yield f"data: {json.dumps({'type':'sources', 'sources':sources})}\n\n"
        llm = get_llm()
        for token in llm.stream(
            [
                {"role":"system","content":SYSTEM},
                {"role":"user","content":f"Context:\n{context}\n\nQuestion:\n{req.message}"},
            ]
        ):
            yield f"data: {json.dumps({'type':'token','token':token})}\n\n"
        #After the answer is complete, generate followup questions and stream them as well
        followups = followups_agent({"chunks": chunks}).get("followups",[])
        yield f"data: {json.dumps({'type':'followups','followups':followups})}\n\n"
        yield f"data: {json.dumps({'type':'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")