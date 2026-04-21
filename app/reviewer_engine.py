"""Core LLM-powered reviewer generation engine."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Literal

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


def _get_llm_client() -> tuple:
    """
    Returns (client, model_name, provider) tuple.
    Provider is 'anthropic' or 'openai'.
    """
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
    max_tokens: int = 4096,
) -> str:
    """Call the LLM and return the raw response text."""
    if provider == "anthropic":
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
    elif provider == "openai":
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
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
    """
    Parse JSON from LLM response.
    Tries direct parse first, then extracts from markdown code blocks.
    """
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try to extract from ```json ... ``` or ``` ... ```
    match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        raw,
        re.DOTALL,
    )
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any {...} block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not parse JSON from LLM response (first 300 chars):\n{raw[:300]}"
    )


def generate_review(
    paper_text: str,
    venue: str,
    venue_info: dict,
    persona_key: str,
    persona_info: dict,
) -> ReviewResult:
    """
    Generate a single structured review for the given paper.

    Args:
        paper_text: The full text of the paper to review.
        venue: The target venue name (e.g., "ICLR").
        venue_info: The venue config dict from app.config.VENUES.
        persona_key: The persona key (e.g., "prolific").
        persona_info: The persona config dict from app.config.PERSONAS.

    Returns:
        A ReviewResult dataclass with all review fields.

    Raises:
        RuntimeError: If no API key is set.
        ValueError: If the LLM response cannot be parsed as JSON.
    """
    client, model, provider = _get_llm_client()
    system_prompt = build_system_prompt(venue, persona_key, persona_info["name"])
    user_prompt = build_reviewer_prompt(
        paper_text=paper_text,
        venue=venue,
        venue_info=venue_info,
        persona_key=persona_key,
        persona_info=persona_info,
    )

    raw = _call_llm(client, model, provider, system_prompt, user_prompt)
    data = _parse_json_response(raw)

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
