from typing import Dict, List
def visible_candidates(context: Dict) -> List[Dict]:
    ids = context.get("visible_products", [])
    return [{"id": i} for i in ids]
