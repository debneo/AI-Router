from lib.connectors.llm import get_llm
from services.retrieval import retrieve
from services.memory import save_message, load_history

SYSTEM = (
    "You answer ONLY using the provided context."
    "If the answer is not in the context, say 'I dont know based on documents.'"
    "Cite the filename(s) you used."
)

def build_context(chunks:list[dict]) -> str:
    return "\n\n".join(
        f"[Source: {c['metadata']['filename']} #chunk{c['metadata']['chunk_index']}]\n{c['text']}"
        for c in chunks
    )

def _needs_rewrite(question:str) -> bool:
    # Only pay for a rewrite if question likely back-references earlier turns.
    refs = {"it","its","it's","that", "this","they","them","those",
            "these","he","she","his","her","their","one","ones"}
    words = [w.strip("?.,!").lower() for w in question.split()]
    return len(words) <=4 or any(w in refs for w in words)

def contextualize(question:str, history:list[dict]) -> str:
    """ Rewrite a follow-up into a standalone question using the conversation.
    eg: history about 'precipitation + "what form does it take?"' -> "What form does precipitation take?"
    This is a common pattern in RAG pipelines, where the LLM is given context and asked to rewrite the question.
    """
    if not history or not _needs_rewrite(question):
        return question
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    llm = get_llm()
    rewritten = llm.complete(
        [
            {
                "role":"system",
                "content":(
                    "Given a conversation and a follow-up question, rewrite the follow-up to be "
                    "a standalone question that includes any relevant context needed to understand it. "
                    "Resolve any pronouns or references to previous messages. Output only the rewritten question, nothing else."
                )
            },
            {
                "role":"user",
                "content":(
                    f"Conversation:\n{convo}\n\nFollow-up question:\n{question}\n\nStandalone question:"
                )
            },
        ]
    )
    return rewritten.strip() or question  # fallback if LLM fails to rewrite

def answer_question(question:str, session_id:str="default") -> dict:
    history = load_history(session_id)
    search_query = contextualize(question, history) # reqrite BEFORE retrieval
    chunks = retrieve(search_query)
    context = build_context(chunks) if chunks else "(no relevant docs found)"
    llm = get_llm()
    messages = [
        {"role":"system","content":SYSTEM},
        *history,
        {"role":"user","content":f"Context:\n{context}\n\nQuestion:\n{question}"},
    ]
    answer = llm.complete(messages)
    save_message(session_id, "user", question)
    save_message(session_id, "assistant", answer)
    sources = sorted({c["metadata"]["filename"] for c in chunks})
    return {"answer":answer, "sources":sources}