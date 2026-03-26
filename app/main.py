from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import json
from pydantic import BaseModel

from app.guardrails import is_in_domain, OUT_OF_SCOPE_REPLY
from app.query_engine import answer_question

app = FastAPI(
    title="Order-to-Cash Graph Agent",
    version="1.0.0"
)

class AskRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "Order-to-Cash Graph Agent API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/graph/summary")
def graph_summary():
    nodes_path = "data/processed/nodes.json"
    edges_path = "data/processed/edges.json"

    if not os.path.exists(nodes_path) or not os.path.exists(edges_path):
        return JSONResponse(
            status_code=404,
            content={"error": "Graph files not found. Run graph build first."}
        )

    with open(nodes_path, "r", encoding="utf-8") as f:
        nodes = json.load(f)
    with open(edges_path, "r", encoding="utf-8") as f:
        edges = json.load(f)

    return {"total_nodes": len(nodes), "total_edges": len(edges)}

@app.get("/graph/data")
def graph_data(limit_nodes: int = 1500, limit_edges: int = 3000):
    nodes_path = "data/processed/nodes.json"
    edges_path = "data/processed/edges.json"

    if not os.path.exists(nodes_path) or not os.path.exists(edges_path):
        return JSONResponse(
            status_code=404,
            content={"error": "Graph files not found. Run graph build first."}
        )

    with open(nodes_path, "r", encoding="utf-8") as f:
        nodes = json.load(f)
    with open(edges_path, "r", encoding="utf-8") as f:
        edges = json.load(f)

    return {
        "nodes": nodes[:limit_nodes],
        "edges": edges[:limit_edges],
        "returned_nodes": min(len(nodes), limit_nodes),
        "returned_edges": min(len(edges), limit_edges),
    }

@app.post("/ask")
def ask(req: AskRequest):
    question = (req.question or "").strip()

    if not is_in_domain(question):
        return {"answer": OUT_OF_SCOPE_REPLY, "data": []}

    result = answer_question(question)
    return result