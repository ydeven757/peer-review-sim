"""Meta-review synthesis from multiple reviewer outputs."""
from __future__ import annotations

import json
import os
import re
from typing import TYPE_CHECKING

from app.prompts.meta_review_prompt import build_meta_review_prompt

if TYPE_CHECKING:
    from app.reviewer_engine import ReviewResult


def _get_llm_client() -> tuple:
    """Returns (client, model_name, provider)."""
    if api_key := os.getenv("ANTHROPIC_API_KEY"):
        import anthropic
        return anthropic.Anthropic(api_key=api_key), "claude-sonnet-4-20250514", "anthropic"
    elif api_key := os.getenv("OPENAI_API_KEY"):
        import openai
        client = openai.OpenAI(api_key=api_key)
        return client, "gpt-4o", "openai"
    else:
        raise RuntimeError(
            "No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your environment."
        )


def _call_llm(
    client,
    model: str,
    provider: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2048,
) -> str:
    """Call the LLM and return the raw response text."""
    if provider == "anthropic":
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
    elif provider == "openai":
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _parse_json_response(raw: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {"error": f"Could not parse JSON from LLM response (first 300 chars):\n{raw[:300]}"}


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

    client, model, provider = _get_llm_client()
    raw = _call_llm(client, model, provider, system_prompt, prompt)
    result = _parse_json_response(raw)
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
