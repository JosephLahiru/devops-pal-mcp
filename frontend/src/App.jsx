import React, { useState, useEffect, useRef } from "react";
import { FiSend, FiRefreshCw, FiMessageSquare, FiUser } from "react-icons/fi";

const API_URL = "http://localhost:5000/api";

// Loading spinner component
const LoadingSpinner = () => (
  <div className="loading-spinner">
    <FiRefreshCw className="animate-spin" />
  </div>
);

// Message component
const Message = ({ role, content }) => {
  // Convert newlines to <br> elements for proper rendering
  const renderContent = (text) => {
    if (typeof text !== 'string') return text; // Return as is if not a string
    return text.split('\n').map((line, i, arr) => (
      <React.Fragment key={i}>
        {line}
        {i < arr.length - 1 && <br />}
      </React.Fragment>
    ));
  };

  return (
    <div className={`message ${role}`}>
      <div className="message-avatar">
        {role === 'user' ? <FiUser /> : <FiMessageSquare />}
      </div>
      <div className="message-content">
        {renderContent(content)}
      </div>
    </div>
  );
};

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const startSession = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/start_session`, {
        method: "POST",
        credentials: "include",
      });
      const data = await res.json();
      setSessionId(data.session_id);
      setMessages([]);
    } catch (error) {
      console.error("Error starting session:", error);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;
    
    const userMsg = { role: "user", content: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setLoading(true);
    setInput("");
    
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ session_id: sessionId, message: userMsg.content }),
      });
      
      if (!res.ok) throw new Error('Network response was not ok');
      
      const data = await res.json();
      if (data.response) {
        setMessages((msgs) => [
          ...msgs,
          { role: "assistant", content: data.response },
        ]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      // Show error message to user
      setMessages(msgs => [
        ...msgs, 
        { 
          role: "assistant", 
          content: "Sorry, I encountered an error. Please try again." 
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>DevOps Pal</h1>
        <p>Your AI-powered DevOps assistant</p>
      </header>
      
      <main className="chat-container">
        {!sessionId ? (
          <div className="welcome-screen">
            <h2>Welcome to DevOps Pal</h2>
            <p>Get help with your DevOps tasks and questions</p>
            <button 
              className="primary-button" 
              onClick={startSession}
              disabled={loading}
            >
              {loading ? 'Starting...' : 'Start New Chat'}
            </button>
          </div>
        ) : (
          <>
            <div className="messages-container">
              {messages.length === 0 ? (
                <div className="empty-state">
                  <FiMessageSquare size={48} />
                  <h3>How can I help you today?</h3>
                  <p>Ask me anything about DevOps, CI/CD, cloud, or infrastructure.</p>
                </div>
              ) : (
                messages.map((msg, i) => (
                  <Message key={i} role={msg.role} content={msg.content} />
                ))
              )}
              {loading && <Message role="assistant" content={<LoadingSpinner />} />}
              <div ref={messagesEndRef} />
            </div>
            
            <form onSubmit={sendMessage} className="message-form">
              <div className="input-container">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your message..."
                  disabled={loading}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage(e);
                    }
                  }}
                />
                <button 
                  type="submit" 
                  className="send-button"
                  disabled={loading || !input.trim()}
                  aria-label="Send message"
                >
                  <FiSend />
                </button>
              </div>
              <div className="chat-actions">
                <button 
                  type="button" 
                  className="secondary-button"
                  onClick={startSession}
                  disabled={loading}
                >
                  <FiRefreshCw /> New Chat
                </button>
              </div>
            </form>
          </>
        )}
      </main>
      
      <style jsx global>{`
        :root {
          --primary-color: #2563eb;
          --primary-hover: #1d4ed8;
          --bg-color: #f8fafc;
          --card-bg: #ffffff;
          --text-color: #1e293b;
          --text-muted: #64748b;
          --border-color: #e2e8f0;
          --user-message: #e0f2fe;
          --assistant-message: #f1f5f9;
          --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
          --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
          --radius-sm: 0.375rem;
          --radius-md: 0.5rem;
          --radius-lg: 1rem;
        }
        
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        
        body {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
          background-color: var(--bg-color);
          color: var(--text-color);
          line-height: 1.5;
        }
        
        .app-container {
          max-width: 48rem;
          margin: 0 auto;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }
        
        .app-header {
          text-align: center;
          padding: 1.5rem 1rem;
          border-bottom: 1px solid var(--border-color);
          background-color: var(--card-bg);
          box-shadow: var(--shadow-sm);
        }
        
        .app-header h1 {
          font-size: 1.875rem;
          font-weight: 700;
          margin-bottom: 0.25rem;
          color: var(--primary-color);
        }
        
        .app-header p {
          color: var(--text-muted);
          font-size: 0.875rem;
        }
        
        .chat-container {
          flex: 1;
          display: flex;
          flex-direction: column;
          padding: 1rem;
          max-width: 100%;
          margin: 0 auto;
          width: 100%;
          max-width: 56rem;
        }
        
        .welcome-screen {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          flex: 1;
          padding: 2rem 1rem;
        }
        
        .welcome-screen h2 {
          font-size: 1.5rem;
          margin-bottom: 0.5rem;
        }
        
        .welcome-screen p {
          color: var(--text-muted);
          margin-bottom: 2rem;
          max-width: 32rem;
        }
        
        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 1rem 0;
          margin-bottom: 1rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          flex: 1;
          color: var(--text-muted);
          padding: 2rem 1rem;
        }
        
        .empty-state svg {
          margin-bottom: 1rem;
          color: var(--border-color);
        }
        
        .empty-state h3 {
          margin-bottom: 0.5rem;
          color: var(--text-color);
        }
        
        .message {
          display: flex;
          gap: 0.75rem;
          max-width: 90%;
          align-self: flex-start;
        }
        
        .message.user {
          align-self: flex-end;
          flex-direction: row-reverse;
        }
        
        .message-avatar {
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
          background-color: var(--border-color);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          margin-top: 0.25rem;
        }
        
        .user .message-avatar {
          background-color: var(--primary-color);
          color: white;
        }
        
        .message-content {
          padding: 0.75rem 1rem;
          border-radius: var(--radius-lg);
          background-color: var(--assistant-message);
          box-shadow: var(--shadow-sm);
          max-width: 100%;
          word-wrap: break-word;
        }
        
        .user .message-content {
          background-color: var(--primary-color);
          color: white;
          border-bottom-right-radius: var(--radius-sm);
        }
        
        .assistant .message-content {
          border-bottom-left-radius: var(--radius-sm);
        }
        
        .message-form {
          width: 100%;
          margin-top: auto;
        }
        
        .input-container {
          position: relative;
          display: flex;
          align-items: center;
          background-color: var(--card-bg);
          border-radius: var(--radius-md);
          box-shadow: var(--shadow-md);
          border: 1px solid var(--border-color);
          transition: all 0.2s;
        }
        
        .input-container:focus-within {
          border-color: var(--primary-color);
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .input-container input {
          flex: 1;
          padding: 0.875rem 1rem;
          border: none;
          background: transparent;
          color: var(--text-color);
          font-size: 1rem;
          border-radius: var(--radius-md);
          outline: none;
          min-height: 3rem;
        }
        
        .input-container input::placeholder {
          color: var(--text-muted);
        }
        
        .send-button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 2.5rem;
          height: 2.5rem;
          margin: 0.25rem;
          border: none;
          border-radius: 50%;
          background-color: var(--primary-color);
          color: white;
          cursor: pointer;
          transition: background-color 0.2s;
        }
        
        .send-button:not(:disabled):hover {
          background-color: var(--primary-hover);
        }
        
        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .chat-actions {
          display: flex;
          justify-content: center;
          margin-top: 1rem;
        }
        
        .primary-button {
          background-color: var(--primary-color);
          color: white;
          border: none;
          border-radius: var(--radius-md);
          padding: 0.625rem 1.25rem;
          font-size: 0.9375rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.2s;
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .primary-button:hover:not(:disabled) {
          background-color: var(--primary-hover);
        }
        
        .primary-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        
        .secondary-button {
          background-color: transparent;
          color: var(--primary-color);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-md);
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .secondary-button:hover:not(:disabled) {
          background-color: rgba(0, 0, 0, 0.02);
          border-color: var(--primary-color);
        }
        
        .secondary-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        
        .loading-spinner {
          display: flex;
          justify-content: center;
          padding: 1rem 0;
        }
        
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        
        @media (max-width: 640px) {
          .app-header h1 {
            font-size: 1.5rem;
          }
          
          .message {
            max-width: 100%;
          }
          
          .message-content {
            padding: 0.625rem 0.875rem;
            font-size: 0.9375rem;
          }
          
          .input-container input {
            padding: 0.75rem 0.875rem;
            font-size: 0.9375rem;
          }
        }
      `}</style>
    </div>
  );
}
