from app.graph_builder import build_graph, export_graph_json

if __name__ == "__main__":
    g = build_graph()
    export_graph_json(g)