"""Shared LLM client — single source of truth for all LLM calls.

Provider priority (first available wins):
  1. ollama     — local, no API key needed (best for testing)
  2. anthropic  — Anthropic's Claude models (requires ANTHROPIC_API_KEY)
  3. openai     — OpenAI models via compatible endpoint (requires OPENAI_API_KEY)

All functions accept optional env_overrides dict to allow runtime overrides
(e.g., from Streamlit sidebar inputs) without needing to set environment variables.
"""

from __future__ import annotations

import os
import re
import json
from typing import Literal, Optional


# ── Popular Ollama models for the UI selector ────────────────────────────

OLLAMA_POPULAR_MODELS = [
    "llama3",
    "llama3.1",
    "llama3.2",
    "mistral",
    "mixtral",
    "qwen2.5",
    "qwen2.5-coder",
    "gemma2",
    "codellama",
    "phi3",
    "llava",
]


# ── Provider priority ────────────────────────────────────────────────────

def get_provider(env_overrides: Optional[dict] = None) -> Literal["ollama", "anthropic", "openai"]:
    """
    Return the highest-priority available provider.
    Ollama is checked first because it requires no API key and is best for testing.

    env_overrides: optional dict with keys like 'ollama_base_url', 'anthropic_api_key',
                   'openai_api_key' — used when the provider is set via UI rather than env vars.
    """
    overrides = env_overrides or {}

    anthropic_key = overrides.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY") or ""
    openai_key = overrides.get("openai_api_key") or os.getenv("OPENAI_API_KEY") or ""
    ollama_url = overrides.get("ollama_base_url") or os.getenv("OLLAMA_BASE_URL") or ""
    ollama_model = overrides.get("ollama_model") or os.getenv("OLLAMA_MODEL") or ""

    # Explicit Ollama model in overrides = user wants Ollama, ignore API key env vars
    if ollama_model and not ollama_url:
        if ollama_url or _ollama_is_reachable():
            return "ollama"
        raise RuntimeError(
            f"Ollama model '{ollama_model}' selected but Ollama server is not reachable at localhost:11434"
        )

    # If no explicit selections made (empty overrides), prefer Ollama for testing
    is_explicit_selection = bool(
        overrides.get("anthropic_api_key") 
        or overrides.get("openai_api_key") 
        or overrides.get("ollama_model")
    )
    
    if not is_explicit_selection:
        # No explicit selection — default to Ollama for local testing
        if ollama_url or _ollama_is_reachable():
            return "ollama"

    # Explicit API key in env_overrides (user entered via UI)
    if anthropic_key and not ollama_url:
        return "anthropic"
    if openai_key and not ollama_url:
        return "openai"

    # Fallback: check for any available provider
    if ollama_url or _ollama_is_reachable():
        return "ollama"
    if anthropic_key:
        return "anthropic"
    if openai_key:
        return "openai"
    raise RuntimeError(
        "No LLM provider available. Either:\n"
        "  1. Run 'ollama serve' (local, no API key needed)\n"
        "  2. Set ANTHROPIC_API_KEY environment variable\n"
        "  3. Set OPENAI_API_KEY environment variable\n"
        "  4. Or enter your API key in the sidebar configuration."
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

def get_client(env_overrides: Optional[dict] = None):
    """
    Returns a (client, model, provider) tuple.

    The returned client is a lightweight wrapper exposing:
      client.complete(prompt, *, system=None, temperature=0.3, max_tokens=4096) -> str

    This interface is identical for all providers, so callers don't need
    to know which backend is actually being used.

    env_overrides: optional dict with runtime overrides for API keys and model names.
                   Supports: ollama_base_url, ollama_model, anthropic_api_key,
                   openai_api_key, openai_model.
    """
    overrides = env_overrides or {}
    provider = get_provider(overrides)

    if provider == "ollama":
        base_url = (
            overrides.get("ollama_base_url")
            or os.getenv("OLLAMA_BASE_URL")
            or "http://localhost:11434/v1"
        )
        model = overrides.get("ollama_model") or os.getenv("OLLAMA_MODEL", "llama3")
        return _OllamaClient(base_url=base_url, model=model), model, "ollama"

    if provider == "anthropic":
        import anthropic
        api_key = overrides.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
        model = "claude-sonnet-4-20250514"
        return (
            _AnthropicClient(anthropic.Anthropic(api_key=api_key), model=model),
            model,
            "anthropic",
        )

    if provider == "openai":
        import openai
        base_url = overrides.get("openai_base_url") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        api_key = overrides.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        model = overrides.get("openai_model") or os.getenv("OPENAI_MODEL", "gpt-4o")
        return (
            _OpenAIClient(openai.OpenAI(api_key=api_key, base_url=base_url), model=model),
            model,
            "openai",
        )


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

    def __init__(self, base_url: str | None = None, model: str | None = None):
        import urllib.request
        import urllib.error
        self._urllib_request = urllib.request
        self._urllib_error = urllib.error
        self._base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self._model = model or os.getenv("OLLAMA_MODEL", "llama3")

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
    def __init__(self, client, model: str = "claude-sonnet-4-20250514"):
        self._client = client
        self._model = model

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        kwargs = dict(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        return response.content[0].text


class _OpenAIClient:
    def __init__(self, client, model: str):
        self._client = client
        self._model = model

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
            model=self._model,
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


# ── Connection tester ────────────────────────────────────────────────

def test_connection(env_overrides: dict | None = None) -> dict:
    """
    Make a minimal LLM call to validate connectivity and credentials.

    Returns a dict with keys:
      - ok (bool): True if the call succeeded
      - provider (str): The provider that was used
      - model (str): The model that was used
      - latency_ms (int): Round-trip time in milliseconds
      - error (str): Error message if failed (present when ok=False)

    This is a fire-and-forget test — errors are caught and returned,
    never raised, so the UI can display them inline.
    """
    import time

    overrides = env_overrides or {}
    test_prompt = "Reply with exactly one word: 'ok'. No punctuation."

    try:
        client, model, provider = get_client(overrides)
        start = time.monotonic()
        raw = client.complete(
            prompt=test_prompt,
            system=None,
            temperature=0.1,
            max_tokens=20,
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        raw_lower = raw.strip().lower()
        # Accept "ok", "ok.", "ok!", etc.
        if raw_lower in ("ok", "ok.") or raw_lower.startswith("ok"):
            return {"ok": True, "provider": provider, "model": model, "latency_ms": latency_ms}
        return {
            "ok": False,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "error": f"Unexpected response (expected 'ok', got): {raw.strip()[:100]}",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── List available Ollama models ───────────────────────────────────

def list_ollama_models(timeout: float = 5.0) -> list[str]:
    """
    Fetch the list of available models from the local Ollama server.

    Returns a list of model names, or an empty list if the server
    is unreachable or returns an error.
    """
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = data.get("models", [])
        return sorted([m["name"] for m in models])
    except Exception:
        return []


def get_ollama_model_choices() -> list[str]:
    """
    Get the list of available Ollama models for the UI dropdown.

    If Ollama is reachable, returns the actual model list.
    Otherwise returns the popular models fallback list.
    """
    models = list_ollama_models()
    if models:
        return models
    return OLLAMA_POPULAR_MODELS
