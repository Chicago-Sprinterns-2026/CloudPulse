import streamlit as st

# --- Import your team's components ---
from src.frontend.components.catalog import render_catalog
from src.frontend.components.chatbot import render_chatbot
from src.frontend.components.settings import render_settings
from src.frontend.components.synthesizer import render_synthesizer

# --- Page Configuration ---
st.set_page_config(
    page_title="CloudPulse Synthesizer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- State Management for Onboarding ---
# This matches the intro screens and wireframes you provided!
if 'onboarding_complete' not in st.session_state:
    st.session_state['onboarding_complete'] = False
if 'current_slide' not in st.session_state:
    st.session_state['current_slide'] = 0

# Onboarding Slides (Derived from your wireframe carousel)
CAROUSEL_SLIDES = [
    {
        "title": "Welcome to CloudPulse",
        "content": "A central workspace to analyze, track, and synthesize fragmented Google Cloud product updates.",
        "icon": "☁️"
    },
    {
        "title": "AI-Powered Synthesis",
        "content": "Stop digging through raw changelogs. Get concise, structured summaries of complex cloud updates.",
        "icon": "🤖"
    },
    {
        "title": "Interactive Troubleshooting",
        "content": "Have questions about how a release affects your architecture? Ask our specialized agent directly.",
        "icon": "💬"
    }
]

def next_slide():
    if st.session_state['current_slide'] < len(CAROUSEL_SLIDES) - 1:
        st.session_state['current_slide'] += 1
    else:
        st.session_state['onboarding_complete'] = True

# ==========================================
# FLOW CONTROL
# ==========================================

# CASE 1: Render Onboarding Carousel (First-time view)
if not st.session_state['onboarding_complete']:
    
    current_idx = st.session_state['current_slide']
    slide = CAROUSEL_SLIDES[current_idx]
    
    # Large onboarding presentation card
    st.write("##")
    st.write("##")
    with st.container():
        st.markdown(f"<h1 style='text-align: center; font-size: 4rem;'>{slide['icon']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{slide['title']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.35rem; color: #888;'>{slide['content']}</p>", unsafe_allow_html=True)
        
        st.write("##")
        st.write("---")
        
        # Navigation buttons matching your intro cards
        col_space, col_main, col_skip, col_space2 = st.columns([2, 3, 1, 2])
        
        with col_main:
            button_label = "Go to Dashboard" if current_idx == len(CAROUSEL_SLIDES) - 1 else "Next"
            st.button(button_label, on_click=next_slide, type="primary", use_container_width=True)
            
        with col_skip:
            if current_idx < len(CAROUSEL_SLIDES) - 1:
                st.button("Skip", on_click=lambda: st.session_state.update({'onboarding_complete': True}), use_container_width=True)
            else:
                st.button("Back", on_click=lambda: st.session_state.update({'current_slide': current_idx - 1}), use_container_width=True)

        # Pagination dots indicator at the bottom (like in wireframe 1)
        dots = ["●" if i == current_idx else "○" for i in range(len(CAROUSEL_SLIDES))]
        st.markdown(f"<p style='text-align: center; font-size: 1.2rem; letter-spacing: 5px; color: #aaa;'>{' '.join(dots)}</p>", unsafe_allow_html=True)

# CASE 2: Main Application Dashboard (Once onboarding is finished)
else:
    # Sidebar Navigation matching your original code
    with st.sidebar:
        st.markdown("## Navigation")
        page = st.radio(
            "Go to page:",
            ["Product Synthesizer", "Troubleshooting Chat", "Product Catalog", "Settings"],
            label_visibility="collapsed"
        )
        st.write("---")
        # Add a quick link to let users replay the onboarding if they want
        st.button("Replay Onboarding Guide", on_click=lambda: st.session_state.update({'onboarding_complete': False, 'current_slide': 0}), use_container_width=True)

    # Render pages dynamically based on sidebar selection
    if page == "Product Synthesizer":
        render_synthesizer()
    elif page == "Troubleshooting Chat":
        render_chatbot()
    elif page == "Product Catalog":
        render_catalog()
    else:
        render_settings()