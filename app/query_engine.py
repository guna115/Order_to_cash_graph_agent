import sqlite3
from app.config import DB_PATH

def _conn():
    return sqlite3.connect(DB_PATH)

def _rows_to_dict(cursor, rows):
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]

def query_top_products_by_billing_docs(limit: int = 10):
    sql = """
    SELECT
      soi.product_id,
      COUNT(DISTINCT b.billing_id) AS billing_doc_count
    FROM billing_documents b
    LEFT JOIN delivery_item_links dil
      ON CAST(dil.delivery_id AS TEXT) = CAST(b.delivery_id AS TEXT)
    LEFT JOIN sales_order_items soi
      ON CAST(soi.sales_order_id AS TEXT) = CAST(dil.sales_order_id AS TEXT)
    WHERE soi.product_id IS NOT NULL
    GROUP BY soi.product_id
    ORDER BY billing_doc_count DESC
    LIMIT ?
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute(sql, (limit,))
    rows = cur.fetchall()
    data = _rows_to_dict(cur, rows)
    conn.close()
    return data

def query_trace_billing_flow(billing_id: str):
    sql = """
    SELECT
      b.billing_id,
      b.sales_order_id,
      b.delivery_id,
      j.journal_entry_id,
      j.accounting_document
    FROM billing_documents b
    LEFT JOIN journal_entries j
      ON CAST(j.billing_id AS TEXT) = CAST(b.billing_id AS TEXT)
    WHERE CAST(b.billing_id AS TEXT) = CAST(? AS TEXT)
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute(sql, (billing_id,))
    rows = cur.fetchall()
    data = _rows_to_dict(cur, rows)
    conn.close()
    return data

def query_broken_flows(limit: int = 50):
    # 1) Orders without any linked delivery
    sql1 = """
    SELECT so.sales_order_id, 'ORDER_WITHOUT_DELIVERY' AS issue_type
    FROM sales_orders so
    LEFT JOIN delivery_item_links dil
      ON CAST(dil.sales_order_id AS TEXT) = CAST(so.sales_order_id AS TEXT)
    WHERE dil.link_id IS NULL
    """

    # 2) Deliveries without billing
    sql2 = """
    SELECT d.delivery_id AS sales_order_id, 'DELIVERY_WITHOUT_BILLING' AS issue_type
    FROM deliveries d
    LEFT JOIN billing_documents b
      ON CAST(b.delivery_id AS TEXT) = CAST(d.delivery_id AS TEXT)
    WHERE b.billing_id IS NULL
    """

    conn = _conn()
    cur = conn.cursor()

    cur.execute(sql1)
    rows1 = _rows_to_dict(cur, cur.fetchall())

    cur.execute(sql2)
    rows2 = _rows_to_dict(cur, cur.fetchall())

    conn.close()

    merged = rows1 + rows2
    return merged[:limit]

def answer_question(question: str):
    q = question.lower().strip()

    if "highest number of billing" in q or ("top" in q and "product" in q and "billing" in q):
        data = query_top_products_by_billing_docs(limit=10)
        if not data:
            return {"answer": "No matching data found.", "data": []}
        top = data[0]
        answer = (
            f"Top product by billing-document association is {top['product_id']} "
            f"with {top['billing_doc_count']} billing documents."
        )
        return {"answer": answer, "data": data}

    if "trace" in q and "billing" in q:
        # try to extract billing id as last token number-ish
        tokens = question.replace("?", " ").split()
        billing_id = None
        for t in reversed(tokens):
            if any(ch.isdigit() for ch in t):
                billing_id = t.strip()
                break
        if not billing_id:
            return {"answer": "Please provide a billing document id to trace.", "data": []}
        data = query_trace_billing_flow(billing_id)
        if not data:
            return {"answer": f"No flow found for billing document {billing_id}.", "data": []}
        row = data[0]
        answer = (
            f"Flow for billing {row['billing_id']}: "
            f"SalesOrder={row['sales_order_id']}, Delivery={row['delivery_id']}, "
            f"JournalEntry={row['journal_entry_id']}."
        )
        return {"answer": answer, "data": data}

    if "broken" in q or "incomplete flow" in q or "delivered but not billed" in q:
        data = query_broken_flows(limit=50)
        if not data:
            return {"answer": "No broken flows found.", "data": []}
        answer = f"Found {len(data)} potentially broken/incomplete flow records."
        return {"answer": answer, "data": data}

    return {
        "answer": (
            "I can help with dataset-specific queries such as:\n"
            "1) Top products by billing document count\n"
            "2) Trace billing flow by billing id\n"
            "3) Broken/incomplete order-to-cash flows"
        ),
        "data": []
    }