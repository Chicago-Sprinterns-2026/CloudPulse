# src/frontend/components/chatbot.py
import streamlit as st
# from src.backend.agent import CloudPulseAgent  # <-- Comment out for offline testing

QUICK_QUESTIONS = [
    "What recent changes affect my deployment?",
    "Are there upcoming deprecations?",
    "What troubleshooting steps should I try first?",
]

def render_chatbot() -> None:
    st.subheader("💬 Troubleshooting Assistant")
    st.caption("Testing Mode: Using mock responses instead of active backend agent.")
    st.write("---")

    st.write("**Quick Questions:**")
    columns = st.columns(len(QUICK_QUESTIONS))
    selected_question = None

    for column, question in zip(columns, QUICK_QUESTIONS):
        if column.button(f"💡 {question}", use_container_width=True):
            selected_question = question

    st.write("##")

    question_input = st.chat_input("Ask a Google Cloud question...")
    final_query = question_input or selected_question

    if final_query:
        # 1. Render User message bubble
        with st.chat_message("user"):
            st.write(final_query)
            
        # 2. Render Assistant response bubble with static text
        with st.chat_message("assistant"):
            st.write(f"This is a simulated answer to your question: *'{final_query}'*")
            st.write("Would you like the technical rundown, or a simpler explanation?")

    # Quick reply option chips logic
    col1, col2, _ = st.columns([1, 1, 2])
    with col1:
        if st.button("🔧 Technical details", use_container_width=True):
            st.chat_message("assistant").write("Mock Technical Answer: Under the hood, this ships via a new WAL-streaming replica mode, with restore handled through the existing backups API — no schema changes required.")
    with col2:
        if st.button("💡 Simpler explanation", use_container_width=True):
            st.chat_message("assistant").write("Mock Simple Answer: In short: you can now roll a database back to almost any second in the past, without taking the live database down to do it.")