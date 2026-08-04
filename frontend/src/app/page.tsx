"use client";
import { useState,useRef, useEffect } from "react";
import { ingestFile, chatStream } from "@/lib/api";

export default function Home(){
    const [status,setStatus] = useState("");
    const [input,setInput] = useState("");
    const [answer,setAnswer] = useState("");
    const [sources,setSources] = useState<string[]>([]);
    const [loading,setLoading] = useState(false);
    const [followups,setFollowups] = useState<string[]>([]);

    const fullTextRef = useRef(""); // everything received from stream so far
    const doneRef = useRef(false); // set to true when stream is done
    const timeRef = useRef<ReturnType<typeof setInterval> | null>(null); // for debouncing

    // Clean up typing timer if component unmounts mid-stream
    useEffect(() => {
        return () => {
            if(timeRef.current) clearInterval(timeRef.current);
        };
    },[]);

    // Reveal buffered text a few chars per tick -> smoother typing effect
    // This is a bit of a hack, but it works well enough for now.
    function startTyping(){
        if(timeRef.current) return; // already typing
        timeRef.current = setInterval(() => {
            setAnswer((shown) => {
                const full = fullTextRef.current;
                if(shown.length >= full.length){
                    if(doneRef.current && timeRef.current){
                        clearInterval(timeRef.current);
                        timeRef.current = null;
                    }
                    return shown;
                }
                return full.slice(0, shown.length + 3); // reveal 3 more chars per tick
            });
        }, 16); // ~60fps
    }

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

    async function onAsk(question?: string){
        const query = question ?? input;
        if(!query.trim()) return;
        setInput(query);
        setLoading(true);
        setAnswer("");
        setSources([]);
        setFollowups([]);
        fullTextRef.current = "";
        doneRef.current = false;
        startTyping();
        try{
            // Buffer tokens as they arrive: Sources 1st, then answer word by word
            // Typing timer reveals them gradually to the user for a smoother effect
            for await (const rsp of chatStream(query)){
                if(rsp.type === "sources") setSources(rsp.sources);
                if(rsp.type === "token") fullTextRef.current += rsp.token;
                if(rsp.type === "followups") setFollowups(rsp.followups);
                if(rsp.type === "error") fullTextRef.current += `\n[Error:${rsp.message}]`;
            }
        } catch (error:any) {
            fullTextRef.current += `\n\nError: ${error.message}`;
        } finally {
            doneRef.current = true; // let the timer drain the buffer, then stop
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
            <button onClick={()=>onAsk()} disabled={loading} style={{ marginLeft:8, padding: "6px 12px" }}>
                {loading ? "Thinking..." : "Ask"}
            </button>

            {sources.length > 0 && (
                <p><b>Sources:</b> {sources.join(", ")}</p>
            )}
            <p style={{ whiteSpace: "pre-wrap", marginTop: 20 }}>{answer}</p>

            {followups.length > 0 && (
                <div style={{ marginTop: 20 }}>
                    <b>Follow-up questions:</b>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
                        {followups.map((q, idx) => (
                            <button
                            key={idx} 
                            onClick={()=>onAsk(q)} 
                            style={{
                                textAlign: "left",
                                padding: "6px 12px",
                                background: "#0c3ea2",
                                border: "1px solid #ccc",
                                borderRadius: 4,
                                cursor: loading ? "not-allowed" : "pointer",
                             }}>
                                {q}
                            </button>
                        ))}
                    </div>
                </div>
            )}
            
        </main>
    );
}
