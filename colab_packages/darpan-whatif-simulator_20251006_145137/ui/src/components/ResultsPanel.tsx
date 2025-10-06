import { useState } from "react";
import { useStore } from "../store";
import { simulate } from "../lib/api";

export default function ResultsPanel() {
  const context = useStore(s => s.context);
  const candidates = useStore(s => s.candidates);
  const scenarios = useStore(s => s.scenarios);
  const explain = useStore(s => s.explain);
  const conditioning = useStore(s => s.conditioning);
  const use_pin = useStore(s => s.use_pin);
  const [resp, setResp] = useState<any|null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    try {
      const payload = {
        cta_seq: [{
          user_id: "demo", session_id: "demo", ts: "2025-06-01T12:00:00",
          context: { ...context, visible_products: candidates.map(c=>c.id) },
          task: "choose_product", action_id: candidates[0]?.id || "A1"
        }],
        task: "choose_product",
        scenarios,
        topk: 5,
        explain,
        deterministic: true,
        seed: 17,
        ...(use_pin ? { use_pin } : {}),
        ...(conditioning ? { conditioning } : {})
      };
      const r = await simulate(payload);
      setResp(r);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="right">
      <div className="row" style={{justifyContent:"space-between", marginBottom:8}}>
        <h3 style={{margin:0}}>Results</h3>
        <button className="btn primary" onClick={run} disabled={busy}>{busy? "Running..." : "Run simulate"}</button>
      </div>
      {!resp ? <div className="small">No run yet. Click Run simulate.</div> : (
        <div className="col" style={{gap:12}}>
          {resp.by_scenario.map((s:any)=>(
            <div key={s.variant_id} className="item">
              <div className="row" style={{justifyContent:"space-between"}}>
                <strong>Scenario: {s.variant_id}</strong>
                {s.why ? <span className="small">blend why: {s.why}</span> : null}
              </div>
              <div className="col" style={{marginTop:6}}>
                <label className="small">TopN</label>
                <pre>{JSON.stringify(s.topN, null, 2)}</pre>
                <label className="small">Deltas vs base</label>
                <pre>{JSON.stringify(s.deltas, null, 2)}</pre>
                {s.by_twin ? (
                  <>
                    <label className="small">Per twin</label>
                    <pre>{JSON.stringify(s.by_twin, null, 2)}</pre>
                  </>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
