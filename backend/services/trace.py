import json
import sys
import time

from services.chunking import count_tokens

def log_event(event:str, **fields):
    """Print one structured log line to stderr (shows up in the uvicorn terminal)."""
    record = {"ts": round(time.time(), 3), "event": event, **fields}
    print(json.dumps(record), file=sys.stderr)

def count_message_tokens(messages: list[dict]) -> int:
    """Count the number of tokens in a message."""
    return sum(count_tokens(m.get("content","")) for m in messages)