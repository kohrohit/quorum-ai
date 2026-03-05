"""FastAPI backend for Quorum AI."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio

from . import storage
from .council import stage1_collect_responses, run_consensus_loop, generate_conversation_title
from .settings import load_settings, update_settings
from .config import AVAILABLE_MODELS, MODEL_COSTS

app = FastAPI(title="Quorum AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    pass


class SendMessageRequest(BaseModel):
    content: str


class UpdateSettingsRequest(BaseModel):
    council_models: Optional[List[str]] = None
    chairman_model: Optional[str] = None
    roles: Optional[Dict[str, str]] = None
    consensus: Optional[Dict[str, Any]] = None


class ConversationMetadata(BaseModel):
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


# ── Core endpoints ──

@app.get("/")
async def root():
    return {"status": "ok", "service": "Quorum AI API"}


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    conversation_id = str(uuid.uuid4())
    return storage.create_conversation(conversation_id)


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


# ── Settings endpoints ──

@app.get("/api/settings")
async def get_settings():
    settings = load_settings()
    return {
        **settings,
        "available_models": AVAILABLE_MODELS,
        "model_costs": MODEL_COSTS,
    }


@app.put("/api/settings")
async def put_settings(request: UpdateSettingsRequest):
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    updated = update_settings(updates)
    return {
        **updated,
        "available_models": AVAILABLE_MODELS,
        "model_costs": MODEL_COSTS,
    }


# ── Export endpoint ──

@app.get("/api/conversations/{conversation_id}/export")
async def export_conversation(conversation_id: str):
    """Export a conversation as markdown."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    md = _conversation_to_markdown(conversation)
    return Response(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="council-{conversation_id[:8]}.md"'}
    )


def _conversation_to_markdown(conv: Dict[str, Any]) -> str:
    """Convert a conversation to markdown format."""
    lines = [
        f"# Quorum AI: {conv.get('title', 'Conversation')}",
        f"*Created: {conv.get('created_at', 'Unknown')}*\n",
        "---\n",
    ]

    for msg in conv.get("messages", []):
        if msg["role"] == "user":
            lines.append(f"## User\n\n{msg['content']}\n")
        else:
            lines.append("## Council Response\n")

            # Stage 1
            if msg.get("stage1"):
                lines.append("### Stage 1: Individual Responses\n")
                for r in msg["stage1"]:
                    model_name = r["model"].split("/")[1] if "/" in r["model"] else r["model"]
                    role_str = f" ({r['role']})" if r.get("role") else ""
                    lines.append(f"#### {model_name}{role_str}\n\n{r['response']}\n")

            # Stage 2 (consensus rounds)
            if msg.get("stage2") and isinstance(msg["stage2"], list) and len(msg["stage2"]) > 0:
                first = msg["stage2"][0]
                if isinstance(first, dict) and "round" in first:
                    lines.append("### Stage 2: Consensus Deliberation\n")
                    for rd in msg["stage2"]:
                        yes = sum(1 for v in rd.get("votes", []) if v.get("vote") == "YES")
                        total = len(rd.get("votes", []))
                        status = "Consensus" if rd.get("consensus_reached") else "No consensus"
                        lines.append(f"**Round {rd['round']}** ({rd.get('threshold', '?')}): {yes}/{total} agreed — {status}\n")

            # Stage 3
            if msg.get("stage3"):
                s3 = msg["stage3"]
                model_name = s3["model"].split("/")[1] if "/" in s3.get("model", "") else s3.get("model", "")
                lines.append(f"### Final Answer (by {model_name})\n\n{s3.get('response', '')}\n")

        lines.append("---\n")

    return "\n".join(lines)


# ── Streaming message endpoint ──

@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    is_first_message = len(conversation["messages"]) == 0
    settings = load_settings()

    queue = asyncio.Queue()

    async def run_council():
        try:
            await queue.put(json.dumps({"type": "stage1_start"}))
            storage.add_user_message(conversation_id, request.content)

            council_models = settings.get("council_models")
            chairman_model = settings.get("chairman_model")
            roles = settings.get("roles", {})
            consensus_config = settings.get("consensus", {})

            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(
                    generate_conversation_title(request.content, council_models)
                )

            stage1_results, stage1_metrics = await stage1_collect_responses(
                request.content, council_models, roles
            )
            await queue.put(json.dumps({
                "type": "stage1_complete",
                "data": stage1_results,
                "metrics": stage1_metrics,
            }))

            await queue.put(json.dumps({"type": "consensus_start"}))

            async def on_round_complete(round_data):
                await queue.put(json.dumps({
                    "type": "consensus_round",
                    "data": round_data,
                }))

            consensus_data = await run_consensus_loop(
                request.content,
                stage1_results,
                on_round_complete,
                council_models=council_models,
                chairman_model=chairman_model,
                roles=roles,
                consensus_config=consensus_config,
            )

            await queue.put(json.dumps({
                "type": "final_complete",
                "data": consensus_data["final_answer"],
                "consensus_type": consensus_data["consensus_type"],
                "final_round": consensus_data["final_round"],
                "total_rounds": len(consensus_data["rounds"]),
                "metrics": consensus_data.get("metrics", {}),
            }))

            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                await queue.put(json.dumps({"type": "title_complete", "data": {"title": title}}))

            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                consensus_data.get("rounds", []),
                consensus_data["final_answer"],
            )

            await queue.put(json.dumps({"type": "complete"}))

        except Exception as e:
            await queue.put(json.dumps({"type": "error", "message": str(e)}))

        await queue.put(None)

    async def stream():
        task = asyncio.create_task(run_council())
        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {item}\n\n"
        await task

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
