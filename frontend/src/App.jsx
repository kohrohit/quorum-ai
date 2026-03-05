import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import SettingsPanel from './components/SettingsPanel';
import PromptRefinement from './components/PromptRefinement';
import { api } from './api';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [refinementData, setRefinementData] = useState(null);
  const [pendingQuery, setPendingQuery] = useState(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, title: 'New Conversation', message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleExport = (conversationId) => {
    window.open(api.getExportUrl(conversationId), '_blank');
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleSendMessage = async (content) => {
    // Start refinement flow
    if (!refinementData) {
      try {
        const data = await api.refineQuery(content);
        setRefinementData(data);
        setPendingQuery(content);
        return;
      } catch (e) {
        // If refinement fails, send directly
        console.error('Refinement failed, sending directly:', e);
      }
    }
    setRefinementData(null);
    setPendingQuery(null);
    await _sendToCouncil(content);
  };

  const handleRefinementFinalize = async (answers, roles) => {
    try {
      const result = await api.refineFinalize(pendingQuery, refinementData.query_type, answers, roles);
      setRefinementData(null);
      await _sendToCouncil(pendingQuery, result.refined_prompt, roles);
      setPendingQuery(null);
    } catch (e) {
      console.error('Finalize failed:', e);
    }
  };

  const handleRefinementSkip = () => {
    const query = pendingQuery;
    setRefinementData(null);
    setPendingQuery(null);
    _sendToCouncil(query);
  };

  const _sendToCouncil = async (content, refinedPrompt, autoRoles) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        consensusRounds: [],
        stage3: null,
        consensusType: null,
        finalRound: null,
        totalRounds: null,
        stage1Metrics: null,
        finalMetrics: null,
        loading: {
          stage1: false,
          consensus: false,
          stage3: false,
        },
      };

      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              messages[messages.length - 1].loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage1 = event.data;
              lastMsg.stage1Metrics = event.metrics || null;
              lastMsg.loading.stage1 = false;
              return { ...prev, messages };
            });
            break;

          case 'consensus_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              messages[messages.length - 1].loading.consensus = true;
              return { ...prev, messages };
            });
            break;

          case 'consensus_round':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.consensusRounds = [...(lastMsg.consensusRounds || []), event.data];
              return { ...prev, messages };
            });
            break;

          case 'final_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage3 = event.data;
              lastMsg.consensusType = event.consensus_type;
              lastMsg.finalRound = event.final_round;
              lastMsg.totalRounds = event.total_rounds;
              lastMsg.finalMetrics = event.metrics || null;
              lastMsg.loading.consensus = false;
              lastMsg.loading.stage3 = false;
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            loadConversations();
            break;

          case 'complete':
            loadConversations();
            setIsLoading(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      }, refinedPrompt, autoRoles);
    } catch (error) {
      console.error('Failed to send message:', error);
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onOpenSettings={() => setSettingsOpen(true)}
        onExport={handleExport}
        onDelete={handleDeleteConversation}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        refinementData={refinementData}
        pendingQuery={pendingQuery}
        onRefinementFinalize={handleRefinementFinalize}
        onRefinementSkip={handleRefinementSkip}
      />
      <SettingsPanel
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  );
}

export default App;
