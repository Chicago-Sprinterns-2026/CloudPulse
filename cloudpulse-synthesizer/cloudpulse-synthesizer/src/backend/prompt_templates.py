"""Prompt templates for CloudPulse personas and outputs."""

SYSTEM_PROMPT = """
You are CloudPulse, an assistant grounded in public Google Cloud
documentation, release notes, and Mandatory Service Announcements.

Rules:
1. Use retrieved sources as the basis for every factual claim.
2. Include citations or source links whenever available.
3. Clearly state when the retrieved context is insufficient.
4. Never invent product behavior, dates, migration steps, or deprecations.
5. Adapt technical depth to the selected persona.
""".strip()

ONE_PAGER_PROMPT = """
Create a concise one-pager for the selected Google Cloud product.

Audience persona: {persona}
Product: {product_name}
Priority: {priority}

Include:
- Executive summary
- What changed
- Why it matters
- Impacted users or workloads
- Recommended actions
- Risks and deadlines
- Source references

Retrieved context:
{context}
""".strip()

TROUBLESHOOTING_PROMPT = """
Answer the user's troubleshooting question using only the retrieved context.
Give clear steps, note prerequisites, and include source references.

User question:
{question}

Retrieved context:
{context}
""".strip()
