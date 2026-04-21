"""User prompt builder for meta-review synthesis."""

from app.config import DIMENSIONS

def build_meta_review_prompt(
    reviews_data: list,
    venue: str,
    paper_title: str = "Research Paper",
) -> str:
    """
    Build the user prompt for synthesizing a meta-review from multiple reviews.
    """
    reviews_text = "\n\n".join(
        f"--- Review {i+1} (Persona: {r.get('persona', '?')}) ---\n"
        f"Summary: {r.get('summary', '')}\n"
        f"Recommendation: {r.get('recommendation', '?')} (confidence: {r.get('confidence', '?')}/10)\n"
        f"Scores: {r.get('scores', {})}\n"
        f"Strengths: {r.get('strengths', [])}\n"
        f"Weaknesses: {r.get('weaknesses', [])}\n"
        f"Questions: {r.get('questions', [])}\n"
        f"Suggestions: {r.get('suggestions', [])}\n"
        for i, r in enumerate(reviews_data)
    )
    return f"""## Paper: {paper_title}
## Venue: {venue}

You have received {len(reviews_data)} independent peer reviews of the paper above. Synthesize them into a coherent meta-review.

Your meta-review should:
1. Identify consensus STRENGTHS — things most or all reviewers agree on
2. Identify consensus WEAKNESSES — things most or all reviewers flagged
3. Note DISPUTED ASPECTS — where reviewers disagreed
4. Provide a FINAL RECOMMENDATION with clear reasoning

Return your meta-review ONLY as a valid JSON object with this schema:
{{
  "consensus_strengths": ["strength 1", "strength 2", ...],
  "consensus_weaknesses": ["weakness 1", "weakness 2", ...],
  "disputed_aspects": ["disputed point 1", ...],
  "final_recommendation": "Accept | Borderline | Reject",
  "recommendation_reasoning": "2-3 sentence justification for the recommendation"
}}

Rules:
- Be specific in consensus points — name specific weaknesses, not vague generalizations
- If reviewers disagree on something significant, note it in disputed_aspects
- recommendation_reasoning should reference specific evidence from the reviews
- Return JSON only — no additional text outside the JSON object.

---

## Individual Reviews

{reviews_text}
"""
