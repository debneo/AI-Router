from lib.connectors.llm import get_llm
from services.retrieval import retrieve

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

def answer_question(question:str) -> dict:
    chunks = retrieve(question)
    if not chunks:
        return {"answer":"I dont know based on your docs","sources":[]}
    context = build_context(chunks)
    llm = get_llm()
    answer = llm.complete(
        [
            {"role":"system","content":SYSTEM},
            {"role":"user","content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
    )
    sources = sorted({c["metadata"]["filename"] for c in chunks})
    return {"answer":answer, "sources":sources}