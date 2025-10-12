import { useEffect, useState } from "react";
import { useStore } from "../store";
import { copyVariants } from "../lib/api";

export default function ScenarioPanel() {
  const context = useStore(s => s.context);
  const setContext = useStore(s => s.setContext);
  const scenarios = useStore(s => s.scenarios);
  const setScenarios = useStore(s => s.setScenarios);
  const explain = useStore(s => s.explain);
  const setExplain = useStore(s => s.setExplain);
  const use_pin = useStore(s => s.use_pin);
  const setUsePin = useStore(s => s.setUsePin);
  const conditioning = useStore(s => s.conditioning);
  const setConditioning = useStore(s => s.setConditioning);

  const [copies, setCopies] = useState<any[]>([]);
  useEffect(()=>{ copyVariants().then(setCopies); },[]);

  function updateContext(k: string, v: any) {
    setContext({ ...context, [k]: v});
  }

  function addScenario() {
    const id = `v${scenarios.length}`;
    setScenarios([...scenarios, { variant_id: id, context_overrides: {} }]);
  }

  return (
    <div className="panel">
      <h3 style={{marginTop:0}}>Scenario Builder</h3>

      <div className="col">
        <label className="small">Base context</label>
        <div className="row">
          <label className="small">Promo</label>
          <input type="checkbox" checked={!!context.promo_badge} onChange={(e)=>updateContext("promo_badge", e.target.checked)} />
          <label className="small">Price mean</label>
          <input type="number" value={context.price_mean || ""} onChange={(e)=>updateContext("price_mean", Number(e.target.value)||0)} />
          <label className="small">Delivery days</label>
          <input type="number" value={context.delivery_eta_days || ""} onChange={(e)=>updateContext("delivery_eta_days", Number(e.target.value)||0)} />
        </div>
        <div className="row">
          <label className="small">Copy variant</label>
          <select value={context.copy_variant_id || ""} onChange={(e)=>updateContext("copy_variant_id", e.target.value || null)}>
            <option value="">(none)</option>
            {copies.map((c:any)=> (<option key={c.copy_variant_id} value={c.copy_variant_id}>{c.copy_variant_id} — {c.text}</option>))}
          </select>
        </div>
      </div>

      <div className="col" style={{marginTop:12}}>
        <label className="small">Scenarios</label>
        {scenarios.map((s, i)=>(
          <div key={i} className="item">
            <div className="row" style={{justifyContent:"space-between"}}>
              <strong>{s.variant_id}</strong>
            </div>
            <div className="row" style={{marginTop:6}}>
              <label className="small">Override price_mean</label>
              <input type="number" onChange={(e)=>{
                const v = Number(e.target.value);
                const ns = [...scenarios]; ns[i] = {...ns[i], context_overrides: {...ns[i].context_overrides, price_mean: isNaN(v)? undefined : v}};
                setScenarios(ns);
              }} />
              <label className="small">Promo</label>
              <input type="checkbox" onChange={(e)=>{
                const ns = [...scenarios]; ns[i] = {...ns[i], context_overrides: {...ns[i].context_overrides, promo_badge: e.target.checked}};
                setScenarios(ns);
              }} />
              <label className="small">Delivery days</label>
              <input type="number" onChange={(e)=>{
                const v = Number(e.target.value);
                const ns = [...scenarios]; ns[i] = {...ns[i], context_overrides: {...ns[i].context_overrides, delivery_eta_days: isNaN(v)? undefined : v}};
                setScenarios(ns);
              }} />
            </div>
          </div>
        ))}
        <button className="btn" onClick={addScenario}>Add scenario</button>
      </div>

      <div className="row" style={{marginTop:12, gap:12}}>
        <div className="col" style={{flex:1}}>
          <label className="small">Explain mode</label>
          <select value={explain} onChange={(e)=>setExplain(e.target.value as any)}>
            <option value="none">none</option>
            <option value="blend">blend</option>
            <option value="per_twin">per_twin</option>
          </select>
        </div>
        <div className="col" style={{flex:1}}>
          <label className="small">Use pin (optional)</label>
          <input value={use_pin || ""} onChange={(e)=>setUsePin(e.target.value || undefined)} placeholder="pin name"/>
        </div>
      </div>

      <div className="col" style={{marginTop:12}}>
        <label className="small">Conditioning (psychographic tags, comma-separated)</label>
        <input value={(conditioning?.psychographic_tags || []).join(",")} onChange={(e)=>{
          const tags = e.target.value.split(",").map(s=>s.trim()).filter(Boolean);
          setConditioning(tags.length? { ...conditioning, psychographic_tags: tags } : undefined);
        }} />
      </div>
    </div>
  );
}
