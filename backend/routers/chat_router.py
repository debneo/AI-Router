from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel,Field
import json

from lib.connectors.llm import get_llm
from services.retrieval import retrieve
from services.trace import count_message_tokens, log_event
from services.memory import save_message, load_history
from services.rag import SYSTEM, build_context, answer_question, contextualize
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
    result = answer_question(req.message, req.session_id)
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
    # Rewrite pronouns in followup questions to be standalone, so retrieval works better
    history = load_history(req.session_id) # recent turns without token budget
    search_query = contextualize(req.message, history) # rewrite BEFORE retrieval
    chunks = retrieve(search_query)
    context = build_context(chunks) if chunks else "(no relevant docs found)"
    sources = sorted({c["metadata"]["filename"] for c in chunks})

    def event_stream():
        # First event : Sources(metadata) so UI can show citations before answer is complete
        yield f"data: {json.dumps({'type':'sources', 'sources':sources})}\n\n"
        try:
            llm = get_llm()
            prompt_messages = [
                {"role":"system","content":SYSTEM},
                *history,
                {"role":"user","content":f"Context:\n{context}\n\nQuestion:\n{req.message}"},
            ]
            # Observality: log the number of tokens in the prompt, so we can monitor usage and costs
            log_event(
                "chat_stream_prompt",
                question=req.message,
                rewritten=search_query,
                chunks=len(chunks),
                history_msgs=len(history),
                prompt_tokens=count_message_tokens(prompt_messages),
            )
            collected = [] # accumulate full answer to save it in memory
            for token in llm.stream(prompt_messages):
                collected.append(token)
                yield f"data: {json.dumps({'type':'token','token':token})}\n\n"
            answer_text = "".join(collected)
            log_event( "chat_stream_answer",answer_tokens=count_message_tokens([{"content":answer_text}]))
            # Persist this turn so that next question in session has context
            save_message(req.session_id, "user", req.message)
            save_message(req.session_id, "assistant", answer_text)
            #After the answer is complete, generate followup questions and stream them as well
            try:
                followups = followups_agent({"chunks": chunks}).get("followups",[])
            except Exception:
                followups = [] # folowups are optional
            yield f"data: {json.dumps({'type':'followups','followups':followups})}\n\n"
            yield f"data: {json.dumps({'type':'done'})}\n\n"
        except Exception as exec:
            yield f"data: {json.dumps({'type':'error','message':f'{type(exec).__name__}:{exec}'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")