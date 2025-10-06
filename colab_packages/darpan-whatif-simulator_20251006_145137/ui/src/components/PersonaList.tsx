import { useEffect, useState } from "react";
import { getBank } from "../lib/api";
import { useStore } from "../store";

export default function PersonaList() {
  const [items, setItems] = useState<any[]>([]);
  const setTwin = useStore(s => s.setTwin);
  const selected = useStore(s => s.selectedTwin);

  useEffect(() => { getBank().then((d) => setItems(d.twins || [])); }, []);

  return (
    <aside>
      <div className="panel">
        <div className="row" style={{justifyContent:"space-between"}}>
          <h3 style={{margin:0}}>Personas</h3>
          <span className="small">adapters show ✓</span>
        </div>
        <div className="list">
          {items.map(t => {
            const active = selected?.id === t.id;
            return (
              <div key={t.id} className={`item ${active ? "active":""}`} onClick={() => setTwin({id:t.id, label:t.label, adapter:t.adapter})}>
                <div className="row" style={{justifyContent:"space-between"}}>
                  <div><strong>{t.label}</strong><div className="small">{t.id}</div></div>
                  <div>{t.adapter ? "✓" : ""}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
