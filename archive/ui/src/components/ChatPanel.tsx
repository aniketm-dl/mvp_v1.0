import { useState } from "react";
import { chatTwin } from "../lib/api";
import { useStore } from "../store";

export default function ChatPanel() {
  const twin = useStore(s => s.selectedTwin);
  const chat = useStore(s => s.chat);
  const push = useStore(s => s.pushChat);
  const conditioning = useStore(s => s.conditioning);
  const [text, setText] = useState("");

  async function send() {
    if (!twin || !text.trim()) return;
    push({ who: "user", text });
    const r = await chatTwin(twin.id, text, chat.map(m => ({ role: m.who === "user" ? "user":"assistant", content: m.text })), conditioning);
    push({ who: "twin", text: r.reply });
    setText("");
  }

  return (
    <div className="panel">
      <h3 style={{marginTop:0}}>Chat</h3>
      <div style={{height:"calc(100% - 90px)", overflow:"auto", display:"flex", flexDirection:"column", gap:8}}>
        {chat.map((m, i) => (
          <div key={i}><span className="tag">{m.who}</span> {m.text}</div>
        ))}
      </div>
      <div className="row" style={{marginTop:8}}>
        <input placeholder={twin ? `Message ${twin.label}` : "Select a persona first"} value={text} onChange={(e)=>setText(e.target.value)} />
        <button className="btn primary" onClick={send}>Send</button>
      </div>
    </div>
  );
}
