from services.retrieval import retrieve

def fetch_relevant_chunks(question:str) -> list[dict]:
    """ Fetch the most relevant chunks from the user's uploaded documents based on the question. 
    
    Returns a list of { text, metadata, score }."""
    return retrieve(question)