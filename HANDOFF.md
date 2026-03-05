# Quorum AI — Handoff for Next Session

## Done (pushed to master + quality)
- Iterative consensus loop (unanimous → 2/3 majority → chairman)
- Configurable council via UI (models, chairman, roles, consensus rules)
- Expert roles system
- Cost & latency dashboard
- Markdown export
- Prompt refinement loop (LLM-driven classification, clarifying questions, auto-roles)
- Delete conversations
- Branding (Quorum AI, logo, favicon)

## Remaining Sprints

### Sprint 2: Multi-turn + Error Recovery
- **Multi-turn**: Pass last 5 conversation exchanges as context to Stage 1. Update `council.py` stage1_collect_responses to accept conversation_history. Update main.py streaming endpoint to extract prior exchanges from storage. Remove `conversation.messages.length === 0` condition on input form in ChatInterface.jsx.
- **Error Recovery**: Update openrouter.py query_model to return `{"error": "msg"}` on failure instead of None. Show failed model tabs with red indicator in Stage1.jsx.

### Sprint 3: Local Folder Context + Streaming Prep
- **Folders**: Create backend/indexer.py (scan_folder, read_file_contents, get_relevant_files with keyword matching). Add endpoints: POST /api/folder/connect, GET /api/folder/status, POST /api/folder/disconnect. Inject file context into query before Stage 1. Create FolderPicker component in sidebar.
- **Streaming Prep**: Add query_model_streaming function to openrouter.py (don't wire in yet).

### Sprint 4: Dissent Report + Council Presets
- **Dissent**: Collect NO votes with explanations across all rounds in run_consensus_loop. Return as dissent_report. Create DissentReport component (amber/orange theme, collapsible). Show between Stage3 and MetricsDashboard.
- **Presets**: Add get_presets/save_preset/delete_preset to settings.py. 3 built-in presets: Fast Council, Deep Research, Code Review. Endpoints: GET/POST/DELETE /api/presets, POST /api/presets/{name}/apply. Add presets section to SettingsPanel.

### Sprint 5: Leaderboard + Dark Mode + Search
- **Leaderboard**: Create backend/leaderboard.py scanning all conversations. Track consensus adoption rate, agreement rate, tokens, cost per model. GET /api/leaderboard endpoint. Leaderboard component accessible from sidebar.
- **Dark Mode**: CSS custom properties at :root, override in [data-theme="dark"]. Theme toggle in sidebar, persist to localStorage.
- **Search**: GET /api/conversations/search?q=query. search_conversations in storage.py. Search input in sidebar.

## Agent Transcripts (detailed implementation plans)
- Sprint 2: /tmp/claude-1001/-home-rohit-Desktop-agents/tasks/ab40eede70d94a703.output
- Sprint 3: /tmp/claude-1001/-home-rohit-Desktop-agents/tasks/a87aad6bd021d3d9d.output
- Sprint 4: /tmp/claude-1001/-home-rohit-Desktop-agents/tasks/a1e85b9430347483c.output
- Sprint 5: /tmp/claude-1001/-home-rohit-Desktop-agents/tasks/abe468877b1a8fb2b.output
