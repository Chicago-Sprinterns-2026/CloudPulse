from google.adk.agents.llm_agent import Agent
 
from .tools import cloudpulse_tool
 
root_agent = Agent(
    model='gemini-3.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction=(
        "Answer user questions to the best of your knowledge. "
        "You have access to cloudpulse_tool, which supports four actions: "
        "'search_docs' for general how-to/conceptual questions (pass `query`), "
        "'metadata' for product status/ownership lookups (pass `product_name`), "
        "'release_notes' for what changed since a date (pass `product_name` and "
        "`start_date` in YYYY-MM-DD format), and 'msas' for required actions or "
        "deprecations (pass `product_name` and optionally `severity`). "
        "Always set the `action` argument explicitly."
    ),
    tools=[cloudpulse_tool],
)