import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
import os
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Order-to-Cash Graph Agent", layout="wide")
st.title("Order-to-Cash Graph + Chat")

@st.cache_data
def load_graph():
    res = requests.get(f"{API_BASE}/graph/data")
    res.raise_for_status()
    return res.json()

def build_plot(nodes, edges, max_nodes=400):
    # limit for browser performance
    nodes = nodes[:max_nodes]
    node_ids = set(n["id"] for n in nodes)
    edges = [e for e in edges if e["source"] in node_ids and e["target"] in node_ids]

    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"], label=n.get("label", "Entity"))
    for e in edges:
        G.add_edge(e["source"], e["target"], relation=e.get("relation", "RELATED_TO"))

    pos = nx.spring_layout(G, k=0.4, iterations=40, seed=42)

    edge_x, edge_y = [], []
    for s, t in G.edges():
        x0, y0 = pos[s]
        x1, y1 = pos[t]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.6),
        hoverinfo="none",
        mode="lines"
    )

    node_x, node_y, node_text = [], [], []
    for n in G.nodes():
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        node_text.append(n)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(size=8)
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        height=650
    )
    return fig

try:
    graph = load_graph()
    nodes = graph["nodes"]
    edges = graph["edges"]
except Exception as e:
    st.error(f"Failed to load graph from API: {e}")
    st.stop()

left, right = st.columns([2, 1])

with left:
    st.subheader("Graph View")
    max_nodes = st.slider("Max nodes to render", 50, 800, 400, 50)
    fig = build_plot(nodes, edges, max_nodes=max_nodes)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Chat with Graph")
    question = st.text_area("Ask a dataset question", height=120, placeholder="Example: Which products are associated with highest number of billing documents?")
    if st.button("Ask"):
        try:
            res = requests.post(f"{API_BASE}/ask", json={"question": question}, timeout=60)
            res.raise_for_status()
            out = res.json()
            st.success(out.get("answer", "No answer"))
            data = out.get("data", [])
            if data:
                st.write("Data preview:")
                st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(f"Ask failed: {e}")

st.caption("Tip: Run backend first (uvicorn), then this Streamlit app.")