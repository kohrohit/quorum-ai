import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onOpenSettings,
  onExport,
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title-row">
          <h1>LLM Council</h1>
          <button className="settings-btn" onClick={onOpenSettings} title="Council Settings">
            Settings
          </button>
        </div>
        <button className="new-conversation-btn" onClick={onNewConversation}>
          + New Conversation
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">No conversations yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId ? 'active' : ''
              }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-title">
                {conv.title || 'New Conversation'}
              </div>
              <div className="conversation-item-footer">
                <span className="conversation-meta">
                  {conv.message_count} messages
                </span>
                {conv.id === currentConversationId && conv.message_count > 0 && (
                  <button
                    className="export-btn"
                    onClick={(e) => { e.stopPropagation(); onExport(conv.id); }}
                    title="Export as Markdown"
                  >
                    Export
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
