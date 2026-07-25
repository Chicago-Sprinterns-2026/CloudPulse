import asyncio
import json
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
    "data alone — do not invent facts not present in it. If more than one "
    "product's data is given, synthesize a single combined one-pager that "
    "covers them together (compare/contrast or group related updates as "
    "appropriate) rather than writing separate reports back to back.\n\n"
    "If a user-requested focus is given below, prioritize and filter the "
    "content in every section around that focus — omit or de-emphasize "
    "material outside it — while still keeping all six sections.\n\n"
    "The output must fit exactly one printed page — use this exact "
    "structure, in this exact order, with these exact Markdown headers, "
    "and stay within the word budget per section (target ~500-600 words "
    "total; treat these as hard caps, not suggestions):\n\n"
    "## Executive Summary\n"
    "60-80 words. One paragraph, no bullets. What the product is and its "
    "current state.\n\n"
    "## What Changed / Active Alerts\n"
    "150-180 words, MAXIMUM 5 bullets. The most important recent release "
    "notes and any active MSAs, most impactful first. If more than 5 items "
    "are relevant, keep only the 5 most impactful and drop the rest — "
    "never add a 6th bullet to fit more in.\n\n"
    "## Why It Matters\n"
    "60-80 words. One paragraph. The business/technical impact of the "
    "above changes.\n\n"
    "## Impacted Users/Workloads\n"
    "50-70 words, MAXIMUM 4 bullets (or one short paragraph). Who/what is "
    "affected.\n\n"
    "## Recommended Actions & Deadlines\n"
    "100-120 words, MAXIMUM 4 bullets, one action per bullet, with a "
    "deadline date when one exists in the source data. If more than 4 "
    "actions are relevant, keep only the 4 most urgent/impactful.\n\n"
    "## Sources & Citations\n"
    "30-50 words, MAXIMUM 4 bullets. Short bulleted list of the specific "
    "tool calls/source URLs used.\n\n"
    "These are hard caps on bullet COUNT, independent of the word budget — "
    "a section with terse bullets must still stop at its bullet cap rather "
    "than adding more short bullets to fill the word budget.\n\n"
    "Never add, remove, rename, or reorder sections. Never add extra "
    "commentary outside these six sections. If a section has nothing "
    "relevant to report, keep the header and write one line stating "
    "that plainly rather than omitting or padding it."
)

_one_pager_client = genai.Client(vertexai=True, project=_PROJECT_ID, location=_LOCATION)


async def _gather_product_data(product_name: str) -> dict:
    metadata_result, release_notes_result, msas_result = await asyncio.gather(
        asyncio.to_thread(cloudpulse_tool, action="metadata", product_name=product_name),
        asyncio.to_thread(cloudpulse_tool, action="release_notes", product_name=product_name),
        asyncio.to_thread(cloudpulse_tool, action="msas", product_name=product_name),
    )
    return {
        "product": product_name,
        "metadata": metadata_result,
        "release_notes": release_notes_result,
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
    # Fetching every product's three tool calls together (rather than
    # product-by-product) keeps this at the wall-clock cost of the single
    # slowest call overall, not the sum across products.
    per_product_data = await asyncio.gather(
        *(_gather_product_data(product_name) for product_name in products)
    )

    data_sections = "\n\n".join(
        f"Product: {entry['product']}\n"
        f"metadata tool result:\n{json.dumps(entry['metadata'], default=str)}\n\n"
        f"release_notes tool result:\n{json.dumps(entry['release_notes'], default=str)}\n\n"
        f"msas tool result:\n{json.dumps(entry['msas'], default=str)}"
        for entry in per_product_data
    )

    focus_block = f"\nUser-requested focus: {focus}\n" if focus else ""

    prompt = f"{ONE_PAGER_INSTRUCTION}\n{focus_block}\n{data_sections}"

    response = _one_pager_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(initial_delay=1, attempts=5),
            ),
        ),
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

    return content_text
