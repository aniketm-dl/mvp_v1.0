import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000",
  headers: { "Content-Type": "application/json" }
});

export async function getBank() {
  const r = await api.get("/twin/bank"); return r.data;
}
export async function getPersonas() {
  const r = await api.get("/twin/personas"); return r.data.personas;
}
export async function chatTwin(twin_id: string, prompt: string, history: Array<{role:string;content:string}>, conditioning?: any) {
  const r = await api.post("/twin/chat", { twin_id, prompt, history, conditioning }); return r.data;
}
export async function decideTwin(twin_id: string, context: any, candidates: Array<{id:string}>, conditioning?: any) {
  const r = await api.post("/twin/decide", { twin_id, context, candidates, max_tokens: 20, conditioning }); return r.data;
}
export async function simulate(payload: any) {
  const r = await api.post("/simulate", payload); return r.data;
}
export async function copyVariants() {
  const r = await api.get("/catalog/copy_variants"); return r.data.variants || [];
}
export async function listPins() {
  const r = await api.get("/admin/pins", { headers: { "X-Admin-Token": import.meta.env.VITE_ADMIN_TOKEN } }); return r.data.pins;
}
export async function upsertPin(name: string, weights: Record<string, number>, conditioning?: any) {
  const r = await api.post("/admin/pin", { name, weights, conditioning }, { headers: { "X-Admin-Token": import.meta.env.VITE_ADMIN_TOKEN } });
  return r.data.pin;
}
