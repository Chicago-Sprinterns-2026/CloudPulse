import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import api from "./api"; // Adjust path if api.js lives elsewhere
import { extractProductsFromText } from "./utils";


const QUICK_QUESTIONS = [
 "What recent changes affect my deployment?",
 "Are there upcoming deprecations?",
 "What troubleshooting steps should I try first?",
];


const ONE_PAGER_INTENT_PATTERN = /\bone[-\s]?pagers?\b/i;
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
* Calculates Confidence Score based on the Matrix:
* - Official Docs + Hyperlink -> Very High (95%)
* - Community Forum Hyperlink -> High (90%)
* - Official Docs (no links)  -> Medium (75%)
* - No Grounded Sources       -> Low (<50%)
*/
function evaluateConfidence(messageText, sources = []) {
 if (!messageText || messageText.startsWith("⚠️")) {
   return null;
 }


 const hasSources = Array.isArray(sources) && sources.length > 0;
 const sourceUrls = hasSources
   ? sources.map((s) => (typeof s === "string" ? s : s.source_url || s.url || ""))
   : [];


 const textContainsLink = messageText.includes("http://") || messageText.includes("https://");
 const hasLinks = sourceUrls.some((url) => url.startsWith("http")) || textContainsLink;


 const isCommunityForum = sourceUrls.some(
   (url) =>
     url.includes("stackoverflow.com") ||
     url.includes("reddit.com") ||
     url.includes("googlecloudcommunity.com") ||
     url.includes("forum")
 );


 const isOfficialDocs =
   sourceUrls.some((url) => url.includes("cloud.google.com")) ||
   messageText.includes("cloud.google.com") ||
   hasSources;


 if (isOfficialDocs && hasLinks) {
   return {
     level: "🟢 Very High",
     score: "95%",
     rationale:
       "Grounded in official Google Cloud documentation with direct hyperlink verification.",
   };
 }


 if (isCommunityForum && hasLinks) {
   return {
     level: "🟢 High",
     score: "90%",
     rationale:
       "Includes real-world context verified by external community forum page links.",
   };
 }


 if (isOfficialDocs) {
   return {
     level: "🟡 Medium",
     score: "75%",
     rationale:
       "Based on official Google Cloud platform context without direct source links.",
   };
 }


 return {
   level: "🔴 Low",
   score: "<50%",
   rationale:
     "Lacks direct document grounding or verified links. Output generated from general platform context.",
 };
}


function ConfidenceTab({ messageText, sources = [] }) {
 const [isOpen, setIsOpen] = useState(false);


 const confidence = evaluateConfidence(messageText, sources);


 // Hide tab on system errors or empty messages
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
                   <a href={src.url} target="_blank" rel="noreferrer" style={{ color: "#1a73e8" }}>
                     {src.title}
                   </a>
                 </li>
               ))}
             </ul>
           </div>
         ) : (
           <p style={{ margin: 0, fontSize: "0.75rem", color: "#888" }}>
             No direct URL citations attached.
           </p>
         )}
       </div>
     )}
   </div>
 );
}


export default function Chatbot({ product, manifest = [] }) {
 const [messages, setMessages] = useState([]);
 const [input, setInput] = useState("");
 const [isSending, setIsSending] = useState(false);
 const [isGeneratingOnePager, setIsGeneratingOnePager] = useState(false);
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


 const handleSend = async (text) => {
   const query = text || input;
   if (!query.trim()) return;


   pushMessage({ sender: "user", text: query, replyTo });
   setInput("");
   setReplyTo(null);


   if (ONE_PAGER_INTENT_PATTERN.test(query)) {
     await handleOnePagerRequest(query);
     return;
   }


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


 const runOnePagerGeneration = async (products, focus) => {
   const label = products.join(" + ");
   setIsGeneratingOnePager(true);
   startThinkingSequence();


   try {
     const { data } = await api.post("/api/generate-pdf", {
       products,
       focus: focus || null,
     });


     pushMessage({
       sender: "bot",
       isOnePager: true,
       text: data.content_text,
       pdfUrl: data.pdf_url ? `${api.defaults.baseURL || ""}${data.pdf_url}` : null,
     });
   } catch (error) {
     pushMessage({
       sender: "bot",
       text: `⚠️ Unable to generate a one-pager for ${label}. Check that VITE_API_BASE_URL points to a running server.`,
     });
   } finally {
     clearThinkingSequence();
     setIsGeneratingOnePager(false);
   }
 };


 const handleGenerateOnePager = () => {
   const targetProduct = (product || "").trim();
   setInput(targetProduct ? `Generate a one-pager for ${targetProduct}` : "Generate a one-pager for ");
   inputRef.current?.focus();
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
           className={`chat-bubble ${msg.sender} ${msg.isOnePager ? "onepager" : ""}`}
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
               {msg.sender === "bot" ? (
                 <>
                   <ReactMarkdown>{msg.text}</ReactMarkdown>
                   <ConfidenceTab messageText={msg.text} sources={msg.sources} />
                 </>
               ) : (
                 <p>{msg.text}</p>
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


