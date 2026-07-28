import asyncio
import json
import time
import uuid

from google.adk.agents.llm_agent import Agent
from google import genai
from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from .tools import cloudpulse_tool, _PROJECT_ID, _LOCATION
from .prompt_templates import (
    SYSTEM_PROMPT,
    ONE_PAGER_PROMPT,
    TROUBLESHOOTING_PROMPT,
    SUPPORT_ENGINEER_PROMPT,
    TAM_PROMPT,
    SALES_REP_PROMPT,
    ONBOARDING_INTERN_PROMPT,
    CUSTOMER_ENGINEER_PROMPT,
    DEVOPS_ENGINEER_PROMPT,
    CLOUD_ARCHITECT_PROMPT,
    STARTUP_CTO_PROMPT,
    COMPLIANCE_MANAGER_PROMPT,
)

# Persona-to-Prompt template map for dynamic selection
PERSONA_PROMPTS = {
    "support_engineer": SUPPORT_ENGINEER_PROMPT,
    "tam": TAM_PROMPT,
    "sales_rep": SALES_REP_PROMPT,
    "onboarding_intern": ONBOARDING_INTERN_PROMPT,
    "customer_engineer": CUSTOMER_ENGINEER_PROMPT,
    "devops_engineer": DEVOPS_ENGINEER_PROMPT,
    "cloud_architect": CLOUD_ARCHITECT_PROMPT,
    "startup_cto": STARTUP_CTO_PROMPT,
    "compliance_manager": COMPLIANCE_MANAGER_PROMPT,
}

SYSTEM_INSTRUCTION = f"""
{SYSTEM_PROMPT}

TOOL USAGE INSTRUCTIONS:
You have access to `cloudpulse_tool`, which supports four actions:
- 'search_docs' for general how-to/conceptual questions, troubleshooting, and technical documentation (pass `query`).
- 'metadata' for product status/ownership lookups (pass `product_name`).
- 'release_notes' for product release notes and recent updates (pass `product_name`). Do NOT ask the user for a start date; omit `start_date` to automatically retrieve the latest notes.
- 'msas' for required actions or deprecations (pass `product_name` and optionally `severity`).

Always set the `action` argument explicitly when calling `cloudpulse_tool`.

EMAIL DRAFTING INSTRUCTIONS:
If the user asks you to draft an email, write a concise, ready-to-send draft — not a long report. Include every piece of information the user actually asked for (dates, deadlines, links, specific changes) but nothing beyond that. Use a short subject line, a brief greeting, 3-6 sentences or a short bulleted list in the body, and a brief sign-off. Do not pad it with generic filler, restate the same point twice, or add sections the user didn't ask for.

PERSONA ADAPTATION & FORMATTING INSTRUCTIONS:
Identify the targeted persona or use-case requested by the user (e.g., Support Engineer, TAM, Cloud Sales Rep, Onboarding Intern, Customer Engineer, DevOps Engineer, Cloud Architect, Startup CTO, or Compliance Manager).
Format your response using the specific Google Advisory headers, callout boxes (`> ⚠️`), and structural layouts defined for that persona.
""".strip()

# 2. Define a clean fallback string for generic queries
DEFAULT_PERSONA = "support_engineer"

