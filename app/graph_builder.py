import json
import os
import sqlite3
import networkx as nx
from app.config import DB_PATH

OUTPUT_NODES = "data/processed/nodes.json"
OUTPUT_EDGES = "data/processed/edges.json"

def ensure_output_dirs():
    os.makedirs("data/processed", exist_ok=True)

def fetch_all(conn, query):
    cur = conn.cursor()
    cur.execute(query)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return [dict(zip(cols, r)) for r in rows]

def node_id(entity_type: str, key: str):
    return f"{entity_type}:{key}"

def safe_add_node(G, entity_type, key, attrs):
    if key is None:
        return
    k = str(key)
    if k.lower() == "none" or k.strip() == "":
        return
    nid = node_id(entity_type, k)
    G.add_node(nid, entity_type=entity_type, **attrs)

def safe_add_edge(G, src_type, src_key, dst_type, dst_key, relation):
    if src_key is None or dst_key is None:
        return
    s = str(src_key).strip()
    d = str(dst_key).strip()
    if s == "" or d == "" or s.lower() == "none" or d.lower() == "none":
        return
    G.add_edge(node_id(src_type, s), node_id(dst_type, d), relation=relation)

def build_graph():
    conn = sqlite3.connect(DB_PATH)
    G = nx.DiGraph()

    customers = fetch_all(conn, "SELECT * FROM customers")
    addresses = fetch_all(conn, "SELECT * FROM addresses")
    products = fetch_all(conn, "SELECT * FROM products")
    sales_orders = fetch_all(conn, "SELECT * FROM sales_orders")
    so_items = fetch_all(conn, "SELECT * FROM sales_order_items")
    deliveries = fetch_all(conn, "SELECT * FROM deliveries")
    delivery_links = fetch_all(conn, "SELECT * FROM delivery_item_links")
    billings = fetch_all(conn, "SELECT * FROM billing_documents")
    journals = fetch_all(conn, "SELECT * FROM journal_entries")
    payments = fetch_all(conn, "SELECT * FROM payments")

    # Nodes
    for r in customers:
        safe_add_node(G, "Customer", r.get("customer_id"), r)
    for r in addresses:
        safe_add_node(G, "Address", r.get("address_id"), r)
    for r in products:
        safe_add_node(G, "Product", r.get("product_id"), r)
    for r in sales_orders:
        safe_add_node(G, "SalesOrder", r.get("sales_order_id"), r)
    for r in so_items:
        safe_add_node(G, "SalesOrderItem", r.get("so_item_id"), r)
    for r in deliveries:
        safe_add_node(G, "Delivery", r.get("delivery_id"), r)
    for r in billings:
        safe_add_node(G, "Billing", r.get("billing_id"), r)
    for r in journals:
        safe_add_node(G, "JournalEntry", r.get("journal_entry_id"), r)
    for r in payments:
        safe_add_node(G, "Payment", r.get("payment_id"), r)

    # Edges
    for r in addresses:
        safe_add_edge(G, "Customer", r.get("customer_id"), "Address", r.get("address_id"), "CUSTOMER_HAS_ADDRESS")

    for r in sales_orders:
        safe_add_edge(G, "Customer", r.get("customer_id"), "SalesOrder", r.get("sales_order_id"), "CUSTOMER_PLACED_ORDER")

    for r in so_items:
        safe_add_edge(G, "SalesOrder", r.get("sales_order_id"), "SalesOrderItem", r.get("so_item_id"), "ORDER_HAS_ITEM")
        safe_add_edge(G, "SalesOrderItem", r.get("so_item_id"), "Product", r.get("product_id"), "ITEM_FOR_PRODUCT")

    # IMPORTANT: connect through delivery_item_links
    for r in delivery_links:
        safe_add_edge(G, "SalesOrder", r.get("sales_order_id"), "Delivery", r.get("delivery_id"), "ORDER_TO_DELIVERY")
        # optional detailed link to product context
        safe_add_edge(G, "Delivery", r.get("delivery_id"), "Product", r.get("product_id"), "DELIVERY_CONTAINS_PRODUCT")

    # Billing links
    for r in billings:
        if r.get("delivery_id") is not None and str(r.get("delivery_id")).strip() not in ["", "None", "none"]:
            safe_add_edge(G, "Delivery", r.get("delivery_id"), "Billing", r.get("billing_id"), "DELIVERY_TO_BILLING")
        else:
            safe_add_edge(G, "SalesOrder", r.get("sales_order_id"), "Billing", r.get("billing_id"), "ORDER_TO_BILLING")

    # Journal / Payment
    for r in journals:
        safe_add_edge(G, "Billing", r.get("billing_id"), "JournalEntry", r.get("journal_entry_id"), "BILLING_TO_JOURNAL")

    for r in payments:
        safe_add_edge(G, "Billing", r.get("billing_id"), "Payment", r.get("payment_id"), "BILLING_TO_PAYMENT")

    conn.close()
    return G

def export_graph_json(G: nx.DiGraph):
    ensure_output_dirs()

    nodes = []
    for nid, attrs in G.nodes(data=True):
        nodes.append({
            "id": nid,
            "label": attrs.get("entity_type", "Entity"),
            "metadata": attrs
        })

    edges = []
    for src, dst, attrs in G.edges(data=True):
        edges.append({
            "source": src,
            "target": dst,
            "relation": attrs.get("relation", "RELATED_TO")
        })

    with open(OUTPUT_NODES, "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=2)

    with open(OUTPUT_EDGES, "w", encoding="utf-8") as f:
        json.dump(edges, f, indent=2)

    print(f"[OK] Exported {len(nodes)} nodes -> {OUTPUT_NODES}")
    print(f"[OK] Exported {len(edges)} edges -> {OUTPUT_EDGES}")