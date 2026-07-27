// Persists chat conversations to localStorage so the "Show history" panel
// and "New chat" button have something real to work with. Each entry is
// keyed by the same session_id sent to the backend, so re-opening a past
// conversation also resumes real backend memory for it (see agent.py's
// session service), not just the on-screen transcript.

const STORAGE_KEY = "cloudpulse_chat_sessions";
const MAX_SESSIONS = 50;

function readAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function writeAll(sessions) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS)));
  } catch {
    // Storage full or unavailable (private browsing, etc.) — history just
    // won't persist across reloads; not worth surfacing as an error.
  }
}

export function listSessions() {
  return readAll().sort((a, b) => b.updatedAt - a.updatedAt);
}

export function getSession(sessionId) {
  return readAll().find((s) => s.sessionId === sessionId) || null;
}

function deriveTitle(messages) {
  const firstUserMsg = messages.find((m) => m.sender === "user");
  if (!firstUserMsg) return "New conversation";
  const text = firstUserMsg.text.trim();
  return text.length > 60 ? `${text.slice(0, 60)}…` : text;
}

// Saves/updates a conversation. Conversations with no messages are dropped
// (nothing worth remembering yet), so switching to a new chat and never
// sending anything doesn't clutter the history list.
export function saveSession(sessionId, messages) {
  const sessions = readAll();
  const idx = sessions.findIndex((s) => s.sessionId === sessionId);

  if (messages.length === 0) {
    if (idx !== -1) {
      sessions.splice(idx, 1);
      writeAll(sessions);
    }
    return;
  }

  const entry = {
    sessionId,
    title: deriveTitle(messages),
    updatedAt: Date.now(),
    messages,
  };

  if (idx !== -1) sessions[idx] = entry;
  else sessions.unshift(entry);

  writeAll(sessions);
}

export function deleteSession(sessionId) {
  writeAll(readAll().filter((s) => s.sessionId !== sessionId));
}
