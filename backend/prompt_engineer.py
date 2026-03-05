"""Prompt refinement system for Quorum AI — LLM-driven, no keyword maintenance."""

from typing import List, Dict, Any, Optional
from .openrouter import query_model
from .config import COUNCIL_MODELS
import json


async def classify_and_refine(query: str, council_models: List[str] = None) -> Dict[str, Any]:
    """
    Use a fast model to classify the query, generate clarifying questions,
    and suggest expert roles. No hardcoded keywords.
    """
    models = council_models or COUNCIL_MODELS
    model = models[0]  # Use first available model for classification

    prompt = f"""Analyze this user query and return a JSON object with exactly these fields:

1. "query_type": a short label for the type of question (e.g. "code", "architecture", "debug", "comparison", "creative", "factual", etc.)
2. "questions": a list of 2-3 clarifying questions that would help answer this query better
3. "suggested_roles": a dict mapping each of these model IDs to an expert role that would be most helpful for this query: {json.dumps(models)}

User query: "{query}"

Return ONLY valid JSON, no markdown, no explanation."""

    response = await query_model(model, [{"role": "user", "content": prompt}], timeout=30.0)

    if response is None:
        return _fallback(query, models)

    try:
        text = response.get("content", "").strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        return json.loads(text)
    except (json.JSONDecodeError, KeyError):
        return _fallback(query, models)


def _fallback(query: str, models: List[str]) -> Dict[str, Any]:
    """Fallback when LLM classification fails."""
    return {
        "query_type": "general",
        "questions": [
            "Can you provide more context about what you're trying to achieve?",
            "Any specific constraints or requirements?",
        ],
        "suggested_roles": {m: "Expert" for m in models},
    }


async def build_refined_prompt(
    query: str,
    query_type: str,
    user_answers: Optional[Dict[str, str]] = None,
    role: str = "Expert",
) -> str:
    """Build a structured prompt from query, type, and user's clarifying answers."""
    context = ""
    if user_answers:
        context = "\n".join(f"- {q}: {a}" for q, a in user_answers.items() if a.strip())

    if not context:
        context = "(No additional context provided)"

    return f"""You are answering as a {role}.

Context from the user:
{context}

Question: {query}

Provide a comprehensive, well-structured answer. Be specific and concrete."""
