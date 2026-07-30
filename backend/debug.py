"""Debug conversational RAG step by step"""

from dotenv import load_dotenv
load_dotenv()

from services.memory import load_history, save_message
from services.rag import contextualize
from services.retrieval import retrieve

SESSION = "debug-session"

def show_hisotry():
    hist = load_history(SESSION)
    print(f"\n[HISTORY] {len(hist)} messages for session '{SESSION}':")
    for m in hist:
        print(f"  {m['role']}:{m['content'][:80]}")
    return hist

def probe(question:str):
    print("\n"+"="*70)
    print(f"[QUESTION] {question}")
    hist = show_hisotry()

    rewritten = contextualize(question,hist)
    print(f"\n[REWRITTEN QUERY] {rewritten!r}")
    if rewritten.strip() == question.strip():
        print("     no rewrite happened")

    chunks = retrieve(rewritten)
    print(f"\n[RETRIEVED] {len(chunks)} chunks for rewritten query:")
    for c in chunks:
        print(f" score={c['score']:.2f} file={c['metadata']['filename']} :: {c['text'][:80]}")
    if not chunks:
        print(" NO CHUNKS")

if __name__ == "__main__":
    q1 = "What is precipitation?"
    probe(q1)
    save_message(SESSION,"user",q1)
    save_message(SESSION,"assisstant","Precipitation is rain, snow, or hail that falls on EARTH")

    probe("What forms does it take")