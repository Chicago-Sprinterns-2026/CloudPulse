import React, { useEffect, useState } from "react";
import { listSessions, deleteSession } from "./chatHistoryStorage";

function formatTimestamp(ms) {
  const date = new Date(ms);
  const now = new Date();
  const sameDay = date.toDateString() === now.toDateString();
  return sameDay
    ? date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
    : date.toLocaleDateString([], { month: "short", day: "numeric" });
}

export default function ChatHistoryPanel({ activeSessionId, onSelect, onClose }) {
  const [sessions, setSessions] = useState(() => listSessions());

  // Re-read on mount in case a session was saved just before opening.
  useEffect(() => {
    setSessions(listSessions());
  }, []);

  const handleDelete = (e, sessionId) => {
    e.stopPropagation();
    deleteSession(sessionId);
    setSessions(listSessions());
  };

  return (
    <div className="chat-history-panel">
      <div className="chat-history-panel-header">
        <h4>Chat history</h4>
        <button
          type="button"
          className="btn-icon"
          aria-label="Close history"
          onClick={onClose}
        >
          ✕
        </button>
      </div>

      <div className="chat-history-panel-list">
        {sessions.length === 0 && (
          <p className="subtitle" style={{ padding: "0 4px" }}>
            No past conversations yet.
          </p>
        )}

        {sessions.map((s) => (
          <div
            key={s.sessionId}
            className={`chat-history-item ${s.sessionId === activeSessionId ? "active" : ""}`}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(s.sessionId)}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect(s.sessionId)}
          >
            <div className="chat-history-item-main">
              <p className="chat-history-item-title">{s.title}</p>
              <p className="note">{formatTimestamp(s.updatedAt)}</p>
            </div>
            <button
              type="button"
              className="btn-icon chat-history-item-delete"
              aria-label={`Delete "${s.title}"`}
              onClick={(e) => handleDelete(e, s.sessionId)}
            >
              🗑
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
