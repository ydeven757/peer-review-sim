"""Shared LLM client — single source of truth for all LLM calls.

Provider priority (first available wins):
  1. ollama     — local, no API key needed (best for testing)
  2. anthropic  — Anthropic's Claude models (requires ANTHROPIC_API_KEY)
  3. openai     — OpenAI models via compatible endpoint (requires OPENAI_API_KEY)
"""
from __future__ import annotations

import os
import re
import json
from typing import Literal


# ── Provider priority ───────────────────────────────────────────────

def get_provider() -> Literal["ollama", "anthropic", "openai"]:
    """
    Return the highest-priority available provider.
    Ollama is checked first because it requires no API key and is best for testing.
    """
    if os.getenv("OLLAMA_BASE_URL") or _ollama_is_reachable():
        return "ollama"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    raise RuntimeError(
        "No LLM provider available. Set one of:\n"
        "  OLLAMA_BASE_URL     — for local Ollama (no API key needed)\n"
        "  ANTHROPIC_API_KEY   — for Claude Sonnet 4\n"
        "  OPENAI_API_KEY      — for GPT-4o"
    )


def _ollama_is_reachable(timeout: float = 2.0) -> bool:
    """Check if a local Ollama instance is reachable."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags")
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except Exception:
        return False


# ── Client factory ─────────────────────────────────────────────────

def get_client():
    """
    Returns a (client, model, provider) tuple.

    The returned client is a lightweight wrapper exposing:
      client.complete(prompt, *, system=None, temperature=0.3, max_tokens=4096) -> str

    This interface is identical for all providers, so callers don't need
    to know which backend is actually being used.
    """
    provider = get_provider()

    if provider == "ollama":
        return _OllamaClient(), os.getenv("OLLAMA_MODEL", "llama3"), "ollama"
    if provider == "anthropic":
        import anthropic
        return _AnthropicClient(anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )), "claude-sonnet-4-20250514", "anthropic"
    if provider == "openai":
        import openai
        base_url = os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        return _OpenAIClient(openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=base_url,
        )), os.getenv("OPENAI_MODEL", "gpt-4o"), "openai"


# ── Per-provider client wrappers ────────────────────────────────────

class _OllamaClient:
    """
    Ollama client using the OpenAI-compatible chat completions endpoint.

    Requires a running Ollama server:
        ollama serve          # default: http://localhost:11434

    Environment variables:
        OLLAMA_BASE_URL  — full base URL (default: http://localhost:11434/v1)
        OLLAMA_MODEL    — model name (default: llama3)

    Example models: llama3, llama3.1, mistral, mixtral, qwen2.5, codellama
    """

    def __init__(self):
        import urllib.request
        import urllib.error
        self._urllib_request = urllib.request
        self._urllib_error = urllib.error
        self._base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self._model = os.getenv("OLLAMA_MODEL", "llama3")

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        data = json.dumps(payload).encode("utf-8")
        req = self._urllib_request.Request(
            f"{self._base_url}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._urllib_request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except self._urllib_error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(
                f"Ollama request failed ({e.code}): {err_body or e.reason}"
            ) from e

        return result["choices"][0]["message"]["content"]


class _AnthropicClient:
    def __init__(self, client):
        self._client = client

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        kwargs = dict(
            model=self._client.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        return response.content[0].text


class _OpenAIClient:
    def __init__(self, client):
        self._client = client

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self._client.chat.completions.create(
            model=self._client.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
        )
        return response.choices[0].message.content


# ── Shared JSON parser ─────────────────────────────────────────────

def parse_json_response(raw: str) -> dict:
    """
    Parse JSON from LLM response, handling markdown code blocks.
    Returns a dict, or a dict with an "error" key on parse failure.
    """
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    for pattern in [
        r"```json\s*(\{.*?\})\s*```",
        r"```\s*(\{.*?\})\s*```",
    ]:
        match = re.search(pattern, raw, re.DOTALL)
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
