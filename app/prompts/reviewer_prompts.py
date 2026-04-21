"""User prompt builders for reviewer generation."""

from app.config import DIMENSIONS


def build_reviewer_prompt(
    paper_text: str,
    venue: str,
    venue_info: dict,
    persona_key: str,
    persona_info: dict,
) -> str:
    """
    Build the full user prompt for generating a single review.
    """
    dim_lines = "\n".join(
        f"  - {d['label']}: {d['prompt_hint']}"
        for d in DIMENSIONS
    )
    return f"""## Paper Under Review

**Target Venue:** {venue}
**Venue Description:** {venue_info['description']}
**Venue Emphasis:** {venue_info['emphasis']}

**Reviewer Persona:** {persona_info['name']}
**Character:** {persona_info['character']}
**This reviewer is known for:** {persona_info['strengths']}
**This reviewer may miss:** {persona_info['weaknesses']}
**Tone:** {persona_info['tone']}

---

## Paper Content

{paper_text}

---

## Review Dimensions to Assess

{dim_lines}

---

Please produce your full structured review as a JSON object following the schema in your system prompt.

Be specific — cite paper content where relevant. Do not hold back on weaknesses. The goal is to provide actionable, honest feedback to the authors that will help them improve the paper.

Return your review as a valid JSON object only — no additional text."""
