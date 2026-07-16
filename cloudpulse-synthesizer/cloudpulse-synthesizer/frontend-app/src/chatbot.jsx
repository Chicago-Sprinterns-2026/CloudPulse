import React, { useState } from 'react';

const QUICK_QUESTIONS = [
  "What recent changes affect my deployment?",
  "Are there upcoming deprecations?",
  "What troubleshooting steps should I try first?"
];

export default function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const handleSend = (textToSend) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const userMessage = { sender: 'user', text: query };
    const botResponse = { 
      sender: 'bot', 
      text: `This is a simulated answer for: "${query}". Would you like a technical overview or a simplified walkthrough?`,
      showChips: true 
    };

    setMessages((prev) => [...prev, userMessage, botResponse]);
    setInput('');
  };

  const handleChipClick = (choice) => {
    // Remove chip selections from past bubbles to clean the layout
    setMessages((prev) => prev.map(m => ({ ...m, showChips: false })));
    
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
        {messages.length === 0 && <p className="subtitle">Select a quick prompt or type below to begin mock agent execution.</p>}
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

      <div className="quick-questions-row" style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
        {QUICK_QUESTIONS.map((q, i) => (
          <button key={i} className="btn btn-secondary" style={{ fontSize: '0.8rem' }} onClick={() => handleSend(q)}>
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
