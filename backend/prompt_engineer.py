"""Prompt refinement system for Quorum AI."""

import re
from typing import List, Dict, Any, Optional


QUERY_TYPES = {
    "code": {
        "keywords": ["code", "function", "bug", "error", "implement", "write", "class", "api", "endpoint", "syntax", "refactor", "test", "unit test"],
        "roles": {"default": ["Senior Developer", "Code Reviewer", "Performance Engineer"]},
    },
    "architecture": {
        "keywords": ["architecture", "design", "system", "scale", "microservice", "monolith", "database", "infrastructure", "deploy", "cloud"],
        "roles": {"default": ["System Architect", "DevOps Engineer", "Security Expert"]},
    },
    "debug": {
        "keywords": ["debug", "fix", "crash", "broken", "not working", "fails", "exception", "traceback", "stack trace", "issue"],
        "roles": {"default": ["Debugger", "Performance Engineer", "Senior Developer"]},
    },
    "comparison": {
        "keywords": ["compare", "vs", "versus", "difference", "better", "which one", "pros and cons", "trade-off", "alternative"],
        "roles": {"default": ["Technical Analyst", "Solutions Architect", "Product Engineer"]},
    },
    "factual": {
        "keywords": ["what is", "how does", "explain", "define", "meaning", "concept", "theory", "history"],
        "roles": {"default": ["Domain Expert", "Technical Writer", "Research Analyst"]},
    },
    "creative": {
        "keywords": ["create", "generate", "idea", "brainstorm", "suggest", "innovate", "design", "prototype", "build"],
        "roles": {"default": ["Creative Lead", "Product Manager", "UX Designer"]},
    },
}

QUESTIONS_BY_TYPE = {
    "code": [
        "What programming language/framework are you using?",
        "What's the expected behavior vs what's happening?",
        "Any constraints (performance, compatibility, etc.)?",
    ],
    "architecture": [
        "What's your current scale (users, data size, traffic)?",
        "Cloud provider or self-hosted?",
        "Team size and experience level?",
    ],
    "debug": [
        "What error message or unexpected behavior are you seeing?",
        "When did it start happening (after a change, randomly)?",
        "What have you already tried?",
    ],
    "comparison": [
        "What's the use case or context for this comparison?",
        "Any constraints (budget, team skills, timeline)?",
        "What matters most to you (performance, cost, simplicity)?",
    ],
    "factual": [
        "What's your current understanding of this topic?",
        "What level of depth do you need (overview vs deep dive)?",
    ],
    "creative": [
        "What problem are you trying to solve?",
        "Any constraints or requirements to keep in mind?",
        "Who is the target audience?",
    ],
    "general": [
        "Can you provide more context about what you're trying to achieve?",
        "Any specific constraints or requirements?",
    ],
}

PROMPT_TEMPLATES = {
    "code": """You are answering as a {role}.

Context from the user:
{context}

Question: {query}

Provide:
- Working code with clear comments
- Edge cases and error handling considerations
- Performance implications if relevant
- Alternative approaches if applicable""",

    "architecture": """You are answering as a {role}.

Context from the user:
{context}

Question: {query}

Provide:
- Specific architectural recommendations with diagrams described in text
- Step-by-step approach prioritized by impact
- Trade-offs and alternatives considered
- Scalability and maintenance implications""",

    "debug": """You are answering as a {role}.

Context from the user:
{context}

Question: {query}

Provide:
- Root cause analysis (think step by step)
- Specific fix with code if applicable
- How to verify the fix works
- How to prevent this issue in the future""",

    "comparison": """You are answering as a {role}.

Context from the user:
{context}

Question: {query}

Provide:
- Structured comparison with clear criteria
- Pros and cons for each option
- Recommendation based on the user's context
- When each option is the better choice""",

    "factual": """You are answering as a {role}.

Context from the user:
{context}

Question: {query}

Provide:
- Clear, accurate explanation
- Concrete examples
- Common misconceptions if any
- Further reading or next steps""",

    "creative": """You are answering as a {role}.

Context from the user:
{context}

Question: {query}

Provide:
- Multiple creative approaches
- Feasibility assessment for each
- Recommended approach with rationale
- Implementation starting points""",

    "general": """You are answering as a {role}.

Context from the user:
{context}

Question: {query}

Provide a comprehensive, well-structured answer with specific examples and actionable recommendations where applicable.""",
}


def classify_query(query: str) -> str:
    """Classify a query into a type using keyword matching."""
    query_lower = query.lower()
    scores = {}
    for qtype, config in QUERY_TYPES.items():
        score = sum(1 for kw in config["keywords"] if kw in query_lower)
        scores[qtype] = score

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general"
    return best


def generate_clarifying_questions(query: str, query_type: str) -> List[str]:
    """Return targeted clarifying questions based on query type."""
    return QUESTIONS_BY_TYPE.get(query_type, QUESTIONS_BY_TYPE["general"])


def auto_assign_roles(query_type: str, council_models: List[str]) -> Dict[str, str]:
    """Auto-assign expert roles to council models based on query type."""
    type_config = QUERY_TYPES.get(query_type, {})
    role_list = type_config.get("roles", {}).get("default", ["Expert", "Analyst", "Reviewer"])

    roles = {}
    for i, model in enumerate(council_models):
        roles[model] = role_list[i % len(role_list)]
    return roles


def build_refined_prompt(
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

    template = PROMPT_TEMPLATES.get(query_type, PROMPT_TEMPLATES["general"])
    return template.format(role=role, context=context, query=query)
