async function baseUrl(): Promise<string>{
    const res = await fetch("/api/config");
    const data = await res.json();
    return data.config?.API_URL ?? "http://localhost:8000";
}

// Upload a file to the backend's /ingest endpoint.
export async function ingestFile(file: File){
    const url = `${await baseUrl()}/ingest`;
    const form = new FormData();
    form.append("file",file);
    const res = await fetch(url, { method: "POST", body: form});
    if (!res.ok) throw new Error(`Ingest failed: ${res.status}`);
    return res.json();
}

// Ask a question via the backend's /chat endpoint (non-streaming).
export async function askQuestion(message: string, sessionId = "default"){
    const url = `${await baseUrl()}/chat`;
    const res = await fetch(url,{
        method: "POST",
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify({message, session_id:sessionId}),
    });
    if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
    return res.json(); // {response, sources}
}

// Streaming chat: calls/ chat/ stream and yields parsed SSE events as they arrive.
export async function* chatStream(message: string, sessionId = "default"){
    const url = `${await baseUrl()}/chat/stream`;
    const res = await fetch(url,{
        method: "POST",
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify({message, session_id:sessionId}),
    });
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true){
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n"); // SSE messages are seperatedbyu blank lines
        buffer = lines.pop() ?? ""; // last line may be incomplete, keep it in buffer
        for (const line of lines){
            if (!line.startsWith("data:")) continue;
            yield JSON.parse(line.slice(5)); // parse JSON after "data:" // { type: "sources"|"token"|"done", ... }
        }
    }
}