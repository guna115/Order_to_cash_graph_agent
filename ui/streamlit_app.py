import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Order-to-Cash Graph Agent", layout="wide")
st.title("Order-to-Cash Graph + Chat")


@st.cache_data(ttl=60)
def load_graph():
    res = requests.get(f"{API_BASE}/graph/data", timeout=60)
    res.raise_for_status()
    return res.json()


def safe_table(data):
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        st.dataframe(data, use_container_width=True)
    else:
        st.json(data)


try:
    graph = load_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
except Exception as e:
    st.error(f"Failed to load graph from API: {e}")
    st.stop()

left, right = st.columns([2, 1])

with left:
    st.subheader("Graph Overview")
    st.metric("Nodes", len(nodes))
    st.metric("Edges", len(edges))

    with st.expander("Sample Nodes (first 20)", expanded=True):
        safe_table(nodes[:20])

    with st.expander("Sample Edges (first 20)", expanded=False):
        safe_table(edges[:20])

with right:
    st.subheader("Chat with Graph")
    question = st.text_area(
        "Ask a dataset question",
        height=120,
        placeholder="Example: Which products are associated with highest number of billing documents?",
    )

    if st.button("Ask"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            try:
                res = requests.post(
                    f"{API_BASE}/ask",
                    json={"question": question},
                    timeout=90,
                )
                res.raise_for_status()
                out = res.json()

                st.success(out.get("answer", "No answer"))
                data = out.get("data", [])
                if data:
                    st.write("Data preview:")
                    safe_table(data)
            except Exception as e:
                st.error(f"Ask failed: {e}")

st.caption("Connected to backend: " + API_BASE)