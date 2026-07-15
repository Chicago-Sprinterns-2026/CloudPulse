"""One-pager generator UI."""

import streamlit as st

from src.backend.agent import CloudPulseAgent
from src.frontend.utils.exporter import build_text_export


def render_synthesizer() -> None:
    st.header("Product One-Pager Synthesizer")

    product_name = st.text_input(
        "Google Cloud product",
        placeholder="Example: Cloud Run",
    )
    persona = st.selectbox(
        "Audience persona",
        ["Cloud Architect", "Cloud Sales Representative", "TAM", "Developer"],
    )
    priority = st.selectbox(
        "Priority",
        ["Critical", "High", "Medium", "Low"],
    )

    if st.button("Generate one-pager", type="primary"):
        if not product_name.strip():
            st.warning("Enter a Google Cloud product.")
            return

        agent = CloudPulseAgent()
        response = agent.build_one_pager_prompt(
            product_name=product_name,
            persona=persona,
            priority=priority,
        )
        result = agent.generate(response.content)

        st.subheader(f"{product_name} Update")
        st.write(result)

        export_bytes = build_text_export(result)
        st.download_button(
            "Download TXT",
            data=export_bytes,
            file_name=f"{product_name.lower().replace(' ', '-')}-one-pager.txt",
            mime="text/plain",
        )