async def update_persona_context(callback_context):
    """
    Lightweight persona router.

    Strategy:
    - Look at recent conversation history for continuity.
    - Look at the latest user message for explicit persona need shifts.
    - Preserve the existing persona unless the new request clearly changes the audience.
    - Store persona state for future turns.
    """

    MAX_EVENTS = 8

    conversation = []

    # ---------------------------------------------------------
    # 1. Pull recent conversation history from ADK session
    # ---------------------------------------------------------
    if callback_context.session:
        for event in callback_context.session.events[-MAX_EVENTS:]:

            if not event.content:
                continue

            text = ""

            if hasattr(event.content, "parts"):
                text = "".join(
                    part.text
                    for part in event.content.parts
                    if getattr(part, "text", None)
                )

            if not text:
                continue

            speaker = (
                "user"
                if event.author == "user"
                else "assistant"
            )

            conversation.append(
                {
                    "speaker": speaker,
                    "text": text,
                }
            )


    # ---------------------------------------------------------
    # 2. Find latest user message
    # ---------------------------------------------------------
    latest_user_message = ""

    for message in reversed(conversation):
        if message["speaker"] == "user":
            latest_user_message = message["text"].lower()
            break


    # ---------------------------------------------------------
    # 3. Retrieve existing persona state
    # ---------------------------------------------------------
    current_persona = callback_context.state.get(
        "persona_key"
    )


    # ---------------------------------------------------------
    # 4. Determine if this is a persona shift
    # ---------------------------------------------------------

    selected_persona = current_persona or DEFAULT_PERSONA


    # ---- Executive / leadership context ----
    if any(keyword in latest_user_message for keyword in [
        "executive",
        "leadership",
        "vp",
        "cio",
        "business impact",
        "customer briefing",
        "presentation",
        "stakeholder",
    ]):
        selected_persona = "tam"


    # ---- Troubleshooting / incident response ----
    elif any(keyword in latest_user_message for keyword in [
        "error",
        "exception",
        "failed",
        "failure",
        "timeout",
        "stack trace",
        "logs",
        "crash",
        "503",
        "debug",
        "broken",
        "incident",
    ]):
        selected_persona = "support_engineer"


    # ---- Architecture / design ----
    elif any(keyword in latest_user_message for keyword in [
        "architecture",
        "architect",
        "design",
        "migration",
        "scaling",
        "best practice",
        "recommend an approach",
    ]):
        selected_persona = "cloud_architect"


    # ---- DevOps ----
    elif any(keyword in latest_user_message for keyword in [
        "pipeline",
        "ci/cd",
        "terraform",
        "deployment strategy",
        "automation",
        "infrastructure",
    ]):
        selected_persona = "devops_engineer"


    # ---- Learning / onboarding ----
    elif any(keyword in latest_user_message for keyword in [
        "what is",
        "explain",
        "teach me",
        "beginner",
        "tutorial",
        "how does",
    ]):
        selected_persona = "onboarding_intern"


    # ---- Sales / customer value ----
    elif any(keyword in latest_user_message for keyword in [
        "pricing",
        "cost",
        "competitive",
        "preview",
        "ga",
        "availability",
        "customer value",
    ]):
        selected_persona = "sales_rep"


    # ---------------------------------------------------------
    # 5. Update ADK session state
    # ---------------------------------------------------------

    callback_context.state["persona_key"] = selected_persona

    callback_context.state["persona"] = PERSONA_PROMPTS.get(
        selected_persona,
        PERSONA_PROMPTS["support_engineer"]
    )


    # Optional debugging context
    callback_context.state["recent_messages"] = conversation[-6:]

    callback_context.state["last_persona_update"] = {
        "previous": current_persona,
        "selected": selected_persona,
        "trigger_message": latest_user_message,
    }


root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for CloudPulse operational and technical questions.',
    instruction=SYSTEM_INSTRUCTION,
    tools=[cloudpulse_tool],
    before_agent_callback=update_persona_context,
    generate_content_config=types.GenerateContentConfig(
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(initial_delay=1, attempts=5),
        ),
    ),
)

_APP_NAME = "cloudpulse"
_USER_ID = "cloudpulse-user"

_session_service = InMemorySessionService()
_runner = Runner(
    app_name=_APP_NAME,
    agent=root_agent,
    session_service=_session_service,
)


