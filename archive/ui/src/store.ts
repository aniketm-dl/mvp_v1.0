import { create } from "zustand";

type Msg = { who: "user" | "twin"; text: string };

type State = {
  selectedTwin?: { id: string; label: string; adapter?: boolean };
  chat: Msg[];
  context: any;
  candidates: { id: string }[];
  scenarios: { variant_id: string; context_overrides: any }[];
  explain: "none" | "blend" | "per_twin";
  use_pin?: string;
  conditioning?: { psychographic_tags?: string[]; demographic_profile?: any };
  setTwin: (t: any) => void;
  pushChat: (m: Msg) => void;
  setContext: (c: any) => void;
  setCandidates: (cs: { id: string }[]) => void;
  setScenarios: (s: any[]) => void;
  setExplain: (e: "none"|"blend"|"per_twin") => void;
  setUsePin: (p?: string) => void;
  setConditioning: (c?: any) => void;
};

export const useStore = create<State>((set) => ({
  selectedTwin: undefined,
  chat: [],
  context: { page_type: "search", visible_products: ["A1","A2","A3"], promo_badge: false, delivery_eta_days: 3 },
  candidates: [{id:"A1"},{id:"A2"},{id:"A3"}],
  scenarios: [{ variant_id: "base", context_overrides: {} }],
  explain: "blend",
  use_pin: undefined,
  conditioning: undefined,
  setTwin: (t) => set({ selectedTwin: t, chat: [] }),
  pushChat: (m) => set((s) => ({ chat: [...s.chat, m] })),
  setContext: (c) => set({ context: c }),
  setCandidates: (cs) => set({ candidates: cs }),
  setScenarios: (s) => set({ scenarios: s }),
  setExplain: (e) => set({ explain: e }),
  setUsePin: (p) => set({ use_pin: p }),
  setConditioning: (c) => set({ conditioning: c })
}));
