import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

from google.adk.agents.llm_agent import Agent
from google import genai
from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
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
- 'release_notes' for what changed since a date (pass `product_name` and `start_date` in YYYY-MM-DD format).
- 'msas' for required actions or deprecations (pass `product_name` and optionally `severity`).

Always set the `action` argument explicitly when calling `cloudpulse_tool`.

PERSONA ADAPTATION & FORMATTING INSTRUCTIONS:
Identify the targeted persona or use-case requested by the user (e.g., Support Engineer, TAM, Cloud Sales Rep, Onboarding Intern, Customer Engineer, DevOps Engineer, Cloud Architect, Startup CTO, or Compliance Manager).
Format your response using the specific Google Advisory headers, callout boxes (`> ⚠️`), and structural layouts defined for that persona.
""".strip()

# 2. Define a clean fallback string for generic queries
DEFAULT_PERSONA = "A general technical assistant focused on operational clarity and strict grounding."

async def determine_and_set_persona(callback_context):
    """
    Analyzes the latest user request to dynamically match it to a predefined
    CloudPulse sub-persona before the system prompt compiles.
    """
    # 3. Extract the last message sent by the user from session history
    user_message = ""
    if callback_context.session and callback_context.session.events:
        for event in reversed(callback_context.session.events):
            if event.author == "user":
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts") and event.content.parts:
                        user_message = "".join([
                            part.text for part in event.content.parts if hasattr(part, "text") and part.text
                        ])
                    elif hasattr(event.content, "text") and event.content.text:
                        user_message = event.content.text
                break

    # If it's a completely new session with no text yet, apply the default string
    if not user_message:
        if "persona" not in callback_context.state:
            callback_context.state["persona"] = DEFAULT_PERSONA
        return

    # 4. Prompt the classifier to output exactly one key from your map
    allowed_keys = list(PERSONA_PROMPTS.keys())
    classifier_prompt = f"""
    You are an internal routing system for CloudPulse. Analyze the user's question and categorize it into the single best audience persona key.
    
    Allowed Keys:
    - 'support_engineer': Deep technical debugging, handling tickets, or tracking down system/code exceptions.
    - 'tam': Multi-service cloud architecture setups, high-level client impact briefings, or roadmap queries.
    - 'sales_rep': Feature capabilities, preview/GA status updates, or customer value-propositions for client calls.
    - 'onboarding_intern': Conceptual questions, foundational GCP architecture explainers, and educational engineering mentoring.
    
    User Question: "{user_message}"
    
    Respond with ONLY the exact matching key name from this list: {allowed_keys}. 
    If the question doesn't cleanly fit any category or is a basic greeting, return 'support_engineer' as the safest technical fallback. Do not add any extra text or punctuation.
    """

    try:
        # 5. Execute the classification via a fast flash model with 0.0 temperature
        with genai.Client() as ai_client:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=classifier_prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
        
        selected_key = response.text.strip().lower()
        
        # 6. Retrieve the matching full prompt block. 
        # If the model hallucinates a key, fallback to support_engineer or default
        chosen_persona_prompt = PERSONA_PROMPTS.get(selected_key, PERSONA_PROMPTS["support_engineer"])
        
        # 7. Inject the text block straight into the state variable expected by your SYSTEM_PROMPT
        context.session.state["persona"] = chosen_persona_prompt
        
    except Exception as e:
        # Fallback guardrail to keep the system operational if the API call fails
        if "persona" not in callback_context.state:
            callback_context.state["persona"] = PERSONA_PROMPTS["support_engineer"]

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for CloudPulse operational and technical questions.',
    instruction=SYSTEM_INSTRUCTION,
    tools=[cloudpulse_tool],
    before_agent_callback=determine_and_set_persona,
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

    return {"answer": answer, "source_documents": []}


# One-pagers always need exactly the same three lookups (metadata,
# release_notes, msas) — there's no need to spend a Gemini round-trip
# having an agent "decide" to call them. Fetching them directly in
# parallel and doing a single synthesis call cuts out that whole extra
# round-trip (previously: one call to choose tools, then the tool calls,
# then a final call to write the text — now: tool calls, then one call).
ONE_PAGER_INSTRUCTION = (
    "You are given pre-fetched data for a Google Cloud product from three "
    "sources: product metadata, recent release notes, and mandatory service "
    "announcements (MSAs). Write a one-pager from that data alone — do not "
    "invent facts not present in it.\n\n"
    "The output must fit exactly one printed page — use this exact "
    "structure, in this exact order, with these exact Markdown headers, "
    "and stay within the word budget per section (target ~500-600 words "
    "total; treat these as hard caps, not suggestions):\n\n"
    "## Executive Summary\n"
    "60-80 words. One paragraph, no bullets. What the product is and its "
    "current state.\n\n"
    "## What Changed / Active Alerts\n"
    "150-180 words. Bulleted. The most important recent release notes "
    "and any active MSAs, most impactful first.\n\n"
    "## Why It Matters\n"
    "60-80 words. One paragraph. The business/technical impact of the "
    "above changes.\n\n"
    "## Impacted Users/Workloads\n"
    "50-70 words. Bulleted or one short paragraph. Who/what is affected.\n\n"
    "## Recommended Actions & Deadlines\n"
    "100-120 words. Bulleted, one action per bullet, with a deadline "
    "date when one exists in the source data.\n\n"
    "## Sources & Citations\n"
    "30-50 words. Short bulleted list of the specific tool calls/source "
    "URLs used.\n\n"
    "Never add, remove, rename, or reorder sections. Never add extra "
    "commentary outside these six sections. If a section has nothing "
    "relevant to report, keep the header and write one line stating "
    "that plainly rather than omitting or padding it."
)

_one_pager_client = genai.Client(vertexai=True, project=_PROJECT_ID, location=_LOCATION)


async def generate_one_pager(product_name: str) -> str:
    start_date = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")

    metadata_result, release_notes_result, msas_result = await asyncio.gather(
        asyncio.to_thread(cloudpulse_tool, action="metadata", product_name=product_name),
        asyncio.to_thread(
            cloudpulse_tool, action="release_notes", product_name=product_name, start_date=start_date
        ),
        asyncio.to_thread(cloudpulse_tool, action="msas", product_name=product_name),
    )

    prompt = (
        f"{ONE_PAGER_INSTRUCTION}\n\n"
        f"Product: {product_name}\n\n"
        f"metadata tool result:\n{json.dumps(metadata_result, default=str)}\n\n"
        f"release_notes tool result:\n{json.dumps(release_notes_result, default=str)}\n\n"
        f"msas tool result:\n{json.dumps(msas_result, default=str)}"
    )

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

    return response.text or ""
