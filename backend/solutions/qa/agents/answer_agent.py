from lib.connectors.llm import get_llm
from services.rag import SYSTEM, build_context
from solutions.qa.tools.retriever_tool import fetch_relevant_chunks

def retrieve_agent(state: dict) -> dict:
    """Chef 1: fetch relevant chunks and put them into shared state"""
    chunks = fetch_relevant_chunks(state["question"])
    return {"chunks": chunks}

def answer_agent(state: dict) -> dict:
    """Chef 2: write an answer based on the question and the chunks"""
    chunks = state.get("chunks", [])
    if not chunks:
        return {"answer": "I don't know based on provided docs.", "sources": []}
    llm = get_llm()
    answer = llm.complete(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", 
             "content": f"Context:\n{build_context(chunks)}\n\nQuestion:\n{state['question']}"},
        ]
    )
    sources = sorted({c["metadata"]["filename"] for c in chunks})
    return {"answer": answer, "sources": sources}

def followups_agent(state: dict) -> dict:
    """Chef 3: write followup questions based on the answer"""
    chunks = state.get("chunks", [])
    if not chunks:
        return {"followups": []}
    llm = get_llm()
    followups = llm.complete(
        [
            {"role": "system", "content": "Suggest 3 short followup questions. One per line, no numbering."},
            {"role": "user", 
             "content": build_context(chunks)},
        ]
    )
    return {"followups": [l.strip("-.") for l in followups.splitlines() if l.strip()][:3]}