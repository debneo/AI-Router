import re
import tiktoken

_enc = tiktoken.get_encoding("cl100k_base") # a good general token counter

def count_tokens(text: str) -> int:
    return len(_enc.encode(text))

def _split_sentences(text: str) -> list[str]:
    # Simple sentence splitter, good enough for chunking
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

def adaptive_chunks(text: str, target_tokens: int=300, overlap_tokens: int = 40) -> list[str]:
    """
    Adaptive strategy:
        1. Split on blank lines into 'blocks' (paragraphs / sections) - respects structure.
        2. Pack blocks together until we approach target_tokens (keeps related text together)
        3. If a single block is bigger than target, split it by sentences
        4. Add a small token overlap between chunks so context isnt cut mid-thought.
    """
    blocks = [b.strip() for b in re.split(r"\n\s*\n",text) if b.strip()]
    chunks : list[str] = []
    buffer: list[str] = []
    buffer_tokens = 0

    def flush():
        nonlocal buffer, buffer_tokens
        if buffer:
            chunks.append("\n\n".join(buffer))
            buffer, buffer_tokens = [], 0

    for block in blocks:
        bt = count_tokens(block)
        if bt > target_tokens: # oversized block -> split by sentence
            flush()
            sent_buf, sent_tokens = [],0
            for sent in _split_sentences(block):
                st = count_tokens(sent)
                if sent_tokens + st > target_tokens and sent_buf:
                    chunks.append(" ".join(sent_buf))
                    sent_buf, sent_tokens = [],0
                sent_buf.append(sent)
                sent_tokens += st
            if sent_buf:
                chunks.append(" ".join(sent_buf))
        elif buffer_tokens + bt > target_tokens: # would overflow -> start a new chunk
            flush()
            buffer, buffer_tokens = [block], bt
        else: # fits -> keep packing
            buffer.append(block)
            buffer_tokens += bt
    flush()

    # add overlap: prepend the tail of the previous chunk to each chunk
    if overlap_tokens > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1,len(chunks)):
            prev_tail = _enc.decode(_enc.encode(chunks[i-1])[-overlap_tokens:])
            overlapped.append(prev_tail + "\n" + chunks[i])
        chunks = overlapped
    return chunks