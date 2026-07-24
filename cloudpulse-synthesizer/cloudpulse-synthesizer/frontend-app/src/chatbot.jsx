import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import api from "./api"; // Adjust path if api.js lives elsewhere
const QUICK_QUESTIONS = [
  "What recent changes affect my deployment?",
  "Are there upcoming deprecations?",
  "What troubleshooting steps should I try first?",
];

// Small talk (greetings, thanks, acknowledgements) never warrants offering
// a "more technical" / "simpler" follow-up — there's no substance to
// re-explain. Same for answers too short to have a technical/simple axis.
const SMALL_TALK_PATTERN =
  /^(hi|hello|hey+|yo|sup|thanks|thank you|thx|ty|bye|goodbye|see ya|ok|okay|k|cool|nice|great|got it|sounds good|awesome|perfect|np|no problem|you're welcome)[\s!.,]*$/i;

function shouldOfferFollowUpChips(query, answer) {
  if (SMALL_TALK_PATTERN.test(query.trim())) return false;
  if (!answer || answer.trim().length < 40) return false;
  return true;
}

// Staged labels for the "still working" indicator — timestamps are ms
// after the request starts. Keeps a long-running call from just sitting
// on a static "Thinking..." with no sense of progress.
const THINKING_STAGES = [
  { at: 0, label: "Thinking" },
  { at: 1800, label: "Gathering information" },
  { at: 4200, label: "Finalizing" },
];

// Single chatbot surface for the workspace: handles free-form Q&A through
// the general chat agent (/api/chat) AND, when a product is selected, a
// one-click structured one-pager (/api/generate-pdf) rendered as a bot
// message in the same thread — same conversation, two backends.
export default function Chatbot({ product }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isGeneratingOnePager, setIsGeneratingOnePager] = useState(false);
  const [lastOnePagerId, setLastOnePagerId] = useState(null);
  const [replyTo, setReplyTo] = useState(null);
  const [selectionMenu, setSelectionMenu] = useState(null);
  const [thinkingLabel, setThinkingLabel] = useState(THINKING_STAGES[0].label);
  const nextIdRef = useRef(0);
  const chatHistoryRef = useRef(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const thinkingTimeoutsRef = useRef([]);

  const clearThinkingSequence = () => {
    thinkingTimeoutsRef.current.forEach(clearTimeout);
    thinkingTimeoutsRef.current = [];
  };

  const startThinkingSequence = () => {
    clearThinkingSequence();
    setThinkingLabel(THINKING_STAGES[0].label);
    thinkingTimeoutsRef.current = THINKING_STAGES.slice(1).map((stage) =>
      setTimeout(() => setThinkingLabel(stage.label), stage.at)
    );
  };

  useEffect(() => clearThinkingSequence, []);

  const nextId = () => {
    nextIdRef.current += 1;
    return nextIdRef.current;
  };

  const pushMessage = (msg) => {
    const withId = { id: nextId(), ...msg };
    setMessages((prev) => [...prev, withId]);
    return withId.id;
  };

  // Keep the newest message (or the typing indicator) in view without
  // requiring a manual scroll.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isSending, isGeneratingOnePager]);

  // Dismiss the "Reply" popup on any click that isn't the popup itself.
  useEffect(() => {
    if (!selectionMenu) return undefined;
    const handleOutsideClick = (e) => {
      if (!e.target.closest?.(".selection-reply-btn")) {
        setSelectionMenu(null);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [selectionMenu]);

  const handleTextSelection = () => {
    const selection = window.getSelection();
    const snippet = selection && selection.toString().trim();
    if (!snippet || selection.isCollapsed) {
      setSelectionMenu(null);
      return;
    }

    const anchorEl =
      selection.anchorNode.nodeType === 3 ? selection.anchorNode.parentElement : selection.anchorNode;
    const bubbleEl = anchorEl?.closest?.(".chat-bubble");
    const containerEl = chatHistoryRef.current;
    if (!bubbleEl || !containerEl) {
      setSelectionMenu(null);
      return;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const containerRect = containerEl.getBoundingClientRect();

    setSelectionMenu({
      messageId: Number(bubbleEl.dataset.msgId),
      snippet,
      top: rect.top - containerRect.top + containerEl.scrollTop - 34,
      left: rect.left - containerRect.left + rect.width / 2,
    });
  };

  const handleReplyToSelection = () => {
    if (!selectionMenu) return;
    setReplyTo({ messageId: selectionMenu.messageId, snippet: selectionMenu.snippet });
    setSelectionMenu(null);
    window.getSelection()?.removeAllRanges();
    inputRef.current?.focus();
  };

  const handleSend = async (text) => {
    const query = text || input;
    if (!query.trim()) return;

    pushMessage({ sender: "user", text: query, replyTo });
    setInput("");
    setReplyTo(null);
    setIsSending(true);
    startThinkingSequence();

    try {
      const { data } = await api.post("/api/chat", {
        message: query,
      });

      pushMessage({
        sender: "bot",
        text: data.answer,
        sources: data.source_documents || [],
        showChips: shouldOfferFollowUpChips(query, data.answer),
      });
    } catch (error) {
      pushMessage({
        sender: "bot",
        text: "⚠️ Unable to reach the retrieval backend. Check that VITE_API_BASE_URL points to a running server.",
      });
    } finally {
      clearThinkingSequence();
      setIsSending(false);
    }
  };

  const handleGenerateOnePager = async () => {
    const targetProduct = (product || "").trim();
    if (!targetProduct) {
      pushMessage({
        sender: "bot",
        text: "Pick a product in the release ledger on the right first, then I can put together a one-pager for it.",
      });
      return;
    }

    pushMessage({ sender: "user", text: `Generate a one-pager for ${targetProduct}` });
    setIsGeneratingOnePager(true);
    startThinkingSequence();

    try {
      const { data } = await api.post("/api/generate-pdf", {
        product_name: targetProduct,
      });

      const id = pushMessage({
        sender: "bot",
        isOnePager: true,
        text: data.content_text,
      });
      setLastOnePagerId(id);
    } catch (error) {
      pushMessage({
        sender: "bot",
        text: `⚠️ Unable to generate a one-pager for ${targetProduct}. Check that VITE_API_BASE_URL points to a running server.`,
      });
    } finally {
      clearThinkingSequence();
      setIsGeneratingOnePager(false);
    }
  };

  const handleChipClick = (choice) => {
    setMessages((prev) => prev.map((m) => ({ ...m, showChips: false })));

    const botFollowUp = {
      sender: "bot",
      text:
        choice === "tech"
          ? "Mock Technical Data: Process relies on write-ahead logging (WAL) replication updates using schema engine 16.4."
          : "Mock Simple Data: You can now safely roll your storage database backwards without causing runtime downtime.",
    };
    pushMessage(botFollowUp);
  };

  return (
    <div className="workspace-chatbot">
      <h4>💬 CloudPulse Assistant</h4>
      <hr />

      <div className="chat-history" ref={chatHistoryRef} onMouseUp={handleTextSelection}>
        {messages.length === 0 && (
          <p className="subtitle">
            Ask a question, or generate a one-pager for the selected product.
          </p>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            data-msg-id={msg.id}
            className={`chat-bubble ${msg.sender} ${msg.isOnePager ? "onepager" : ""} ${
              msg.id === lastOnePagerId ? "one-pager-print" : ""
            }`}
          >
            {msg.replyTo && (
              <div className="reply-quote">
                <span className="reply-quote-bar" />
                <span className="reply-quote-text">{msg.replyTo.snippet}</span>
              </div>
            )}

            {msg.isOnePager ? (
              <>
                <div className="synthesis-output">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
                <div className="onepager-actions">
                  <button
                    type="button"
                    className="btn-icon"
                    onClick={() => window.print()}
                    aria-label="Export as PDF"
                    title="Export as PDF"
                  >
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 3v12" />
                      <path d="M7 10l5 5 5-5" />
                      <path d="M5 21h14" />
                    </svg>
                  </button>
                </div>
              </>
            ) : (
              <p>{msg.text}</p>
            )}

            {msg.showChips && (
              <div className="chat-chips">
                <button className="chip" onClick={() => handleChipClick("tech")}>
                  🔧 Technical details
                </button>
                <button className="chip" onClick={() => handleChipClick("simple")}>
                  💡 Simpler explanation
                </button>
              </div>
            )}
          </div>
        ))}

        {(isSending || isGeneratingOnePager) && (
          <div className="chat-bubble bot typing-indicator">
            <span className="typing-label">{thinkingLabel}…</span>
            <span className="typing-dots">
              <span />
              <span />
              <span />
            </span>
          </div>
        )}

        {selectionMenu && (
          <button
            type="button"
            className="selection-reply-btn"
            style={{ top: selectionMenu.top, left: selectionMenu.left }}
            onClick={handleReplyToSelection}
          >
            ↩ Reply
          </button>
        )}

        <div ref={bottomRef} />
      </div>

      <button
        type="button"
        className="btn btn-primary full-width one-pager-trigger"
        onClick={handleGenerateOnePager}
        disabled={isGeneratingOnePager}
      >
        {isGeneratingOnePager
          ? "Generating one-pager…"
          : `📄 Generate one-pager${product ? ` for ${product}` : ""}`}
      </button>

      <div className="quick-questions-row">
        {QUICK_QUESTIONS.map((q, i) => (
          <button
            key={i}
            className="btn btn-secondary quick-question"
            onClick={() => handleSend(q)}
            disabled={isSending}
          >
            💡 {q}
          </button>
        ))}
      </div>

      {replyTo && (
        <div className="reply-banner">
          <div className="reply-banner-text">
            <span className="reply-banner-label">Replying to</span>
            <span className="reply-banner-snippet">{replyTo.snippet}</span>
          </div>
          <button
            type="button"
            className="reply-banner-close"
            onClick={() => setReplyTo(null)}
            aria-label="Cancel reply"
          >
            ✕
          </button>
        </div>
      )}

      <div className="chat-input-wrapper">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask a Google Cloud question..."
          disabled={isSending}
        />
        <button className="btn btn-primary" onClick={() => handleSend()} disabled={isSending}>
          Send
        </button>
      </div>
    </div>
  );
}