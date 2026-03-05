/**
 * API client for the Quorum AI backend.
 */

const API_BASE = 'http://localhost:8001';

export const api = {
  async listConversations() {
    const response = await fetch(`${API_BASE}/api/conversations`);
    if (!response.ok) throw new Error('Failed to list conversations');
    return response.json();
  },

  async createConversation() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!response.ok) throw new Error('Failed to create conversation');
    return response.json();
  },

  async getConversation(conversationId) {
    const response = await fetch(`${API_BASE}/api/conversations/${conversationId}`);
    if (!response.ok) throw new Error('Failed to get conversation');
    return response.json();
  },

  async sendMessageStream(conversationId, content, onEvent, refinedPrompt, autoRoles) {
    const body = { content };
    if (refinedPrompt) body.refined_prompt = refinedPrompt;
    if (autoRoles) body.auto_roles = autoRoles;
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }
    );
    if (!response.ok) throw new Error('Failed to send message');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));
            onEvent(event.type, event);
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        }
      }
    }
  },

  // ── Delete ──

  async deleteConversation(conversationId) {
    const response = await fetch(`${API_BASE}/api/conversations/${conversationId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete conversation');
    return response.json();
  },

  // ── Prompt Refinement ──

  async refineQuery(content) {
    const response = await fetch(`${API_BASE}/api/refine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) throw new Error('Failed to refine query');
    return response.json();
  },

  async refineFinalize(content, queryType, answers, roles) {
    const response = await fetch(`${API_BASE}/api/refine/finalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, query_type: queryType, answers, roles }),
    });
    if (!response.ok) throw new Error('Failed to finalize refinement');
    return response.json();
  },

  // ── Settings ──

  async getSettings() {
    const response = await fetch(`${API_BASE}/api/settings`);
    if (!response.ok) throw new Error('Failed to get settings');
    return response.json();
  },

  async updateSettings(settings) {
    const response = await fetch(`${API_BASE}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error('Failed to update settings');
    return response.json();
  },

  // ── Export ──

  getExportUrl(conversationId) {
    return `${API_BASE}/api/conversations/${conversationId}/export`;
  },
};
