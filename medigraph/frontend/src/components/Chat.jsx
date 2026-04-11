import { useState, useRef, useEffect, useCallback } from 'react';
import { sendChat } from '../services/api';
import './Chat.css';

// Generate unique message IDs
let messageIdCounter = 0;
const generateMessageId = () => `msg_${++messageIdCounter}_${Date.now()}`;

function Chat({ onDiseaseSelect }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedExplanations, setExpandedExplanations] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const messagesEndRef = useRef(null);
  const lastBotMessageIdRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = useCallback(async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading || isSubmitting) return;

    const userMessageId = generateMessageId();
    const userMessage = { id: userMessageId, role: 'user', content: input };

    setMessages((prev) => {
      // Prevent duplicate user messages
      const lastMsg = prev[prev.length - 1];
      if (lastMsg?.role === 'user' && lastMsg.content === input) {
        return prev;
      }
      return [...prev, userMessage];
    });

    setInput('');
    setLoading(true);
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await sendChat(input);

      // Prevent duplicate bot responses
      setMessages((prev) => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.role === 'bot' && lastMsg.content === response.response) {
          return prev;
        }

        const botMessageId = generateMessageId();
        lastBotMessageIdRef.current = botMessageId;

        const botMessage = {
          id: botMessageId,
          role: 'bot',
          content: response.response,
          data: response.data,
          intent: response.intent,
          confidence: response.confidence,
          confidenceLabel: response.confidence_label,
          explanation: response.explanation,
          suggestions: response.suggestions || [],
          llmEnhanced: response.llm_enhanced
        };

        return [...prev, botMessage];
      });

      // If disease info returned, notify graph
      // Handle both object (get_info) and string (get_symptoms/get_treatments)
      if (response.data?.disease) {
        const diseaseName = typeof response.data.disease === 'string'
          ? response.data.disease
          : response.data.disease.name;
        if (diseaseName) {
          onDiseaseSelect(diseaseName);
        }
      }

      // Also update graph if symptoms or treatments returned (show disease subgraph)
      if (response.data?.symptoms || response.data?.treatments) {
        const diseaseName = typeof response.data.disease === 'string'
          ? response.data.disease
          : response.data.disease?.name;
        if (diseaseName) {
          onDiseaseSelect(diseaseName);
        }
      }
    } catch (err) {
      setError('Failed to get response. Is the backend running?');
    } finally {
      setLoading(false);
      setIsSubmitting(false);
    }
  }, [input, loading, isSubmitting, onDiseaseSelect]);

  const handleQuickQuery = (query) => {
    setInput(query);
  };

  const toggleExplanation = (msgId) => {
    setExpandedExplanations((prev) => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return '#10b981'; // green
    if (confidence >= 0.6) return '#3b82f6'; // blue
    if (confidence >= 0.4) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Medigraph Assistant</h2>
        <p className="subtitle">Ask about diseases, symptoms, treatments, and drug interactions</p>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Hello! I can help you explore medical knowledge.</p>
            <p>Try asking:</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.role === 'bot' && <span className="bot-avatar">🩺</span>}
              {msg.role === 'user' && <span className="user-avatar">👤</span>}
              <div className="message-text">
                <p>{msg.content}</p>
                {msg.data && msg.data.count !== undefined && (
                  <span className="result-count">
                    {msg.data.count} result{msg.data.count !== 1 ? 's' : ''} found
                  </span>
                )}

                {/* Confidence indicator */}
                {msg.role === 'bot' && msg.confidence !== undefined && (
                  <div className="confidence-indicator">
                    <span
                      className="confidence-dot"
                      style={{ backgroundColor: getConfidenceColor(msg.confidence) }}
                    />
                    <span className="confidence-label">{msg.confidenceLabel}</span>
                    {msg.llmEnhanced && <span className="llm-badge">LLM</span>}
                  </div>
                )}

                {/* Explanation toggle */}
                {msg.role === 'bot' && msg.explanation && (
                  <div className="explanation-container">
                    <button
                      className="explanation-toggle"
                      onClick={() => toggleExplanation(msg.id)}
                    >
                      {expandedExplanations[msg.id] ? 'Hide' : 'Why?'} this answer
                    </button>
                    {expandedExplanations[msg.id] && (
                      <div className="explanation-text">
                        {msg.explanation}
                      </div>
                    )}
                  </div>
                )}

                {/* Suggestions */}
                {msg.role === 'bot' && msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="suggestions">
                    <span className="suggestions-label">You might also ask:</span>
                    {msg.suggestions.map((suggestion, sIdx) => (
                      <button
                        key={`${msg.id}-suggestion-${sIdx}`}
                        className="suggestion-chip"
                        onClick={() => handleQuickQuery(suggestion)}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message bot">
            <div className="message-content">
              <span className="bot-avatar">🩺</span>
              <div className="message-text">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="message bot error">
            <div className="message-content">
              <span className="bot-avatar">⚠️</span>
              <div className="message-text">
                <p>{error}</p>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="quick-queries">
        <button onClick={() => handleQuickQuery("What are symptoms of Hypertension?")}>
          Symptoms
        </button>
        <button onClick={() => handleQuickQuery("How is Diabetes treated?")}>
          Treatments
        </button>
        <button onClick={() => handleQuickQuery("What diseases cause chest pain?")}>
          By Symptom
        </button>
        <button onClick={() => handleQuickQuery("Does Aspirin interact with Warfarin?")}>
          Interactions
        </button>
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about diseases, symptoms, treatments..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? '...' : 'Send'}
        </button>
      </form>
    </div>
  );
}

export default Chat;
