TEMPLATE = "Chooses the best visible option."
def short_reason(context, candidate_id) -> str:
    # TODO: integrate LLM at temperature=0; enforce visible-only attributes
    return TEMPLATE
