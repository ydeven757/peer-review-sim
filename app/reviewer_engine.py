"""Core LLM-powered reviewer generation engine."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from app.llm_client import get_client, parse_json_response
from app.prompts.system_prompt import build_system_prompt
from app.prompts.reviewer_prompts import build_reviewer_prompt


@dataclass
class ReviewResult:
    """Structured result from a single reviewer persona."""
    persona: str
    summary: str
    scores: dict
    strengths: list
    weaknesses: list
    questions: list
    suggestions: list
    minor_issues: list
    recommendation: str
    confidence: int
    raw_json: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def generate_review(
    paper_text: str,
    venue: str,
    venue_info: dict,
    persona_key: str,
    persona_info: dict,
    env_overrides: dict | None = None,
) -> ReviewResult:
    """
    Generate a single structured review for the given paper.

    Args:
        paper_text: The full text of the paper to review.
        venue: The target venue name (e.g., "ICLR").
        venue_info: The venue config dict from app.config.VENUES.
        persona_key: The persona key (e.g., "prolific").
        persona_info: The persona config dict from app.config.PERSONAS.
        env_overrides: Optional dict of LLM overrides (api keys, model names).

    Returns:
        A ReviewResult dataclass with all review fields.

    Raises:
        RuntimeError: If no LLM provider is available (no API key, no Ollama).
        ValueError: If the LLM response cannot be parsed as JSON.
    """
    client, model, provider = get_client(env_overrides)
    system_prompt = build_system_prompt(venue, persona_key, persona_info["name"])
    user_prompt = build_reviewer_prompt(
        paper_text=paper_text,
        venue=venue,
        venue_info=venue_info,
        persona_key=persona_key,
        persona_info=persona_info,
    )

    raw = client.complete(
        prompt=user_prompt,
        system=system_prompt,
        temperature=0.3,
        max_tokens=8192,  # Increased for slower Ollama models
    )
    data = parse_json_response(raw)
    if "error" in data:
        raise ValueError(data["error"])

    return ReviewResult(
        persona=persona_info["name"],
        summary=data.get("summary", ""),
        scores=data.get("scores", {}),
        strengths=data.get("strengths", []),
        weaknesses=data.get("weaknesses", []),
        questions=data.get("questions", []),
        suggestions=data.get("suggestions", []),
        minor_issues=data.get("minor_issues", []),
        recommendation=data.get("recommendation", "Borderline"),
        confidence=data.get("confidence", 5),
        raw_json=raw,
    )
