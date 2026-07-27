import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import api from "./api"; // Adjust path if api.js lives elsewhere
import { extractProductsFromText } from "./utils";
import { saveSession, getSession } from "./chatHistoryStorage";
import ChatHistoryPanel from "./chatHistoryPanel";

// crypto.randomUUID() is only exposed in secure contexts (HTTPS, or the
// page origin literally being "localhost") — accessed over plain HTTP via
// any other host/IP (e.g. a LAN or WSL address), it's undefined and throws,
// crashing the whole component. Fall back to a manual v4 UUID in that case.
function generateSessionId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Pool the two non-one-pager prompt buttons draw from — kept larger than 2
// so the row shows different suggestions across sessions instead of the
// same fixed pair every time.
const QUICK_QUESTION_POOL = [
  "What recent changes affect my deployment?",
  "Are there upcoming deprecations?",
  "What troubleshooting steps should I try first?",
  "What's new in the last 30 days?",
  "Are there any active security advisories?",
  "What should I know before my next upgrade?",
];

function pickRandomPrompts(pool, count) {
  const shuffled = [...pool].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
}

const ONE_PAGER_INTENT_PATTERN = /\bone[-\s]?pagers?\b/i;
// Only email-draft responses get the in-bubble edit button — every other
// bot answer is a Q&A response you'd re-ask rather than hand-edit.
const EMAIL_DRAFT_INTENT_PATTERN = /\bdraft\s+(?:an?|the)\s+email\b/i;
const CONTEXT_MESSAGE_WINDOW = 6;
const SMALL_TALK_PATTERN =
  /^(hi|hello|hey+|yo|sup|thanks|thank you|thx|ty|bye|goodbye|see ya|ok|okay|k|cool|nice|great|got it|sounds good|awesome|perfect|np|no problem|you're welcome)[\s!.,]*$/i;

function shouldOfferFollowUpChips(query, answer) {
  if (SMALL_TALK_PATTERN.test(query.trim())) return false;
  if (!answer || answer.trim().length < 40) return false;
  return true;
}

const THINKING_STAGES = [
  { at: 0, label: "Thinking" },
  { at: 1800, label: "Gathering information" },
  { at: 4200, label: "Finalizing" },
];

/**
 * Extracts markdown-style links [Title](URL) directly from message text
 */
function extractLinksFromMarkdown(text) {
  if (!text) return [];
  const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
  const matches = [];
  let match;
  while ((match = linkRegex.exec(text)) !== null) {
    matches.push({ title: match[1], url: match[2] });
  }
  return matches;
}

/**
 * Calculates Confidence Score based on context:
 * - Refusals / Missing Info / Clarification Requests -> Hide badge (returns null)
 * - Greetings / Casual conversation -> Hide badge (returns null)
 * - Official Web Docs + Hyperlinks -> Very High (95%)
 * - Internal Release Notes / MSAs / Backend Sources -> Very High (95%)
 * - Community Forums -> High (90%)
 * - General Google Cloud Context -> Medium (75%)
 * - No Grounding / Fallback -> Low (<50%)
 */
function evaluateConfidence(messageText, sources = []) {
  if (!messageText || messageText.startsWith("⚠️")) {
    return null;
  }

  const textLower = messageText.toLowerCase().trim();

  // 1. HIDE TAB FOR GREETINGS & CASUAL INTROS
  const isGreeting =
    /^(hello|hi|hey|greetings|welcome|howdy)[\s!.,]*$/i.test(textLower) ||
    textLower.includes("how can i help") ||
    textLower.includes("how can i assist") ||
    textLower.startsWith("hello!") ||
    textLower.startsWith("hi!") ||
    (textLower.includes("cloudpulse") && (textLower.includes("help") || textLower.includes("assist")));

  if (isGreeting) {
    return null;
  }

  // 2. HIDE TAB IF THE BOT LACKS INFORMATION, REFUSES, OR ASKS FOR CLARIFICATION
  const isMissingInfoOrClarification =
    textLower.includes("cannot find sufficient") ||
    textLower.includes("don't have enough information") ||
    textLower.includes("dont have enough information") ||
    textLower.includes("unable to find") ||
    textLower.includes("no information available") ||
    textLower.includes("cannot answer") ||
    textLower.includes("insufficient information") ||
    textLower.includes("not enough information") ||
    textLower.includes("couldn't find") ||
    textLower.includes("could not find") ||
    textLower.includes("no data found") ||
    textLower.includes("don't have access") ||
    textLower.includes("dont have access") ||
    textLower.includes("i do not have access") ||
    textLower.includes("i don't have information") ||
    textLower.includes("no specific information") ||
    textLower.includes("please specify") ||
    textLower.includes("broad platform") ||
    textLower.includes("specify a particular");

  if (isMissingInfoOrClarification) {
    return null;
  }

  const hasSources = Array.isArray(sources) && sources.length > 0;
  const sourceUrls = hasSources
    ? sources.map((s) => (typeof s === "string" ? s : s.source_url || s.url || s.title || ""))
    : [];

  const textContainsLink = messageText.includes("http://") || messageText.includes("https://");
  const hasLinks = sourceUrls.some((url) => url.startsWith("http")) || textContainsLink;

  // Detect internal release notes / MSAs / backend sources
  const isInternalDoc =
    hasSources ||
    /release\s*notes?|deprecation|msa|feature\s*updates?|manifest/i.test(messageText);

  const isOfficialDocs =
    sourceUrls.some((url) => url.includes("cloud.google.com")) ||
    messageText.includes("cloud.google.com");

  if ((isOfficialDocs && hasLinks) || isInternalDoc) {
    return {
      level: "🟢 Very High",
      score: "95%",
      rationale: isInternalDoc && !hasLinks
        ? "Grounded directly in verified internal release notes and GCP platform documentation."
        : "Grounded in official Google Cloud documentation with direct hyperlink verification.",
    };
  }

  const isCommunityForum = sourceUrls.some(
    (url) =>
      url.includes("stackoverflow.com") ||
      url.includes("reddit.com") ||
      url.includes("googlecloudcommunity.com") ||
      url.includes("forum")
  );

  if (isCommunityForum && hasLinks) {
    return {
      level: "🟢 High",
      score: "90%",
      rationale: "Includes real-world context verified by external community forum page links.",
    };
  }

  if (isOfficialDocs) {
    return {
      level: "🟡 Medium",
      score: "75%",
      rationale: "Based on official Google Cloud platform context without direct source links.",
    };
  }

  return {
    level: "🔴 Low",
    score: "<50%",
    rationale: "Lacks direct document grounding or verified links. Output generated from general platform context.",
  };
}

function ConfidenceTab({ messageText, sources = [] }) {
  const [isOpen, setIsOpen] = useState(false);

  const confidence = evaluateConfidence(messageText, sources);

  // Hide tab if confidence is null (e.g. greetings, errors, refusals, or lack of information)
  if (!confidence) {
    return null;
  }

  // Check backend sources array, fallback to extracting markdown links from messageText
  const extractedLinks = extractLinksFromMarkdown(messageText);
  const displaySources =
    sources && sources.length > 0
      ? sources.map((s) => ({
          title: typeof s === "string" ? s : s.title || s.source_url || s.url || "Reference Document",
          url: typeof s === "string" ? s : s.source_url || s.url,
        }))
      : extractedLinks;

  return (
    <div className="confidence-tab-wrapper" style={{ marginTop: "8px", fontSize: "0.85rem" }}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: "#f8f9fa",
          border: "1px solid #e0e0e0",
          borderRadius: "6px",
          padding: "6px 12px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          color: "#333",
          fontWeight: "500",
        }}
      >
        <span>
          🛡️ Response Confidence: <strong>{confidence.level} ({confidence.score})</strong>
        </span>
        <span style={{ fontSize: "0.75rem", color: "#666" }}>
          {isOpen ? "▲ Hide Details" : "▼ View Verification"}
        </span>
      </button>

      {isOpen && (
        <div
          style={{
            background: "#ffffff",
            border: "1px solid #e0e0e0",
            borderTop: "none",
            borderRadius: "0 0 6px 6px",
            padding: "10px 12px",
            lineHeight: "1.4",
            color: "#444",
          }}
        >
          <p style={{ margin: "0 0 6px 0", fontSize: "0.8rem" }}>
            <strong>Assessment Rationale:</strong> {confidence.rationale}
          </p>

          {displaySources && displaySources.length > 0 ? (
            <div>
              <strong style={{ fontSize: "0.8rem" }}>Verified Sources:</strong>
              <ul style={{ margin: "4px 0 0 0", paddingLeft: "18px" }}>
                {displaySources.map((src, idx) => (
                  <li key={idx}>
                    {src.url ? (
                      <a href={src.url} target="_blank" rel="noreferrer" style={{ color: "#1a73e8" }}>
                        {src.title}
                      </a>
                    ) : (
                      <span>{src.title}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p style={{ margin: 0, fontSize: "0.75rem", color: "#888" }}>
              Grounded in internal release ledger document.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default function Chatbot({ product, manifest = [] }) {
  // One id per conversation so the backend's ADK session can accumulate
  // real multi-turn memory, and so New Chat / History can tell
  // conversations apart from each other.
  const [sessionId, setSessionId] = useState(() => generateSessionId());
  const [historyOpen, setHistoryOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isGeneratingOnePager, setIsGeneratingOnePager] = useState(false);
  const [replyTo, setReplyTo] = useState(null);
  const [selectionMenu, setSelectionMenu] = useState(null);
  const [thinkingLabel, setThinkingLabel] = useState(THINKING_STAGES[0].label);
  const [randomPrompts, setRandomPrompts] = useState(() => pickRandomPrompts(QUICK_QUESTION_POOL, 2));
  const [attachedFile, setAttachedFile] = useState(null);
  const nextIdRef = useRef(0);
  const chatHistoryRef = useRef(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const thinkingTimeoutsRef = useRef([]);
  const abortControllerRef = useRef(null);

  // Persist this conversation (keyed by sessionId) any time it changes, so
  // "Show history" and page refreshes have something real to show.
  useEffect(() => {
    saveSession(sessionId, messages);
  }, [sessionId, messages]);

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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isSending, isGeneratingOnePager]);

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

  const ALLOWED_EXTENSIONS = [".txt", ".md", ".csv", ".json", ".log", ".pdf", ".docx"];
  const MAX_FILE_CHARS = 8000;

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    const lower = file.name.toLowerCase();
    const hasAllowedExtension = ALLOWED_EXTENSIONS.some((ext) => lower.endsWith(ext));
    if (!hasAllowedExtension) {
      pushMessage({
        sender: "bot",
        text: `⚠️ Unsupported file type. Please attach one of: ${ALLOWED_EXTENSIONS.join(", ")}.`,
      });
      return;
    }

    if (lower.endsWith(".pdf") || lower.endsWith(".docx")) {
      const formData = new FormData();
      formData.append("file", file);
      try {
        const { data } = await api.post("/api/extract-text", formData);
        setAttachedFile({ name: file.name, content: data.content });
      } catch (error) {
        pushMessage({ sender: "bot", text: `⚠️ Couldn't extract text from ${file.name}.` });
      }
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const content = String(reader.result || "").slice(0, MAX_FILE_CHARS);
      setAttachedFile({ name: file.name, content });
    };
    reader.onerror = () => {
      pushMessage({ sender: "bot", text: "⚠️ Couldn't read that file. Please try again." });
    };
    reader.readAsText(file);
  };

  const handleRemoveAttachment = () => setAttachedFile(null);

  const handleNewChat = () => {
    clearThinkingSequence();
    setSessionId(generateSessionId());
    setMessages([]);
    setInput("");
    setIsSending(false);
    setIsGeneratingOnePager(false);
    setReplyTo(null);
    setSelectionMenu(null);
    setThinkingLabel(THINKING_STAGES[0].label);
    setRandomPrompts(pickRandomPrompts(QUICK_QUESTION_POOL, 2));
    setAttachedFile(null);
    nextIdRef.current = 0;
    inputRef.current?.focus();
  };

  const handleSelectHistorySession = (id) => {
    const session = getSession(id);
    if (session) {
      clearThinkingSequence();
      setSessionId(id);
      setMessages(session.messages);
      setInput("");
      setReplyTo(null);
      setSelectionMenu(null);
      nextIdRef.current = session.messages.reduce((max, m) => Math.max(max, m.id || 0), 0);
    }
    setHistoryOpen(false);
  };

  const handleSend = async (text) => {
    const query = text || input;
    if (!query.trim() && !attachedFile) return;

    const fullQuery = attachedFile
      ? `[Attached file: ${attachedFile.name}]\n\`\`\`\n${attachedFile.content}\n\`\`\`\n\n${query}`
      : query;

    const hadAttachment = Boolean(attachedFile);


    pushMessage({ sender: "user", text: query, replyTo, attachmentName: attachedFile?.name });
    setInput("");
    setReplyTo(null);
    setAttachedFile(null);

    if (ONE_PAGER_INTENT_PATTERN.test(query)) {
      await handleOnePagerRequest(query);
      return;
    }

    setIsSending(true);
    startThinkingSequence();

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const { data } = await api.post(
        "/api/chat",
        { message: fullQuery, session_id: sessionId },
        { signal: controller.signal }
      );

      pushMessage({
        sender: "bot",
        text: data.answer,
        sources: data.source_documents || [],
        showChips: shouldOfferFollowUpChips(query, data.answer),
        fromAttachment: hadAttachment,
        isEmailDraft: EMAIL_DRAFT_INTENT_PATTERN.test(query),
      });

    } catch (error) {
      if (error.code !== "ERR_CANCELED") {
        pushMessage({
          sender: "bot",
          text: "⚠️ Unable to reach the retrieval backend. Check that VITE_API_BASE_URL points to a running server.",
        });
      }
    } finally {
      clearThinkingSequence();
      setIsSending(false);
      abortControllerRef.current = null;
    }
  };

  const runOnePagerGeneration = async (products, focus) => {
    const label = products.join(" + ");
    setIsGeneratingOnePager(true);
    startThinkingSequence();

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const { data } = await api.post(
        "/api/generate-pdf",
        { products, focus: focus || null, session_id: sessionId },
        { signal: controller.signal }
      );

      pushMessage({
        sender: "bot",
        isOnePager: true,
        text: data.content_text,
        pdfUrl: data.pdf_url ? `${api.defaults.baseURL || ""}${data.pdf_url}` : null,
      });
    } catch (error) {
      if (error.code !== "ERR_CANCELED") {
        pushMessage({
          sender: "bot",
          text: `⚠️ Unable to generate a one-pager for ${label}. Check that VITE_API_BASE_URL points to a running server.`,
        });
      }
    } finally {
      clearThinkingSequence();
      setIsGeneratingOnePager(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopGenerating = () => {
    abortControllerRef.current?.abort();
  };

  const handleGenerateOnePager = () => {
    setInput("Generate one-pager");
    inputRef.current?.focus();
  };

  const handleDraftEmail = () => {
    setInput("Draft an email about ");
    inputRef.current?.focus();
  };

  const [copiedMessageId, setCopiedMessageId] = useState(null);

  const handleCopyMessage = (id, text) => {
    navigator.clipboard?.writeText(text);
    setCopiedMessageId(id);
    setTimeout(() => setCopiedMessageId((current) => (current === id ? null : current)), 1500);
  };

  // In-place editing of a bot response (e.g. tweaking an email draft's
  // wording) — edits the bubble itself rather than routing through the
  // main input box.
  const [editingMessageId, setEditingMessageId] = useState(null);
  const [editDraft, setEditDraft] = useState("");

  const handleStartEdit = (msg) => {
    setEditingMessageId(msg.id);
    setEditDraft(msg.text);
  };

  const handleCancelEdit = () => {
    setEditingMessageId(null);
    setEditDraft("");
  };

  const handleSaveEdit = (id) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, text: editDraft } : m)));
    setEditingMessageId(null);
    setEditDraft("");
  };

  const buildConversationContext = () =>
    messages
      .slice(-CONTEXT_MESSAGE_WINDOW)
      .filter((m) => !m.isOnePager)
      .map((m) => `${m.sender === "user" ? "User" : "Assistant"}: ${m.text}`)
      .join("\n");

  const handleOnePagerRequest = async (requestText) => {
    const contextText = [buildConversationContext(), requestText].filter(Boolean).join("\n");
    const manifestProducts = manifest.map((m) => m.product);
    const matchedProducts = extractProductsFromText(contextText, manifestProducts);
    const targetProducts = matchedProducts.length
      ? matchedProducts
      : [(product || "").trim()].filter(Boolean);

    if (targetProducts.length === 0) {
      pushMessage({
        sender: "bot",
        text: "I couldn't tell which product you mean — pick one in the release ledger on the right, or name it in your message, then try again.",
      });
      return;
    }

    await runOnePagerGeneration(targetProducts, requestText);
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
    <div className="workspace-chatbot-wrapper">
      {historyOpen && (
        <ChatHistoryPanel
          activeSessionId={sessionId}
          onSelect={handleSelectHistorySession}
          onClose={() => setHistoryOpen(false)}
        />
      )}
      <div className="workspace-chatbot">
        <div className="chatbot-header-row">
        <div className="chatbot-header-actions">
          <button
            type="button"
            className="header-action-btn"
            onClick={() => setHistoryOpen(true)}
            aria-label="Show conversation history"
            title="Show conversation history"
          >
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 7v5l3 3" />
            </svg>
          </button>
          <button
            type="button"
            className="header-action-btn header-action-btn-primary"
            onClick={handleNewChat}
            disabled={isSending || isGeneratingOnePager}
            aria-label="Start a new conversation"
            title="Start a new conversation"
          >
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>
      </div>
      <hr />

      <div className="chat-history" ref={chatHistoryRef} onMouseUp={handleTextSelection}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            data-msg-id={msg.id}
            className={`chat-bubble ${msg.sender} ${msg.isOnePager ? "onepager" : ""} ${
              msg.id === editingMessageId ? "editing" : ""
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
                  {msg.pdfUrl && (
                    <a
                      href={msg.pdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-icon"
                      aria-label="Download PDF"
                      title="Download PDF"
                    >
                      <svg
                        viewBox="0 0 24 24"
                        width="16"
                        height="16"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M12 3v12" />
                        <path d="M7 10l5 5 5-5" />
                        <path d="M5 21h14" />
                      </svg>
                    </a>
                  )}
                </div>
              </>
            ) : (
              <div className={msg.sender === "bot" ? "chat-markdown" : undefined}>
                {msg.id === editingMessageId ? (
                  <>
                    <textarea
                      className="message-edit-textarea"
                      value={editDraft}
                      onChange={(e) => setEditDraft(e.target.value)}
                      rows={Math.max(4, editDraft.split("\n").length)}
                      autoFocus
                    />
                    <div className="message-actions">
                      <button
                        type="button"
                        className="btn btn-primary quick-question"
                        onClick={() => handleSaveEdit(msg.id)}
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary quick-question"
                        onClick={handleCancelEdit}
                      >
                        Cancel
                      </button>
                    </div>
                  </>
                ) : msg.sender === "bot" ? (
                  <>
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                    {!msg.fromAttachment && (
                      <ConfidenceTab messageText={msg.text} sources={msg.sources} />
                    )}
                    <div className="message-actions">
                      <button
                        type="button"
                        className="btn-icon"
                        onClick={() => handleCopyMessage(msg.id, msg.text)}
                        aria-label="Copy text"
                        title={copiedMessageId === msg.id ? "Copied!" : "Copy text"}
                      >
                        {copiedMessageId === msg.id ? "✓" : "📋"}
                      </button>
                      {msg.isEmailDraft && (
                        <button
                          type="button"
                          className="btn-icon"
                          onClick={() => handleStartEdit(msg)}
                          aria-label="Edit email draft"
                          title="Edit email draft"
                        >
                          ✏️
                        </button>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <p>{msg.text}</p>
                    <div className="message-actions">
                      <button
                        type="button"
                        className="btn-icon"
                        onClick={() => handleStartEdit(msg)}
                        aria-label="Edit message"
                        title="Edit message"
                      >
                        ✏️
                      </button>
                    </div>
                  </>
                )}
              </div>
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

      <div className="quick-questions-row">
        <button
          type="button"
          className="btn btn-secondary quick-question"
          onClick={handleGenerateOnePager}
          disabled={isGeneratingOnePager}
        >
          📄 Generate one-pager
        </button>
        <button
          type="button"
          className="btn btn-secondary quick-question"
          onClick={handleDraftEmail}
        >
          ✉️ Draft an email
        </button>
        {randomPrompts.map((q, i) => (
          <button
            key={i}
            className="btn btn-secondary quick-question"
            onClick={() => {
              setInput(q);
              inputRef.current?.focus();
            }}
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

      {attachedFile && (
        <div className="attachment-chip">
          <span>📎 {attachedFile.name}</span>
          <button type="button" onClick={handleRemoveAttachment} aria-label="Remove attachment">
            ✕
          </button>
        </div>
      )}

      <div className="chat-input-wrapper">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          style={{ display: "none" }}
          accept=".txt,.md,.csv,.json,.log,.pdf,.docx"
        />
        <button
          type="button"
          className="btn btn-secondary attach-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={isSending}
          title="Attach a file"
        >
          📎
        </button>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask a Google Cloud question..."
          disabled={isSending}
        />
        {isSending || isGeneratingOnePager ? (
          <button type="button" className="btn btn-secondary stop-generating-btn" onClick={handleStopGenerating}>
            ⏹ Stop
          </button>
        ) : (
          <button className="btn btn-primary" onClick={() => handleSend()}>
            Send
          </button>
        )}
      </div>

      </div>
    </div>
  );
}
