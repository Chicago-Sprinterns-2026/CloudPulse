"""Main Streamlit entrypoint for CloudPulse."""

import streamlit as st

from src.frontend.components.catalog import render_catalog
from src.frontend.components.chatbot import render_chatbot
from src.frontend.components.settings import render_settings
from src.frontend.components.synthesizer import render_synthesizer


def main() -> None:
    st.set_page_config(
        page_title="CloudPulse Synthesizer",
        page_icon="☁️",
        layout="wide",
    )

    st.title("CloudPulse")
    st.caption("AI-powered Google Cloud product update synthesizer")

    page = st.sidebar.radio(
        "Navigate",
        ["Product Synthesizer", "Troubleshooting Chat", "Product Catalog", "Settings"],
    )

    if page == "Product Synthesizer":
        render_synthesizer()
    elif page == "Troubleshooting Chat":
        render_chatbot()
    elif page == "Product Catalog":
        render_catalog()
    else:
        render_settings()


if __name__ == "__main__":
    main()
