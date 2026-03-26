# Order-to-Cash Knowledge Graph Agent

An AI-powered **Order-to-Cash (O2C)** analytics assistant that:
- builds a graph from ERP-style transactional data,
- exposes graph-aware APIs via FastAPI,
- answers natural-language business questions using an LLM (Groq),
- and includes a Streamlit UI for interactive exploration.

---

## Live Deployment

### Backend (Live)
- **Base URL:** https://o2c-fastapi.onrender.com
- **Health:** https://o2c-fastapi.onrender.com/health
- **Graph Summary:** https://o2c-fastapi.onrender.com/graph/summary
- **API Docs:** https://o2c-fastapi.onrender.com/docs

### Frontend
- Streamlit frontend code is included in `ui/streamlit_app.py`.
- (If frontend public URL is available, add it here.)

---

## Problem Statement

Business users in Order-to-Cash workflows need quick answers to operational questions such as:
- Which customers have delayed billing?
- Which products are linked to high dispute volume?
- Which invoices are related to multiple deliveries or payment issues?

Traditional dashboards are static and SQL queries are not user-friendly for non-technical users.  
This project solves that by combining:
1. **Knowledge graph modeling** of O2C entities and relationships,
2. **Natural-language querying** through an LLM-powered API,
3. **Guardrails** for domain-restricted answers.

---

## Features

- Build graph from structured O2C data (`nodes`, `edges`)
- FastAPI endpoints for:
  - graph data and summary
  - LLM-powered Q&A
- Domain guardrails for O2C-only responses
- Streamlit interface for business-friendly interaction
- Render-ready deployment setup

---

## Tech Stack

- **Backend:** FastAPI, Uvicorn
- **Data/Graph:** Pandas, NetworkX, SQLite (processed data)
- **LLM:** Groq API
- **Frontend:** Streamlit
- **Deployment:** Render (backend), Streamlit Cloud/Render-compatible frontend

---

## Repository Structure

```text
order_to_cash_graph_agent/
├─ app/
│  ├─ main.py                 # FastAPI app & routes
│  ├─ llm/
│  │  └─ groq_client.py       # Groq integration
│  └─ services/               # Graph/query service logic
├─ data/
│  ├─ raw/                    # Input ERP-like datasets
│  └─ processed/              # Generated db/json graph artifacts
├─ scripts/
│  ├─ run_ingestion.py        # Data ingestion pipeline
│  └─ run_graph_build.py      # Graph build pipeline
├─ ui/
│  ��─ streamlit_app.py        # Streamlit frontend
├─ start.sh                   # Startup command (cloud runtime)
├─ render.yaml                # Render blueprint/service config
├─ requirements.txt
└─ README.md
```

---

## API Endpoints

### `GET /health`
Returns service health status.

### `GET /graph/summary`
Returns graph-level statistics (e.g., node/edge counts, labels).

### `GET /graph/data`
Returns graph payload (nodes + edges) for visualization/analysis.

### `POST /ask`
Answers natural-language O2C questions using LLM + graph context.

**Example request:**
```json
{
  "question": "Which products are associated with the highest number of billing documents?"
}
```

---

## Local Setup

## 1) Clone repository
```bash
git clone https://github.com/guna115/Order_to_cash_graph_agent.git
cd Order_to_cash_graph_agent
```

## 2) Create virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

## 3) Install dependencies
```bash
pip install -r requirements.txt
```

## 4) Set environment variables
Create `.env` (or export in shell):
```env
GROQ_API_KEY=your_groq_api_key
```

## 5) (Optional) Build data artifacts
If processed files are not present:
```bash
python scripts/run_ingestion.py
python scripts/run_graph_build.py
```

## 6) Run backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 7) Run frontend
```bash
streamlit run ui/streamlit_app.py
```

---

## Deployment Notes

## Backend on Render
- Start command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```
- Required env:
  - `GROQ_API_KEY`

## Frontend
- Streamlit app consumes backend via:
  - `API_BASE_URL` (e.g., `https://o2c-fastapi.onrender.com`)

---

## Guardrails / Scope Control

The assistant is constrained to **Order-to-Cash domain** queries.  
Off-topic prompts are rejected with a safe response.

Examples of in-scope:
- order, invoice, billing, payment, customer, product, delivery, disputes

Examples of out-of-scope:
- general trivia, unrelated coding tasks, non-business random questions

---

## Known Limitations

- First request on free-tier hosting may be slower (cold start).
- Public Streamlit deployment can vary by platform dependency resolution.
- LLM responses depend on available graph/context quality.

---

## AI Usage Disclosure

This project was developed with AI assistance (GitHub Copilot / LLM support) for:
- code scaffolding,
- API and UI refinement,
- deployment troubleshooting,
- documentation drafting.

Human review, integration, debugging, and final validation were performed before submission.

---

## Author

- GitHub: [guna115](https://github.com/guna115)

---

## License

For assignment/evaluation use.  
(Add formal license if required, e.g., MIT.)
