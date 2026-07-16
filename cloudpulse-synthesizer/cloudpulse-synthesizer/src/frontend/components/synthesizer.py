# src/frontend/components/synthesizer.py
import streamlit as st
# from src.backend.agent import CloudPulseAgent  # <-- Comment out for offline testing
from src.frontend.utils.exporter import build_text_export

LEDGER = [
    {'tag': 'Cloud SQL', 'note': 'Point-in-time recovery for PostgreSQL 16'},
    {'tag': 'Vertex AI', 'note': 'Gemini Code Assist now in Model Garden'},
    {'tag': 'Vertex AI', 'note': 'Batch prediction quota increased 3x'},
    {'tag': 'Compute Engine', 'note': 'C4 machine series GA in 6 more regions'},
    {'tag': 'Cloud SQL', 'note': 'Per-replica maintenance windows'},
    {'tag': 'Compute Engine', 'note': 'Live migration supports local SSD-attached VMs'},
]

def render_synthesizer() -> None:
    left_panel, right_panel = st.columns([3, 1])
    
    with left_panel:
        st.subheader("Product One-Pager Synthesizer")
        st.caption("Testing Mode: Using mock responses instead of active backend agent.")
        st.write("---")
        
        product_name = st.text_input(
            "Google Cloud product",
            placeholder="Example: Compute Engine, Vertex AI, Cloud Run",
        )
        
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            persona = st.selectbox(
                "Audience persona",
                ["Cloud Architect", "Cloud Sales Representative", "TAM", "Developer"],
            )
        with col_form2:
            priority = st.selectbox(
                "Priority",
                ["Critical", "High", "Medium", "Low"],
            )
            
        st.write("##")
        
        if st.button("Generate one-pager", type="primary", use_container_width=True):
            if not product_name.strip():
                st.warning("Enter a Google Cloud product.")
                return
            
            with st.spinner(f"Simulating synthesis matrix for {product_name}..."):
                import time
                time.sleep(1) # Simulates network delay
                
                # --- MOCK AI RESPONSE ---
                result = f"""### MOCK SYNTHESIS ONE-PAGER
**Product:** {product_name}
**Target Audience:** {persona}
**Priority Matrix:** {priority}

**Key Update Summary:**
This is a simulated release block. Under the hood, this update introduces localized optimizations, automatic cluster rebalancing, and enhanced telemetry protocols designed to reduce management overhead for engineering groups.

**Architectural Recommendations:**
- Review staging environments for version compatibility.
- Update internal runbooks to account for the new configuration parameters."""
            
            st.write("---")
            st.markdown(f"### 📑 {product_name} Synthesis Update")
            st.info(result)
            
            export_bytes = build_text_export(result)
            st.download_button(
                "⬇️ Download TXT One-Pager",
                data=export_bytes,
                file_name=f"{product_name.lower().replace(' ', '-')}-one-pager.txt",
                mime="text/plain",
                use_container_width=True
            )
            
    with right_panel:
        st.markdown("### Release Notes")
        st.caption("Synthesized from source changelogs")
        st.write("---")
        
        for item in LEDGER:
            is_match = product_name.strip().lower() in item['tag'].lower() if product_name.strip() else False
            box_icon = "🔥" if is_match else "▫️"
            st.markdown(f"{box_icon} **{item['tag']}**\n\n{item['note']}")
            st.write("---")