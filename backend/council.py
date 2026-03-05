"""LLM Council orchestration with iterative consensus, expert roles, and metrics."""

from typing import List, Dict, Any, Tuple, Optional
from .openrouter import query_models_parallel, query_model
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL, DEFAULT_CONSENSUS_CONFIG, MODEL_COSTS


def _build_role_prefix(model: str, roles: Dict[str, str]) -> str:
    """Build a role instruction prefix for a model."""
    role = roles.get(model, "")
    if role:
        return f"You are acting as: {role}. Respond from this expert perspective.\n\n"
    return ""


def _estimate_cost(model: str, tokens: Dict[str, int]) -> float:
    """Estimate cost in USD for a model query."""
    costs = MODEL_COSTS.get(model, {"input": 0, "output": 0})
    input_cost = (tokens.get("input", 0) / 1_000_000) * costs["input"]
    output_cost = (tokens.get("output", 0) / 1_000_000) * costs["output"]
    return round(input_cost + output_cost, 6)


def _extract_metrics(model: str, response: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract token/cost/latency metrics from a response."""
    if response is None:
        return {"tokens": {"input": 0, "output": 0}, "latency_ms": 0, "cost_usd": 0}
    tokens = response.get("tokens", {"input": 0, "output": 0})
    return {
        "tokens": tokens,
        "latency_ms": response.get("latency_ms", 0),
        "cost_usd": _estimate_cost(model, tokens),
    }


async def stage1_collect_responses(
    user_query: str,
    council_models: List[str] = None,
    roles: Dict[str, str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Stage 1: Collect individual responses. Returns (results, metrics)."""
    models = council_models or COUNCIL_MODELS
    roles = roles or {}

    messages_per_model = {}
    for model in models:
        prefix = _build_role_prefix(model, roles)
        content = f"{prefix}{user_query}" if prefix else user_query
        messages_per_model[model] = [{"role": "user", "content": content}]

    # Query all models in parallel
    import asyncio
    tasks = [query_model(m, messages_per_model[m]) for m in models]
    raw_responses = await asyncio.gather(*tasks)
    responses = {m: r for m, r in zip(models, raw_responses)}

    stage1_results = []
    stage1_metrics = {}
    for model, response in responses.items():
        metrics = _extract_metrics(model, response)
        stage1_metrics[model] = metrics
        if response is not None:
            stage1_results.append({
                "model": model,
                "response": response.get("content", ""),
                "role": roles.get(model, ""),
            })

    return stage1_results, stage1_metrics


async def _revise_responses(
    user_query: str,
    current_responses: List[Dict[str, Any]],
    round_num: int,
    roles: Dict[str, str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Ask each model to revise. Returns (revised_responses, metrics)."""
    roles = roles or {}
    revised = []
    metrics = {}

    for target in current_responses:
        others_text = "\n\n".join([
            f"**{r['model'].split('/')[1]}**: {r['response']}"
            for r in current_responses if r['model'] != target['model']
        ])

        role_prefix = _build_role_prefix(target['model'], roles)
        prompt = f"""{role_prefix}You are in round {round_num} of a council deliberation on this question:

Question: {user_query}

Your previous answer:
{target['response']}

Other council members' answers:
{others_text}

Consider the other perspectives carefully. Revise your answer to incorporate valid points from others while maintaining accuracy. If you already agree with the group consensus, restate it clearly. Aim to converge on the best possible answer.

Provide your revised answer:"""

        messages = [{"role": "user", "content": prompt}]
        response = await query_model(target['model'], messages)
        metrics[target['model']] = _extract_metrics(target['model'], response)

        if response is not None:
            revised.append({
                "model": target['model'],
                "response": response.get("content", ""),
                "role": target.get("role", ""),
            })
        else:
            revised.append(target)

    return revised, metrics


async def _check_agreement(
    user_query: str,
    current_responses: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Check if models agree. Returns (votes, metrics)."""
    all_responses_text = "\n\n".join([
        f"**{r['model'].split('/')[1]}**: {r['response']}"
        for r in current_responses
    ])

    votes = []
    metrics = {}
    for target in current_responses:
        prompt = f"""You are evaluating whether a council of AI models has reached consensus on this question:

Question: {user_query}

All current responses:
{all_responses_text}

Do all responses substantially agree on the core answer? Minor wording differences are fine — focus on whether the key conclusions, facts, and recommendations align.

You MUST reply with exactly one word on the first line: YES or NO
Then optionally explain briefly."""

        messages = [{"role": "user", "content": prompt}]
        response = await query_model(target['model'], messages, timeout=30.0)
        metrics[target['model']] = _extract_metrics(target['model'], response)

        vote = "NO"
        explanation = ""
        if response is not None:
            text = response.get("content", "").strip()
            first_line = text.split('\n')[0].strip().upper()
            if first_line.startswith("YES"):
                vote = "YES"
            explanation = '\n'.join(text.split('\n')[1:]).strip()

        votes.append({
            "model": target['model'],
            "vote": vote,
            "explanation": explanation,
        })

    return votes, metrics


def _check_consensus(votes: List[Dict[str, Any]], round_num: int, config: Dict) -> bool:
    """Check if consensus is reached based on round number."""
    yes_count = sum(1 for v in votes if v['vote'] == 'YES')
    total = len(votes)
    if total == 0:
        return False

    unanimous_rounds = config.get("unanimous_rounds", 3)
    if round_num <= unanimous_rounds:
        return yes_count == total
    else:
        return yes_count >= (2 * total) / 3


async def run_consensus_loop(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    on_round_complete=None,
    council_models: List[str] = None,
    chairman_model: str = None,
    roles: Dict[str, str] = None,
    consensus_config: Dict = None,
) -> Dict[str, Any]:
    """Run the consensus loop with metrics tracking."""
    config = consensus_config or DEFAULT_CONSENSUS_CONFIG
    max_rounds = config.get("max_rounds", 5)
    chairman = chairman_model or CHAIRMAN_MODEL
    roles = roles or {}

    current_responses = stage1_results
    rounds_data = []
    all_metrics = []

    for round_num in range(1, max_rounds + 1):
        round_metrics = {}

        if round_num > 1:
            current_responses, revision_metrics = await _revise_responses(
                user_query, current_responses, round_num, roles
            )
            round_metrics["revision"] = revision_metrics

        votes, vote_metrics = await _check_agreement(user_query, current_responses)
        round_metrics["voting"] = vote_metrics

        consensus = _check_consensus(votes, round_num, config)
        unanimous_rounds = config.get("unanimous_rounds", 3)
        threshold = "unanimous" if round_num <= unanimous_rounds else "2/3 majority"

        round_data = {
            "round": round_num,
            "responses": current_responses,
            "votes": votes,
            "consensus_reached": consensus,
            "threshold": threshold,
            "metrics": round_metrics,
        }
        rounds_data.append(round_data)
        all_metrics.append(round_metrics)

        if on_round_complete:
            await on_round_complete(round_data)

        if consensus:
            final, final_metrics = await _synthesize_consensus(user_query, current_responses, chairman)
            consensus_type = "unanimous" if round_num <= unanimous_rounds else "majority"
            return {
                "rounds": rounds_data,
                "consensus_reached": True,
                "final_round": round_num,
                "consensus_type": consensus_type,
                "final_answer": final,
                "metrics": _aggregate_metrics(all_metrics, final_metrics),
            }

    # Chairman decides
    chairman_answer, final_metrics = await _chairman_decides(user_query, current_responses, rounds_data, chairman)
    return {
        "rounds": rounds_data,
        "consensus_reached": False,
        "final_round": None,
        "consensus_type": "chairman",
        "final_answer": chairman_answer,
        "metrics": _aggregate_metrics(all_metrics, final_metrics),
    }


def _aggregate_metrics(round_metrics: List[Dict], final_metrics: Dict) -> Dict[str, Any]:
    """Aggregate all metrics across rounds into a summary."""
    per_model = {}
    total_cost = 0
    total_tokens = {"input": 0, "output": 0}
    total_latency = 0

    for rm in round_metrics:
        for phase in ["revision", "voting"]:
            phase_data = rm.get(phase, {})
            for model, m in phase_data.items():
                if model not in per_model:
                    per_model[model] = {"tokens": {"input": 0, "output": 0}, "cost_usd": 0, "latency_ms": 0, "calls": 0}
                per_model[model]["tokens"]["input"] += m["tokens"]["input"]
                per_model[model]["tokens"]["output"] += m["tokens"]["output"]
                per_model[model]["cost_usd"] += m["cost_usd"]
                per_model[model]["latency_ms"] += m["latency_ms"]
                per_model[model]["calls"] += 1
                total_cost += m["cost_usd"]
                total_tokens["input"] += m["tokens"]["input"]
                total_tokens["output"] += m["tokens"]["output"]
                total_latency += m["latency_ms"]

    # Add final synthesis metrics
    for model, m in final_metrics.items():
        if model not in per_model:
            per_model[model] = {"tokens": {"input": 0, "output": 0}, "cost_usd": 0, "latency_ms": 0, "calls": 0}
        per_model[model]["tokens"]["input"] += m["tokens"]["input"]
        per_model[model]["tokens"]["output"] += m["tokens"]["output"]
        per_model[model]["cost_usd"] += m["cost_usd"]
        per_model[model]["latency_ms"] += m["latency_ms"]
        per_model[model]["calls"] += 1
        total_cost += m["cost_usd"]
        total_tokens["input"] += m["tokens"]["input"]
        total_tokens["output"] += m["tokens"]["output"]
        total_latency += m["latency_ms"]

    return {
        "per_model": {k: {**v, "cost_usd": round(v["cost_usd"], 6)} for k, v in per_model.items()},
        "total_cost_usd": round(total_cost, 6),
        "total_tokens": total_tokens,
        "total_latency_ms": total_latency,
    }


async def _synthesize_consensus(
    user_query: str,
    agreed_responses: List[Dict[str, Any]],
    chairman: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Synthesize consensus answer. Returns (result, metrics)."""
    responses_text = "\n\n".join([
        f"**{r['model'].split('/')[1]}**: {r['response']}"
        for r in agreed_responses
    ])

    prompt = f"""The council has reached consensus on this question:

Question: {user_query}

All council members' agreed responses:
{responses_text}

Synthesize these into a single, clear, comprehensive answer that captures the consensus:"""

    messages = [{"role": "user", "content": prompt}]
    response = await query_model(chairman, messages)
    metrics = {chairman: _extract_metrics(chairman, response)}

    if response is None:
        return {
            "model": chairman,
            "response": agreed_responses[0]["response"] if agreed_responses else "Error generating synthesis."
        }, metrics

    return {
        "model": chairman,
        "response": response.get("content", "")
    }, metrics


async def _chairman_decides(
    user_query: str,
    final_responses: List[Dict[str, Any]],
    rounds_data: List[Dict[str, Any]],
    chairman: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Chairman makes final decision. Returns (result, metrics)."""
    responses_text = "\n\n".join([
        f"**{r['model'].split('/')[1]}**: {r['response']}"
        for r in final_responses
    ])

    rounds_summary = ""
    for rd in rounds_data:
        yes_count = sum(1 for v in rd['votes'] if v['vote'] == 'YES')
        total = len(rd['votes'])
        rounds_summary += f"Round {rd['round']} ({rd['threshold']}): {yes_count}/{total} agreed\n"

    prompt = f"""You are the Chairman of an LLM Council. The council failed to reach consensus after {len(rounds_data)} rounds of deliberation.

Question: {user_query}

Deliberation summary:
{rounds_summary}

Final responses from council members:
{responses_text}

As Chairman, you have the deciding vote. Provide the definitive answer, weighing all perspectives and the deliberation history:"""

    messages = [{"role": "user", "content": prompt}]
    response = await query_model(chairman, messages)
    metrics = {chairman: _extract_metrics(chairman, response)}

    if response is None:
        return {
            "model": chairman,
            "response": "Error: Unable to generate chairman's decision."
        }, metrics

    return {
        "model": chairman,
        "response": response.get("content", "")
    }, metrics


async def generate_conversation_title(user_query: str, council_models: List[str] = None) -> str:
    """Generate a short title for a conversation."""
    models = council_models or COUNCIL_MODELS
    title_prompt = """Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: """ + user_query + "\n\nTitle:"

    messages = [{"role": "user", "content": title_prompt}]
    response = await query_model(models[0], messages, timeout=30.0)

    if response is None:
        return "New Conversation"

    title = response.get("content", "New Conversation").strip().strip('"\'')
    if len(title) > 50:
        title = title[:47] + "..."
    return title
