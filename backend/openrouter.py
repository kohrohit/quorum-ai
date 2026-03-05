"""Multi-provider LLM client with token and latency tracking."""

import httpx
import os
import time
from typing import List, Dict, Any, Optional
from .config import PROVIDER_CONFIG


def _get_provider(model: str) -> tuple[str, str]:
    """Extract provider and model name from 'provider/model' format."""
    parts = model.split("/", 1)
    return parts[0], parts[1]


def _get_api_key(provider: str) -> str:
    """Get the API key for a provider."""
    key_var = PROVIDER_CONFIG[provider]["key_var"]
    return os.getenv(key_var, "")


async def _query_anthropic(
    model_name: str,
    messages: List[Dict[str, str]],
    api_key: str,
    timeout: float,
) -> Optional[Dict[str, Any]]:
    """Query Anthropic's native API."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    system_text = ""
    api_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        else:
            api_messages.append(msg)

    payload = {
        "model": model_name,
        "max_tokens": 8192,
        "messages": api_messages,
    }
    if system_text:
        payload["system"] = system_text

    start = time.time()
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            PROVIDER_CONFIG["anthropic"]["url"],
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    latency_ms = round((time.time() - start) * 1000)

    content_blocks = data.get("content", [])
    text = "".join(
        block["text"] for block in content_blocks if block.get("type") == "text"
    )

    usage = data.get("usage", {})
    return {
        "content": text,
        "tokens": {
            "input": usage.get("input_tokens", 0),
            "output": usage.get("output_tokens", 0),
        },
        "latency_ms": latency_ms,
    }


async def _query_openai_compatible(
    provider: str,
    model_name: str,
    messages: List[Dict[str, str]],
    api_key: str,
    timeout: float,
) -> Optional[Dict[str, Any]]:
    """Query OpenAI-compatible APIs (OpenAI, Google Gemini)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_name,
        "messages": messages,
    }

    url = PROVIDER_CONFIG[provider]["url"]

    start = time.time()
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    latency_ms = round((time.time() - start) * 1000)

    message = data["choices"][0]["message"]
    usage = data.get("usage", {})
    return {
        "content": message.get("content"),
        "reasoning_details": message.get("reasoning_details"),
        "tokens": {
            "input": usage.get("prompt_tokens", 0),
            "output": usage.get("completion_tokens", 0),
        },
        "latency_ms": latency_ms,
    }


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
) -> Optional[Dict[str, Any]]:
    """Query a single model. Returns dict with content, tokens, latency_ms."""
    try:
        provider, model_name = _get_provider(model)
        api_key = _get_api_key(provider)

        if not api_key:
            print(f"Error: No API key found for provider '{provider}'")
            return None

        if provider == "anthropic":
            return await _query_anthropic(model_name, messages, api_key, timeout)
        else:
            return await _query_openai_compatible(
                provider, model_name, messages, api_key, timeout
            )

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
) -> Dict[str, Optional[Dict[str, Any]]]:
    """Query multiple models in parallel."""
    import asyncio

    tasks = [query_model(model, messages) for model in models]
    responses = await asyncio.gather(*tasks)
    return {model: response for model, response in zip(models, responses)}
