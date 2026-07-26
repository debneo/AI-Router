"use client";
import { useState } from "react";
import { ingestFile, askQuestion } from "@/lib/api";

export default function Home(){
    const [status,setStatus] = useState("");
    const [input,setInput] = useState("");
    const [answer,setAnswer] = useState("");
    const [sources,setSources] = useState<string[]>([]);
    const [loading,setLoading] = useState(false);

    async function onUpload(e: React.ChangeEvent<HTMLInputElement>){
        const file = e.target.files?.[0];
        if(!file) return;
        setStatus("Uploading file...");
        try{
            const r = await ingestFile(file);
            setStatus(`Added ${r.chunks} chunks from ${r.fileName}`);
        } catch (error:any) {
            setStatus(`Error: ${error.message}`);
        }
    }

    async function onAsk(){
        if(!input.trim()) return;
        setLoading(true);
        setAnswer("");
        setSources([]);
        try{
            const r = await askQuestion(input);
            setAnswer(r.response);
            setSources(r.sources ?? []);
        } catch (error:any) {
            setStatus(`Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    }

    return (
        <main style ={{ maxWidth: 700, margin: "40px auto", fontFamily: "sans-serif" }}>
            <h1>AskMyDocs</h1>

            <input type="file" onChange={onUpload} accept=".pdf,.txt,.md,.docx" />
            <p>{status}</p>
            <hr />
            <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { e.key==="Enter" && onAsk(); }}
                placeholder="Ask a question about your documents"
                style={{ width: "100%", padding: 8, fontSize: 16 }}
            />
            <button onClick={onAsk} disabled={loading} style={{ marginLeft:8, padding: "6px 12px" }}>
                {loading ? "Asking..." : "Ask"}
            </button>

            {sources.length > 0 && (
                <p><b>Sources:</b> {sources.join(", ")}</p>
            )}
            <p style={{ whiteSpace: "pre-wrap", marginTop: 20 }}>{answer}</p>
        </main>
    )
}
