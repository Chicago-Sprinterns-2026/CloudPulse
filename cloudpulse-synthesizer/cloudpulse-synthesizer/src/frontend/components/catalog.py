"""Product catalog UI."""

import streamlit as st


SAMPLE_PRODUCTS = [
    {"name": "BigQuery", "category": "Data Analytics"},
    {"name": "Cloud Run", "category": "Serverless"},
    {"name": "Vertex AI", "category": "AI and Machine Learning"},
]


def render_catalog() -> None:
    st.header("Product Catalog")

    categories = ["All"] + sorted(
        {product["category"] for product in SAMPLE_PRODUCTS}
    )
    selected_category = st.selectbox("Filter by category", categories)

    products = SAMPLE_PRODUCTS
    if selected_category != "All":
        products = [
            product
            for product in products
            if product["category"] == selected_category
        ]

    for product in products:
        with st.container(border=True):
            st.subheader(product["name"])
            st.caption(product["category"])
            st.write("Product details and update history will appear here.")
