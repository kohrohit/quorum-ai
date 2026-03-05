# Quorum AI

A multi-LLM deliberation platform where AI models debate, reach consensus, and deliver one unified answer.

Instead of asking a single LLM, Quorum AI assembles a **council** of models that deliberate through structured rounds — debating, revising, voting, and converging on the best possible answer.

## How It Works

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│  Stage 1: Individual Responses  │  Each model answers independently
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│  Stage 2: Consensus Loop        │  Models see each other's answers,
│                                 │  revise, and vote on agreement
│  Round 1-3 → Unanimous needed   │
│  Round 4-5 → 2/3 majority       │
│  After 5   → Chairman decides   │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│  Stage 3: Final Answer          │  Consensus synthesis or
│                                 │  chairman's decision
└─────────────────────────────────┘
```

## Features

### Iterative Consensus
Models don't just answer once — they deliberate. Each round, models see all other responses, revise their own, and vote on whether they agree. Consensus thresholds tighten over rounds.

### Configurable Council
Pick which models sit on the council, who chairs it, and how many rounds to run — all from the UI. Settings persist across sessions.

**Supported models:**
| Provider | Models |
|----------|--------|
| OpenAI | GPT-4o, GPT-4o Mini, GPT-4.1, GPT-4.1 Mini, o3-mini |
| Google | Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 2.0 Flash |
| Anthropic | Claude Sonnet 4.5, Claude Haiku 3.5 |

### Expert Roles
Assign perspectives to each model — Security Expert, UX Designer, Backend Engineer, or any custom role. Models argue from their assigned viewpoint for richer deliberation.

### Cost & Latency Dashboard
Track tokens used, estimated cost, and latency per model per query. See which models are expensive and which are fast. Per-model breakdown table with totals.

### Export
Download any conversation as a formatted markdown file — includes all stages, consensus rounds, votes, and the final answer.

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) package manager

### 1. Install Dependencies

```bash
# Backend
uv sync

# Frontend
cd frontend
npm install
cd ..
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
```

You only need keys for the providers whose models you want to use.

### 3. Run

**Option 1: Start script**
```bash
./start.sh
```

**Option 2: Run manually**

```bash
# Terminal 1 — Backend
uv run python -m backend.main

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open **http://localhost:5173** in your browser.

## Configuration

### Via UI
Click **Settings** in the sidebar to:
- Select council models
- Choose chairman model
- Assign expert roles
- Set consensus rules (max rounds, unanimous threshold)

### Via Code
Edit `backend/config.py` to modify the available models catalog or default settings.

## Tech Stack

- **Backend:** FastAPI, async httpx, direct provider APIs (OpenAI, Google, Anthropic)
- **Frontend:** React + Vite, react-markdown
- **Storage:** JSON files in `data/conversations/`
- **Package Management:** uv (Python), npm (JavaScript)

## Project Structure

```
├── backend/
│   ├── config.py          # Models catalog, API config, pricing
│   ├── council.py         # Consensus loop, expert roles, metrics
│   ├── main.py            # FastAPI endpoints, streaming
│   ├── openrouter.py      # Multi-provider LLM client
│   ├── settings.py        # Settings persistence
│   └── storage.py         # Conversation storage
├── frontend/src/
│   ├── App.jsx            # Main app with settings & export
│   ├── api.js             # API client
│   └── components/
│       ├── ChatInterface  # Message display & input
│       ├── Stage1         # Individual responses with role tags
│       ├── Stage2         # Consensus rounds, votes
│       ├── Stage3         # Final answer with consensus badge
│       ├── MetricsDashboard # Cost & latency tracking
│       ├── SettingsPanel  # Council configuration UI
│       └── Sidebar        # Conversations, settings, export
├── .env                   # API keys (not committed)
└── start.sh               # Quick start script
```

## License

MIT
