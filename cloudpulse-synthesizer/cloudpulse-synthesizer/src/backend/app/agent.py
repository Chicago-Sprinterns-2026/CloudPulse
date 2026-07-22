import uuid

from google.adk.agents.llm_agent import Agent
from google import genai
from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from .tools import cloudpulse_tool
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


# Dedicated agent for one-pager generation (pdf.py), skipping root_agent's
# before_agent_callback. That callback spends a full extra Gemini round-trip
# classifying a chat persona, but SYSTEM_PROMPT/ONE_PAGER_PROMPT reference
# persona via unresolved {{persona}} placeholders (not ADK's {persona} state
# templating), and the callback itself sets `context.session.state[...]`
# (undefined `context`) instead of `callback_context...` — so the classified
# persona never actually reaches the instruction either way. One-pagers don't
# need per-message audience adaptation, so this path just skips it outright.
one_pager_agent = Agent(
    model='gemini-2.5-flash',
    name='one_pager_agent',
    description='Generates CloudPulse product one-pagers.',
    instruction=(
        "Write a one-pager for the requested Google Cloud product using "
        "`cloudpulse_tool`, which supports: 'metadata' (product_name), "
        "'release_notes' (product_name, start_date), and 'msas' (product_name). "
        "Always set the `action` argument explicitly. Structure the response as: "
        "1. Executive Summary, 2. What Changed / Active Alerts, "
        "3. Recommended Actions & Deadlines, 4. Sources & Citations."
    ),
    tools=[cloudpulse_tool],
    generate_content_config=types.GenerateContentConfig(
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(initial_delay=1, attempts=5),
        ),
    ),
)

_one_pager_runner = Runner(
    app_name=_APP_NAME,
    agent=one_pager_agent,
    session_service=_session_service,
)


async def run_one_pager_agent(message: str, session_id: str | None = None):
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
    async for event in _one_pager_runner.run_async(
        user_id=_USER_ID, session_id=session_id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            answer = "".join(part.text or "" for part in event.content.parts)

    return {"answer": answer, "source_documents": []}
