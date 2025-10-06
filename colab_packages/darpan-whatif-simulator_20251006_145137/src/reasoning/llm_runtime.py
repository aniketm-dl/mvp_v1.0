from __future__ import annotations
from typing import Any, Dict, Optional, List
from pathlib import Path
import random
import os
import yaml
import json

# Optional heavy imports guarded
_TR = None; _TOK = None; _PEFT = None

def _lazy_import():
    global _TR, _TOK, _PEFT
    if _TR is None:
        from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
        _TR = (AutoModelForCausalLM, set_seed)
        _TOK = AutoTokenizer
        from peft import PeftModel
        _PEFT = PeftModel

class LLMRuntime:
    def __init__(self, cfg_path: str = "CONFIGS/serve/llm.yaml") -> None:
        self.cfg = yaml.safe_load(Path(cfg_path).read_text())
        self.base_model_id = self.cfg["llm"]["base_model"]
        self.adapter_dir = Path(self.cfg["llm"]["adapter_dir"])
        self.use_stub = bool(self.cfg["llm"]["use_stub"])
        self.temp = float(self.cfg["llm"]["temperature"])
        self.top_p = float(self.cfg["llm"]["top_p"])
        self.max_new = int(self.cfg["llm"]["max_new_tokens"])
        self.seed = int(self.cfg["llm"]["seed"])
        self._model = None
        self._tok = None
        self._loaded_adapters: Dict[str, bool] = {}
        random.seed(self.seed)

        # Load personas for stub responses
        self._personas = self._load_personas()

    def _load_personas(self) -> Dict[str, Dict]:
        """Load persona definitions from DATA/personas.json."""
        personas_file = Path("DATA/personas.json")
        if not personas_file.exists():
            return {}

        data = json.loads(personas_file.read_text())
        return {p["id"]: p for p in data.get("personas", [])}

    def _ensure_base(self):
        if self._model is not None or self.use_stub:
            return
        _lazy_import()
        AutoModelForCausalLM, set_seed = _TR
        AutoTokenizer = _TOK
        set_seed(self.seed)
        self._tok = AutoTokenizer.from_pretrained(self.base_model_id)
        self._model = AutoModelForCausalLM.from_pretrained(self.base_model_id)
        self._model.eval()

    def _adapter_path(self, twin_id: str) -> Path:
        return self.adapter_dir / twin_id

    def adapter_available(self, twin_id: str) -> bool:
        return (self._adapter_path(twin_id) / "adapter_config.json").exists()

    def reload_adapter(self, twin_id: str) -> bool:
        if self.use_stub:
            self._loaded_adapters[twin_id] = False
            return False
        self._ensure_base()
        if not self.adapter_available(twin_id):
            self._loaded_adapters[twin_id] = False
            return False
        from peft import PeftModel
        self._model = PeftModel.from_pretrained(self._model, self._adapter_path(twin_id))
        self._model.eval()
        self._loaded_adapters[twin_id] = True
        return True

    def _stub_reply(self, twin_label: str, twin_id: str, prompt: str, tags: List[str]) -> str:
        """Generate stub response based on persona characteristics."""
        hint = f" [{','.join(sorted(tags))}]" if tags else ""

        # Get persona from loaded data
        persona = self._personas.get(twin_id, {})

        # Extract key persona traits
        psychographic_tags = persona.get("psychographic_tags", [])
        shopping_values = persona.get("shopping_values", [])
        typical_behavior = persona.get("typical_behavior", "")

        # Determine response based on prompt keywords and persona traits
        prompt_lower = prompt.lower()

        # Price-related questions
        if any(kw in prompt_lower for kw in ["price", "cost", "budget", "afford", "expensive", "cheap"]):
            if any(tag in psychographic_tags for tag in ["price_sensitive", "deal_seeker", "budget_conscious"]):
                return f"Price is my top priority - I always look for the best deal{hint}."
            elif any(tag in psychographic_tags for tag in ["quality_focused", "premium_buyer"]):
                return f"I'm willing to pay more for quality and reliability{hint}."
            elif "brand_agnostic" in psychographic_tags:
                return f"I have no brand loyalty - I go where the value is{hint}."
            else:
                return f"I consider price along with other factors{hint}."

        # Quality-related questions
        elif any(kw in prompt_lower for kw in ["quality", "reliable", "premium", "best"]):
            if any(tag in psychographic_tags for tag in ["quality_focused", "selective"]):
                return f"Quality is non-negotiable for me{hint}."
            elif "price_sensitive" in psychographic_tags:
                return f"I look for decent quality at the right price{hint}."
            else:
                return f"Quality matters, but I balance it with other factors{hint}."

        # Brand-related questions
        elif any(kw in prompt_lower for kw in ["brand", "loyalty", "trust"]):
            if "brand_loyal" in psychographic_tags:
                return f"I stick with brands I trust{hint}."
            elif "brand_agnostic" in psychographic_tags:
                return f"I have zero brand loyalty - I judge each product individually{hint}."
            else:
                return f"Brands are one factor I consider{hint}."

        # Delivery-related questions
        elif any(kw in prompt_lower for kw in ["delivery", "shipping", "fast", "prime"]):
            if any(tag in psychographic_tags for tag in ["time_conscious", "efficiency_focused", "convenience_focused"]):
                return f"Fast delivery is essential - I value my time{hint}."
            elif "price_sensitive" in psychographic_tags:
                return f"I prefer fast delivery if the price is right{hint}."
            else:
                return f"I appreciate reasonable delivery times{hint}."

        # Local/community/small business questions
        elif any(kw in prompt_lower for kw in ["local", "community", "small business", "amazon", "big box", "walmart", "target"]):
            if "community_oriented" in psychographic_tags or "small_business_supporter" in psychographic_tags:
                if any(kw in prompt_lower for kw in ["amazon", "walmart", "target", "big box"]):
                    return f"I always choose local and small businesses over big retailers - community impact matters more than convenience{hint}."
                else:
                    return f"Supporting local businesses strengthens our community - I'm willing to pay more for that{hint}."
            elif "convenience_focused" in psychographic_tags:
                return f"I prefer the convenience of major retailers for speed and selection{hint}."
            elif "price_sensitive" in psychographic_tags:
                return f"I'll shop wherever I find the best price - usually the big retailers{hint}."
            else:
                return f"I shop at both local and big retailers depending on what I need{hint}."

        # Decision/shopping process questions
        elif any(kw in prompt_lower for kw in ["decide", "choose", "buy", "purchase", "shop"]):
            if any(tag in psychographic_tags for tag in ["analytical", "detail_oriented"]):
                return f"I research extensively and compare all options methodically{hint}."
            elif any(tag in psychographic_tags for tag in ["spontaneous", "fomo_prone"]):
                return f"I make quick decisions based on immediate appeal{hint}."
            elif "values_driven" in psychographic_tags:
                return f"I prioritize ethical and sustainable options{hint}."
            else:
                return f"I weigh multiple factors when making decisions{hint}."

        # Review-related questions
        elif any(kw in prompt_lower for kw in ["review", "rating", "feedback"]):
            if any(tag in psychographic_tags for tag in ["review_dependent", "socially_influenced"]):
                return f"Reviews are essential - I only buy highly-rated products{hint}."
            elif "analytical" in psychographic_tags:
                return f"I read reviews carefully and look for detailed information{hint}."
            else:
                return f"I glance at reviews when available{hint}."

        # Innovation/trends
        elif any(kw in prompt_lower for kw in ["new", "latest", "trend", "innovation"]):
            if any(tag in psychographic_tags for tag in ["innovation_seeker", "early_adopter"]):
                return f"I love being first to try new products and trends{hint}."
            elif "selective" in psychographic_tags:
                return f"I'm cautious with new products - I prefer proven quality{hint}."
            else:
                return f"I'm open to new products if they meet my needs{hint}."

        # Gift/present questions
        elif any(kw in prompt_lower for kw in ["gift", "present", "someone else", "for my"]):
            if "gift_oriented" in psychographic_tags or "thoughtful" in psychographic_tags:
                return f"I love finding unique, meaningful gifts that show I really know the person{hint}."
            else:
                return f"I try to find gifts that match the recipient's interests{hint}."

        # Subscription/recurring purchase questions
        elif any(kw in prompt_lower for kw in ["subscription", "subscribe", "recurring", "auto"]):
            if "automation_lover" in psychographic_tags or "routine_oriented" in psychographic_tags:
                return f"I love subscriptions - set it and forget it is perfect for me{hint}."
            elif "spontaneous" in psychographic_tags:
                return f"I prefer flexibility - subscriptions feel too restrictive{hint}."
            else:
                return f"Subscriptions work well for things I use regularly{hint}."

        # Bulk/quantity questions
        elif any(kw in prompt_lower for kw in ["bulk", "large quantity", "wholesale", "costco", "sam"]):
            if "wholesale_oriented" in psychographic_tags or "planner" in psychographic_tags:
                return f"Buying in bulk saves money long-term - I always calculate unit costs{hint}."
            elif "minimalist" in psychographic_tags:
                return f"I only buy what I need right now - no bulk purchases{hint}."
            else:
                return f"I buy in bulk for items I use frequently{hint}."

        # Mobile/app shopping questions
        elif any(kw in prompt_lower for kw in ["mobile", "app", "phone", "smartphone"]):
            if "mobile_native" in psychographic_tags or "app_user" in psychographic_tags:
                return f"I do almost all my shopping on my phone - mobile experience is crucial{hint}."
            else:
                return f"I use both mobile and desktop depending on what I'm buying{hint}."

        # Generic fallback based on primary persona trait
        if "price_sensitive" in psychographic_tags or "budget_conscious" in psychographic_tags:
            return f"I prioritize value and smart spending{hint}."
        elif "quality_focused" in psychographic_tags:
            return f"I focus on quality and long-term value{hint}."
        elif "convenience_focused" in psychographic_tags:
            return f"I value convenience and efficiency{hint}."
        elif "values_driven" in psychographic_tags:
            return f"I choose products that align with my values{hint}."
        else:
            return f"I balance multiple factors in my shopping decisions{hint}."

    def chat(self, twin_label: str, twin_id: str, prompt: str, psych_tags: List[str]) -> str:
        if self.use_stub or not self.adapter_available(twin_id):
            return self._stub_reply(twin_label, twin_id, prompt, psych_tags)
        self._ensure_base()
        from transformers import set_seed
        set_seed(self.seed)
        sys_prompt = f"You are {twin_label}. Be concise. 1 sentence."
        text = f"{sys_prompt}\nUser: {prompt}\nAssistant:"
        toks = self._tok(text, return_tensors="pt")
        out = self._model.generate(
            **toks,
            do_sample=False,
            temperature=0.0,
            top_p=1.0,
            max_new_tokens=self.max_new
        )
        ans = self._tok.decode(out[0], skip_special_tokens=True)
        return ans.split("Assistant:")[-1].strip()

    def adapters_status(self, twin_ids: List[str]) -> dict:
        return {
            "use_stub": self.use_stub,
            "adapters": {tid: {"available": self.adapter_available(tid), "loaded": self._loaded_adapters.get(tid, False)} for tid in twin_ids}
        }

RUNTIME = LLMRuntime()
