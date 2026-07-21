from google.adk.agents.llm_agent import Agent
from google.genai import types

from .tools import cloudpulse_tool
from .prompt_template import (
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

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for CloudPulse operational and technical questions.',
    instruction=SYSTEM_INSTRUCTION,
    tools=[cloudpulse_tool],
    generate_content_config=types.GenerateContentConfig(
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(initial_delay=1, attempts=5),
        ),
    ),
)