from sentence_transformers import CrossEncoder

from services.chunking import count_tokens
from services.vector_store import get_collection

# A cross-encoder scores ( question, chunk ) pairs far more accurately than
# embeddings alone. Loaded once at import; downlads ~90MB 1st time
_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def retrieve(
        question: str,
        first_k: int= 12,
        final_k: int = 4,
        min_score: float =0.0,
        token_budget: int =1500,
) -> list[dict]:
    """
    Selective retrieval pipeline:
    1. Vector search returns a WIDE net (first_k candidates).
    2. Rerank them with a cross-encoder for true relevance.
    3. Drop anything below min_score ( irrelevant -> gone).
    4. Keep top chunks until we hit final_k OR run out of token_budget.
    """
    col = get_collection()
    res = col.query(query_texts=[question], n_results = first_k)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    if not docs:
        return []

    scores = _reranker.predict([(question,d) for d in docs])
    ranked = sorted(zip(docs,metas,scores), key = lambda x: x[2], reverse=True)

    selected, used_tokens = [],0
    for doc, meta,score in ranked:
        if score < min_score:
            continue
        t = count_tokens(doc)
        if used_tokens + t > token_budget:
            continue # skip chunks that dont fit budget
        selected.append({"text":doc, "metadata":meta, "score": float(score)})
        used_tokens += t
        if len(selected) >= final_k:
            break
    return selected