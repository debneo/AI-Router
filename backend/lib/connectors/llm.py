import os
from typing import Iterator,Protocol


# "message" is {"role": "system"|"user"|"assistant", "content":"..."}
Messages = list[dict]

class LLMClient(Protocol):
    """The one interface the rest of the app depends on.
    Any provider that has these two methods can be dropped in."""

    def complete(self,messages:Messages) -> str: ...
    def stream(self,messages:Messages) -> Iterator[str]: ...


# ------------ Groq ---------
class GroqClient:
    def __init__(self):
        import groq as Groq

        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = os.getenv("GROQ_MODEL","llama-3.1-8b-instant")

    def complete(self,messages:Messages) -> str:
        r= self.client.chat.completions.create(model=self.model,messages=messages)
        return r.choices[0].message.content

    def stream(self,messages:Messages) -> Iterator[str]:
        s=self.client.chat.completions.create(
            model=self.model, messages=messages, stream= True
        )
        for chunk in s:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class GeminiClient:
    def __init__(self):
        from google import genai
        # The new SDK automatically reads GEMINI_API_KEY from os.environ by default,
        # but passing it explicitly guarantees it uses your exact key variable.
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    def _to_prompt(self, messages: Messages) -> str:
        return "\n".join(f"{m['role']}: {m['content']}" for m in messages)

    def complete(self, messages: Messages) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=self._to_prompt(messages)
        )
        return response.text

    def stream(self, messages: Messages) -> Iterator[str]:
        response_stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=self._to_prompt(messages)
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text

# ------------ Factory -------------

_client: LLMClient | None=None

def get_llm() -> LLMClient:
    """Build the chosen client ONCE and reuse it. Callers never know the provider."""
    global _client
    if _client is None:
        provider = os.getenv("LLM_PROVIDER","gemini").lower()
        _client = {
            "groq" : GroqClient,
            "gemini" : GeminiClient,
        }[provider]()
    return _client