async def run_agent(message: str, session_id: str | None = None):
    session_id = session_id or str(uuid.uuid4())

    session = await _session_service.get_session(
        app_name=_APP_NAME, user_id=_USER_ID, session_id=session_id
    )
    if session is None:
        await _session_service.create_session(
            app_name=_APP_NAME, user_id=_USER_ID, session_id=session_id
        )

    content = types.Content(role="user", parts=[types.Part(text=message)])

    answer = ""
    async for event in _runner.run_async(
        user_id=_USER_ID, session_id=session_id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            answer = "".join(part.text or "" for part in event.content.parts)

    return {
        "answer": answer,
        "source_documents": [],
        "session_id": session_id
    }


# One-pagers always need exactly the same three lookups (metadata,
# release_notes, msas) — there's no need to spend a Gemini round-trip
# having an agent "decide" to call them. Fetching them directly in
# parallel and doing a single synthesis call cuts out that whole extra
# round-trip (previously: one call to choose tools, then the tool calls,
# then a final call to write the text — now: tool calls, then one call).
ONE_PAGER_INSTRUCTION = (
    "You are given pre-fetched data for one or more Google Cloud products, "
    "each from three sources: product metadata, recent release notes, and "
    "mandatory service announcements (MSAs). Write a one-pager from that "
    "data alone — do not invent facts not present in it.\n\n"
    "First, silently identify which scenario this request is:\n"
    "- SINGLE: one product, no particular angle requested.\n"
    "- MULTI: several products, no explicit comparison implied — treat "
    "them as a related set (e.g. grouped by theme or by product).\n"
    "- COMPARISON: several products where the request implies choosing "
    "between them or contrasting them (e.g. \"compare X and Y\", \"X vs Y\").\n"
    "- FOCUSED: a specific focus/topic was given (this can combine with "
    "any of the above — e.g. a focused comparison).\n"
    "Then write the one-pager for that scenario using the exact same six "
    "sections and headers below every time — the scenario changes what "
    "you say in each section, never the structure itself.\n\n"
    "Also silently identify the requested LENGTH tier from the user's "
    "message (default STANDARD if nothing is said):\n"
    "- SHORT: user asked for \"short\", \"brief\", \"quick\", or similar.\n"
    "- STANDARD: no length preference stated.\n"
    "- LONG: user asked for \"long\", \"detailed\", \"comprehensive\", "
    "\"extended\", or similar.\n\n"
    "The word counts and bullet caps below are for STANDARD, which must "
    "fit exactly one printed page — treat them as hard caps, not "
    "suggestions. For SHORT, use roughly HALF each word count and HALF "
    "each bullet cap (minimum 2 bullets wherever a cap is listed) — it "
    "should read as a compressed brief, not a trimmed one-pager, and "
    "should comfortably fit on well under one page. For LONG, target "
    "roughly 1100-1300 words total (aim to fill close to two full "
    "printed pages, not just spill a little past one) — use roughly "
    "2.5x each STANDARD bullet cap and expand each section with more "
    "supporting detail/context rather than only adding more bullets. "
    "The one-printed-page constraint does NOT apply for LONG. Use this "
    "exact structure, in this exact order, with these exact Markdown "
    "exact Markdown headers regardless of length tier. All bullet caps "
    "below are TOTAL for the whole section — e.g. in a 3-product MULTI "
    "one-pager, 5 bullets total across all products, not 5 each:\n\n"
    "## Executive Summary\n"
    "60-80 words. One paragraph, no bullets.\n"
    "SINGLE: what the product is and its current state.\n"
    "MULTI: one sentence framing what ties the products together, then "
    "their combined current state.\n"
    "COMPARISON: name the products and the dimension being compared.\n"
    "FOCUSED: state the focus topic up front, before anything else.\n\n"
    "## What Changed / Active Alerts\n"
    "150-180 words, MAXIMUM 5 bullets total. When selecting which updates "
    "to include and in what order, apply this priority ranking (highest "
    "priority first) rather than your own subjective sense of impact:\n"
    "1. Active MSAs, or any update with a future compliance/action deadline.\n"
    "2. Security bulletins and CVEs.\n"
    "3. Deprecations and breaking changes.\n"
    "4. Non-breaking IAM/permission changes and other non-breaking changes.\n"
    "5. Generally Available (GA) feature announcements.\n"
    "6. Preview feature announcements.\n"
    "Fill the 5 bullet slots by working down this list in order until full. "
    "If more than 5 items are relevant, keep only the 5 highest-priority "
    "ones and drop the rest — never add a 6th bullet to fit more in, and "
    "never include a lower-priority item while a higher-priority item is "
    "available and was excluded.\n"
    "SINGLE: the product's most important recent release notes/MSAs.\n"
    "MULTI: group bullets by product (bold the product name per bullet) "
    "or by shared theme, whichever reads more naturally.\n"
    "COMPARISON: phrase bullets as direct deltas between the products "
    "(e.g. \"Product A now supports X; Product B does not\"), not two "
    "separate flat lists.\n"
    "FOCUSED: only include items matching the focus; if a product has "
    "nothing relevant to the focus, say so in one short bullet rather "
    "than including unrelated items to fill space.\n\n"
    "## Why It Matters\n"
    "60-80 words. One paragraph.\n"
    "SINGLE/MULTI: the business/technical impact of the above changes.\n"
    "COMPARISON: why the difference between the products matters when "
    "choosing between them.\n"
    "FOCUSED: impact specifically within the focus area, not the "
    "products' full scope.\n\n"
    "## Impacted Users/Workloads\n"
    "50-70 words, MAXIMUM 4 bullets total (or one short paragraph).\n"
    "SINGLE/MULTI: who/what is affected, combined into one list rather "
    "than repeated per product.\n"
    "COMPARISON: which user profile or workload fits which product, if "
    "that's the natural angle.\n\n"
    "## Recommended Actions & Deadlines\n"
    "100-120 words, MAXIMUM 4 bullets total, one action per bullet, with "
    "a deadline date when one exists in the source data. If more than 4 "
    "actions are relevant across everything, keep only the 4 most "
    "urgent/impactful — prioritize across products/focus, not per product.\n\n"
    "## Sources & Citations\n"
    "30-50 words, MAXIMUM 4 bullets total, covering whichever products "
    "contributed. Bulleted list formatted strictly as Markdown hyperlinks "
    "using the exact syntax `* [Link Text](URL)` on a single line (for "
    "example, `* [Cloud Interconnect Overview](https://cloud.google.com/"
    "network-connectivity/docs/interconnect/concepts/overview)`). NEVER "
    "place line breaks, colons, or extra text between the title and the "
    "URL. NEVER write plain URLs on their own line, and NEVER display "
    "gs:// paths.\n\n"
    "Bullet caps are hard limits on COUNT, independent of the word "
    "budget — a section with terse bullets must still stop at its cap "
    "rather than adding more short bullets to fill the word budget.\n\n"
    "Never add, remove, rename, or reorder sections. Never add extra "
    "commentary outside these six sections, and never mention the "
    "scenario label itself in the output. If a section has nothing "
    "relevant to report, keep the header and write one line stating "
    "that plainly rather than omitting or padding it.\n\n"

    "GROUNDING AND ACCURACY REQUIREMENTS:\n"
    "- Use only information contained in the supplied metadata, release-note, "
    "and MSA results.\n"
    "- The supplied release notes may include multiple records for the same "
    "product published on the same date, describing different, unrelated "
    "release branches, versions, or components (e.g. separate minor-version "
    "tracks each with their own fix/announcement). Do NOT assume records with "
    "the same product and date are duplicates or conflicting — read each "
    "record's own content (version numbers, CVE IDs, described behavior) to "
    "judge whether it actually conflicts with another record.\n"
    "- Two records genuinely conflict only when they make an opposite factual "
    "claim about the same specific thing (e.g. one says a permission is now "
    "required and another says that same permission is no longer required). "
    "When you identify a genuine conflict like this, use the more recently "
    "dated record and do not surface the superseded claim.\n"
    "- When more than five valid updates remain, apply the same priority "
    "ranking given under 'What Changed / Active Alerts' (MSAs/deadlines, "
    "then security bulletins, then deprecations/breaking changes, then "
    "non-breaking changes, then GA features, then preview features) "
    "rather than your own judgment of which are newest or most notable.\n"
    "- Do not select an older update unless it is an active MSA, has a future "
    "deadline, or is necessary to explain a current breaking change.\n"
    "- Do not repeat the same information across sections.\n"
    "- Do not change update selection or ordering merely to make the report more "
    "varied, balanced, or interesting.\n"
    "- Every statement in Why It Matters, Impacted Users/Workloads, and "
    "Recommended Actions & Deadlines must correspond directly to an item selected "
    "in What Changed / Active Alerts.\n"
    "- Do not mention users, workloads, actions, vulnerabilities, announcements, "
    "or sources unrelated to the selected updates.\n"
    "- Do not assign a severity such as critical, high, or urgent unless the "
    "source explicitly states that severity.\n"
    "- Do not invent deadlines, business impacts, remediation steps, recommended "
    "actions, or migration requirements.\n"
    "- Recommend an action only when that action is explicitly supported by the "
    "supplied data. Otherwise, direct the user to review the relevant source.\n"
    "- Preserve exact dates, product names, commands, permissions, release stages, "
    "and status labels such as Preview, General Availability, deprecated, retired, "
    "breaking change, or non-breaking change.\n"
    "- Preserve the exact relationship between each vulnerability title, CVE "
    "identifier, affected platform, security bulletin, and date.\n"
    "- Do not combine separate vulnerabilities or announcements into one bullet "
    "unless the supplied source explicitly groups them.\n"
    "- Never output more than 5 update bullets, 4 impacted-user bullets, "
    "4 recommended-action bullets, or 4 source bullets.\n"
)

_one_pager_client = genai.Client(vertexai=True, project=_PROJECT_ID, location=_LOCATION)


# ---------------------------------------------------------------------------
# One-pager input trimming.
#
# This only caps how much release-note text gets sent to Gemini per
# product (newest N records, sorted by publish_date) — it does not try to
# judge which records "conflict," since same-day/same-product records can
# legitimately describe different things (parallel version branches,
# separate CVEs, etc.). Keeping the prompt smaller helps latency and
# reduces how much old/contradictory history the model has to reconcile.
# MSAs are never trimmed, since they represent required actions regardless
# of age. This does not touch citations/sources handling at all.
# ---------------------------------------------------------------------------

MAX_RELEASE_NOTES_PER_PRODUCT = 25

# Mirrors the priority ranking given to Gemini in ONE_PAGER_INSTRUCTION.
# Lower number = higher priority = should appear earlier in the prompt.
# Models tend to weight earlier content more heavily, so positioning
# high-priority records first in the prompt reinforces (rather than just
# hoping the model follows) the ranking rule stated in the instructions.
# Unrecognized/missing release_note_type values fall back to the lowest
# priority rather than being silently dropped.
_RELEASE_NOTE_TYPE_PRIORITY = {
    "MSA": 0,
    "SECURITY_BULLETIN": 1,
    "DEPRECATION": 2,
    "BREAKING_CHANGE": 2,
    "NON_BREAKING_CHANGE": 3,
    "FIX": 3,
    "SERVICE_ANNOUNCEMENT": 4,
    "FEATURE": 4,
}
_DEFAULT_PRIORITY = 5


def _priority_rank(record) -> int:
    if not isinstance(record, dict):
        return _DEFAULT_PRIORITY
    note_type = str(record.get("release_note_type") or "").upper()
    return _RELEASE_NOTE_TYPE_PRIORITY.get(note_type, _DEFAULT_PRIORITY)


def _parse_date(value) -> str:
    """Returns a sortable string; unparsable/missing dates sort last."""
    if not value:
        return ""
    return str(value)


def _select_recent_release_notes(release_notes_result, max_records: int = MAX_RELEASE_NOTES_PER_PRODUCT):
    """
    Trims a release-notes tool result down to the most recent N records,
    then re-orders that trimmed set by priority (highest-priority record
    types first, newest-dated first within the same priority).

    Handles the common shapes a tool result might come back as: a bare list,
    or a dict with the list under a key like "release_notes"/"items"/"results".
    If the shape isn't recognized, the data is returned unchanged rather than
    risking silently dropping something we don't understand.
    """
    if isinstance(release_notes_result, list):
        records = release_notes_result

        # Step 1: keep only the most recent N records, regardless of type,
        # so we don't lose genuinely recent news by over-favoring priority.
        most_recent = sorted(
            records,
            key=lambda r: _parse_date(r.get("publish_date") if isinstance(r, dict) else None),
            reverse=True,
        )[:max_records]

        # Step 2: within that recent set, order by priority so the highest-
        # priority items are positioned first in what Gemini reads. Python's
        # sort is stable, so sorting the already-date-descending list by
        # priority alone preserves newest-first ordering within each tier.
        prioritized = sorted(most_recent, key=_priority_rank)
        return prioritized

    if isinstance(release_notes_result, dict):
        for key in ("release_notes", "items", "results", "records"):
            if key in release_notes_result and isinstance(release_notes_result[key], list):
                trimmed = release_notes_result.copy()
                trimmed[key] = _select_recent_release_notes(release_notes_result[key], max_records)
                return trimmed

    # Unrecognized shape — leave untouched rather than guessing.
    return release_notes_result


async def _gather_product_data(product_name: str) -> dict:
    t_retrieval_start = time.perf_counter()
    metadata_result, release_notes_result, msas_result = await asyncio.gather(
        asyncio.to_thread(cloudpulse_tool, action="metadata", product_name=product_name),
        asyncio.to_thread(cloudpulse_tool, action="release_notes", product_name=product_name),
        asyncio.to_thread(cloudpulse_tool, action="msas", product_name=product_name),
    )
    t_retrieval_end = time.perf_counter()
    print(f"[{product_name}] retrieval took {t_retrieval_end - t_retrieval_start:.2f}s")

    one_pager_release_notes = _select_recent_release_notes(release_notes_result)
    t_filter_end = time.perf_counter()
    print(
        f"[{product_name}] trimming took {t_filter_end - t_retrieval_end:.3f}s "
        f"({len(release_notes_result) if isinstance(release_notes_result, list) else '?'} -> "
        f"{len(one_pager_release_notes) if isinstance(one_pager_release_notes, list) else '?'} records)"
    )
    if isinstance(one_pager_release_notes, list):
        type_order = [r.get("release_note_type") if isinstance(r, dict) else "?" for r in one_pager_release_notes]
        print(f"[{product_name}] priority order sent to Gemini: {type_order}")

    return {
        "product": product_name,
        "metadata": metadata_result,
        "release_notes": one_pager_release_notes,
        "msas": msas_result,
    }


async def _record_one_pager_in_session(session_id: str, products: list[str], focus: str | None, content_text: str) -> None:
    """Writes the one-pager request/result into the same ADK session used by
    /api/chat, as a normal user+model turn. Without this, a one-pager
    generated via /api/generate-pdf (which talks to Gemini directly, not
    through the Runner) is invisible to later chat turns — a follow-up like
    "summarize that" would have no idea what "that" refers to."""
    session = await _session_service.get_session(
        app_name=_APP_NAME, user_id=_USER_ID, session_id=session_id
    )
    if session is None:
        session = await _session_service.create_session(
            app_name=_APP_NAME, user_id=_USER_ID, session_id=session_id
        )

    label = " + ".join(products)
    focus_note = f" (focus: {focus})" if focus else ""
    user_text = f"Generate a one-pager for {label}{focus_note}."

    await _session_service.append_event(
        session=session,
        event=Event(author="user", content=types.Content(role="user", parts=[types.Part(text=user_text)])),
    )
    await _session_service.append_event(
        session=session,
        event=Event(
            author=root_agent.name,
            content=types.Content(role="model", parts=[types.Part(text=content_text)]),
        ),
    )


async def generate_one_pager(products: list[str], focus: str | None = None, session_id: str | None = None) -> str:
    t_start = time.perf_counter()

    # Fetching every product's three tool calls together (rather than
    # product-by-product) keeps this at the wall-clock cost of the single
    # slowest call overall, not the sum across products.
    per_product_data = await asyncio.gather(
        *(_gather_product_data(product_name) for product_name in products)
    )
    t_data_ready = time.perf_counter()
    print(f"All product data ready in {t_data_ready - t_start:.2f}s")

    data_sections = "\n\n".join(
        f"Product: {entry['product']}\n"
        f"metadata tool result:\n{json.dumps(entry['metadata'], default=str)}\n\n"
        f"release_notes tool result:\n{json.dumps(entry['release_notes'], default=str)}\n\n"
        f"msas tool result:\n{json.dumps(entry['msas'], default=str)}"
        for entry in per_product_data
    )

    focus_block = f"\nUser-requested focus: {focus}\n" if focus else ""

    prompt = f"{ONE_PAGER_INSTRUCTION}\n{focus_block}\n{data_sections}"
    print(f"Prompt size: {len(prompt)} chars (~{len(prompt) // 4} tokens est.)")

    t_gen_start = time.perf_counter()
    response = _one_pager_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            top_p=0.7,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(initial_delay=1, attempts=5),
            ),
        ),
    )
    t_gen_end = time.perf_counter()
    print(f"Gemini generation took {t_gen_end - t_gen_start:.2f}s")

    if response.candidates:
        finish_reason = response.candidates[0].finish_reason
        if finish_reason is not None and str(finish_reason) != "STOP":
            print(
                f"WARNING: one-pager generation finished with reason "
                f"{finish_reason} (not STOP) — output may be truncated or filtered."
            )

    content_text = response.text or ""

    if session_id:
        try:
            await _record_one_pager_in_session(session_id, products, focus, content_text)
        except Exception as error:
            # Don't fail the one-pager response just because the follow-up
            # context couldn't be recorded — worst case, later chat turns
            # fall back to asking which product, same as before this fix.
            print(f"Failed to record one-pager in session {session_id}: {error}")

    print(f"Total generate_one_pager time: {time.perf_counter() - t_start:.2f}s")

    return content_text

