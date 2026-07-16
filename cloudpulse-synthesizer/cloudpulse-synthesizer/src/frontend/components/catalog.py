# src/frontend/components/catalog.py
import streamlit as st

PRODUCTS = {
    'compute': {
        'name': 'Compute Engine',
        'tag': 'Virtual machines, resized on demand',
        'icon': '⚙️',
        'meta': 'updated this cycle'
    },
    'vertex': {
        'name': 'Vertex AI',
        'tag': 'Train, tune, and serve models',
        'icon': '✦',
        'meta': 'updated this cycle'
    },
    'cloudsql': {
        'name': 'Cloud SQL',
        'tag': 'Managed relational databases',
        'icon': '⚃',
        'meta': 'updated this cycle'
    }
}

def render_catalog():
    # Grid setup matching the HTML wireframe
    st.markdown("### Product Catalog")
    st.caption("Select a product below to view active release notes.")
    
    cols = st.columns(3)
    
    for idx, (key, p) in enumerate(PRODUCTS.items()):
        with cols[idx % 3]:
            # Native Streamlit container styling to mimic the wireframe design cards
            with st.container(border=True):
                st.markdown(f"### {p['icon']} {p['name']}")
                st.markdown(f"*{p['tag']}*")
                st.markdown(f"🔴 **{p['meta']}**")
                
                # Navigate to the synthesizer view if clicked
                if st.button(f"View {p['name']} Notes", key=f"btn_{key}", use_container_width=True):
                    st.session_state['selected_product'] = key
                    st.session_state['page_selection'] = "Product Synthesizer"
                    st.rerun()