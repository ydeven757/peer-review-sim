"""Meta-review synthesis from multiple reviewer outputs."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.llm_client import get_client, parse_json_response
from app.prompts.meta_review_prompt import build_meta_review_prompt

if TYPE_CHECKING:
    from app.reviewer_engine import ReviewResult


def synthesize_meta_review(
    reviews: list[ReviewResult],
    venue: str,
    paper_title: str = "Research Paper",
) -> dict:
    """
    Synthesize a meta-review from multiple reviewer results.

    Args:
        reviews: List of ReviewResult dataclasses from generate_review().
        venue: Target venue name.
        paper_title: Title of the paper (for display).

    Returns:
        A dict with keys:
        - consensus_strengths (list[str])
        - consensus_weaknesses (list[str])
        - disputed_aspects (list[str])
        - final_recommendation (str)
        - recommendation_reasoning (str)
        - error (str, only present if parsing failed)
    """
    from app.reviewer_engine import ReviewResult

    reviews_data = [r.to_dict() for r in reviews]
    prompt = build_meta_review_prompt(reviews_data, venue, paper_title)

    system_prompt = (
        "You are an expert program chair synthesizing peer reviews. "
        "Be fair, balanced, and specific. Return ONLY valid JSON matching the schema provided."
    )

    client, _, _ = get_client()
    raw = client.complete(
        prompt=prompt,
        system=system_prompt,
        temperature=0.2,
        max_tokens=2048,
    )
    result = parse_json_response(raw)
    return result


def compute_average_scores(reviews: list[ReviewResult]) -> dict:
    """
    Compute dimension-wise average scores across reviews.

    Args:
        reviews: List of ReviewResult dataclasses.

    Returns:
        Dict mapping dimension keys to average float scores (e.g. {"novelty": 6.5}).
    """
    dims = ["novelty", "technical", "clarity", "experiments", "related_work"]
    avgs = {}
    for dim in dims:
        scores = []
        for r in reviews:
            s = r.scores.get(dim, {})
            if isinstance(s, dict) and "score" in s:
                try:
                    scores.append(int(s["score"]))
                except (ValueError, TypeError):
                    pass
        avgs[dim] = round(sum(scores) / len(scores), 1) if scores else 0.0
    return avgs
