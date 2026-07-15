"""Troubleshooting chatbot UI."""

import streamlit as st

from src.backend.agent import CloudPulseAgent


QUICK_QUESTIONS = [
    "What recent changes affect my deployment?",
    "Are there upcoming deprecations?",
    "What troubleshooting steps should I try first?",
]


def render_chatbot() -> None:
    st.header("Troubleshooting Assistant")
    st.write("Ask questions grounded in Google Cloud documentation.")

    st.subheader("Quick questions")
    columns = st.columns(len(QUICK_QUESTIONS))
    selected_question = None

    for column, question in zip(columns, QUICK_QUESTIONS):
        if column.button(question, use_container_width=True):
            selected_question = question

    question = st.chat_input("Ask a Google Cloud question...")
    question = question or selected_question

    if question:
        agent = CloudPulseAgent()
        response = agent.build_chat_prompt(question)
        answer = agent.generate(response.content)

        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            st.write(answer)
            if response.sources:
                st.markdown("#### Sources")
                for source in response.sources:
                    st.markdown(f"- {source}")
