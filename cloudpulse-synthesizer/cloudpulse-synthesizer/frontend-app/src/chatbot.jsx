import React, { useState } from 'react';
import axios from 'axios';

const QUICK_QUESTIONS = [
  "What recent changes affect my deployment?",
  "Are there upcoming deprecations?",
  "What troubleshooting steps should I try first?"
];

export default function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const handleSend = async (text) => {
    const query = text || input;
    if (!query.trim()) return;

    const userMsg = { sender: 'user', text: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    try {
      const { data } = await axios.post('http://localhost:8000/api/chat', {
        message: query
      });

      const botMsg = {
        sender: 'bot',
        text: data.answer,
        sources: data.source_documents || [],
        showChips: true
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: "⚠️ Unable to reach the retrieval backend. Ensure the API server is running on localhost:8000." }
      ]);
    }
  };

  const handleChipClick = (choice) => {
    setMessages((prev) => prev.map((m) => ({ ...m, showChips: false })));

    const botFollowUp = {
      sender: 'bot',
      text: choice === 'tech'
        ? "Mock Technical Data: Process relies on write-ahead logging (WAL) replication updates using schema engine 16.4."
        : "Mock Simple Data: You can now safely roll your storage database backwards without causing runtime downtime."
    };
    setMessages((prev) => [...prev, botFollowUp]);
  };

  return (
    <div className="workspace-chatbot">
      <h4>💬 Troubleshooting Assistant</h4>
      <hr />

      <div className="chat-history">
        {messages.length === 0 && <p className="subtitle">Select a quick prompt or type below to begin.</p>}
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-bubble ${msg.sender}`}>
            <p>{msg.text}</p>
            {msg.showChips && (
              <div className="chat-chips">
                <button className="chip" onClick={() => handleChipClick('tech')}>🔧 Technical details</button>
                <button className="chip" onClick={() => handleChipClick('simple')}>💡 Simpler explanation</button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="quick-questions-row">
        {QUICK_QUESTIONS.map((q, i) => (
          <button key={i} className="btn btn-secondary quick-question" onClick={() => handleSend(q)}>
            💡 {q}
          </button>
        ))}
      </div>

      <div className="chat-input-wrapper">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a Google Cloud question..."
        />
        <button className="btn btn-primary" onClick={() => handleSend()}>Send</button>
      </div>
    </div>
  );
}