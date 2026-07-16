"""User settings and technology stack selection."""
#feel free to delete if not necessary @backend ppl
import streamlit as st


def render_settings() -> None:
    st.header("My Tech Stack")

    services = st.multiselect(
        "Select the Google Cloud products in your environment",
        [
            "BigQuery",
            "Cloud Run",
            "Cloud SQL",
            "Compute Engine",
            "Google Kubernetes Engine",
            "Vertex AI",
        ],
    )

    st.session_state["selected_services"] = services
    st.success("Your selections are saved for this session.")
