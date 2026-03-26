import os
import glob
import json
import sqlite3
import pandas as pd
from app.config import DB_PATH
from app.models import SCHEMA_SQL

DATA_DIR = "data"

TABLE_MAP = {
    "business_partners": "customers",
    "business_partner_addresses": "addresses",
    "products": "products",
    "product_descriptions": "products",
    "sales_order_headers": "sales_orders",
    "sales_order_items": "sales_order_items",
    "outbound_delivery_headers": "deliveries",
    "outbound_delivery_items": "delivery_item_links",
    "billing_document_headers": "billing_documents",
    "journal_entry_items_accounts_receivable": "journal_entries",
    "payments_accounts_receivable": "payments",
}

TABLE_COLUMNS = {
    "customers": ["customer_id", "customer_name", "email", "phone"],
    "addresses": ["address_id", "customer_id", "line1", "city", "state", "country", "postal_code"],
    "products": ["product_id", "product_name", "category", "unit_price"],
    "sales_orders": ["sales_order_id", "customer_id", "order_date", "status", "total_amount"],
    "sales_order_items": ["so_item_id", "sales_order_id", "product_id", "quantity", "unit_price", "line_total"],
    "deliveries": ["delivery_id", "sales_order_id", "delivery_date", "plant", "status"],
    "delivery_item_links": ["link_id", "delivery_id", "sales_order_id", "sales_order_item_id", "product_id"],
    "billing_documents": ["billing_id", "delivery_id", "sales_order_id", "billing_date", "amount", "status"],
    "journal_entries": ["journal_entry_id", "billing_id", "accounting_document", "company_code", "fiscal_year", "amount", "currency", "posting_date"],
    "payments": ["payment_id", "billing_id", "payment_date", "amount", "method", "status"],
}

# ------------------ UTIL ------------------

def connect_db():
    return sqlite3.connect(DB_PATH)

def create_schema(conn):
    conn.executescript(SCHEMA_SQL)
    conn.commit()

def normalize_columns(df):
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

def make_hashable(df):
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: json.dumps(x, sort_keys=True) if isinstance(x, (dict, list)) else x
        )
    return df

def load_jsonl_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, "*.jsonl"))
    frames = []

    for f in files:
        try:
            df = pd.read_json(f, lines=True)
            df = make_hashable(df)
            frames.append(df)
            print(f"[OK] Read {f} ({len(df)} rows)")
        except Exception as e:
            print(f"[ERROR] {f}: {e}")

    if not frames:
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True)
    merged = make_hashable(merged)
    merged = merged.drop_duplicates()
    return merged

def pick_first_existing(df, candidates):
    for c in candidates:
        if c in df.columns:
            return df[c]
    return None

# ------------------ MAPPERS ------------------

def map_to_customers(df):
    return pd.DataFrame({
        "customer_id": pick_first_existing(df, ["businesspartner"]),
        "customer_name": pick_first_existing(df, ["businesspartnername"]),
        "email": pick_first_existing(df, ["emailaddress"]),
        "phone": pick_first_existing(df, ["phonenumber"]),
    })

def map_to_addresses(df):
    return pd.DataFrame({
        "address_id": pick_first_existing(df, ["addressid"]),
        "customer_id": pick_first_existing(df, ["businesspartner"]),
        "line1": pick_first_existing(df, ["streetname"]),
        "city": pick_first_existing(df, ["cityname"]),
        "state": pick_first_existing(df, ["region"]),
        "country": pick_first_existing(df, ["country"]),
        "postal_code": pick_first_existing(df, ["postalcode"]),
    })

def map_to_products(df):
    return pd.DataFrame({
        "product_id": pick_first_existing(df, ["product", "material"]),
        "product_name": pick_first_existing(df, ["productdescription"]),
        "category": pick_first_existing(df, ["producttype"]),
        "unit_price": pick_first_existing(df, ["netpriceamount"]),
    })

def map_to_sales_orders(df):
    return pd.DataFrame({
        "sales_order_id": pick_first_existing(df, ["salesorder"]),
        "customer_id": pick_first_existing(df, ["soldtoparty"]),
        "order_date": pick_first_existing(df, ["salesorderdate"]),
        "status": pick_first_existing(df, ["overallprocessingstatus"]),
        "total_amount": pick_first_existing(df, ["totalnetamount"]),
    })

def map_to_sales_order_items(df):
    so = pick_first_existing(df, ["salesorder"])
    item = pick_first_existing(df, ["salesorderitem"])

    return pd.DataFrame({
        "so_item_id": so.astype(str) + "-" + item.astype(str),
        "sales_order_id": so,
        "product_id": pick_first_existing(df, ["product"]),
        "quantity": pick_first_existing(df, ["orderquantity"]),
        "unit_price": pick_first_existing(df, ["netpriceamount"]),
        "line_total": pick_first_existing(df, ["itemnetamount"]),
    })

# ✅ FIXED deliveries
def map_to_deliveries(df):
    return pd.DataFrame({
        "delivery_id": pick_first_existing(df, ["deliverydocument", "outbounddelivery"]),
        "sales_order_id": None,
        "delivery_date": pick_first_existing(df, ["actualgoodsmovementdate"]),
        "plant": pick_first_existing(df, ["shippingpoint"]),
        "status": pick_first_existing(df, ["overallgoodsmovementstatus"]),
    })

# ✅ FIXED safe version
def map_to_delivery_item_links(df):
    delivery = pick_first_existing(df, ["outbounddelivery", "deliverydocument"])
    so = pick_first_existing(df, ["referencesddocument", "salesorder"])
    so_item = pick_first_existing(df, ["referencesddocumentitem", "salesorderitem"])
    product = pick_first_existing(df, ["product"])

    out = pd.DataFrame({
        "delivery_id": delivery,
        "sales_order_id": so,
        "sales_order_item_id": so_item,
        "product_id": product,
    })

    d = out["delivery_id"].astype(str).fillna("NA")
    s = out["sales_order_id"].astype(str).fillna("NA")
    i = out["sales_order_item_id"].astype(str).fillna("NA")

    out["link_id"] = d + "-" + s + "-" + i

    return out

def map_to_billing(df):
    return pd.DataFrame({
        "billing_id": pick_first_existing(df, ["billingdocument"]),
        "delivery_id": pick_first_existing(df, ["referencesddocument"]),
        "sales_order_id": pick_first_existing(df, ["salesorder"]),
        "billing_date": pick_first_existing(df, ["billingdocumentdate"]),
        "amount": pick_first_existing(df, ["totalnetamount"]),
        "status": pick_first_existing(df, ["overallbillingstatus"]),
    })

def map_to_journal(df):
    return pd.DataFrame({
        "journal_entry_id": pick_first_existing(df, ["accountingdocument"]),
        "billing_id": pick_first_existing(df, ["referencekey1"]),
        "accounting_document": pick_first_existing(df, ["accountingdocument"]),
        "company_code": pick_first_existing(df, ["companycode"]),
        "fiscal_year": pick_first_existing(df, ["fiscalyear"]),
        "amount": pick_first_existing(df, ["amountincompanycodecurrency"]),
        "currency": pick_first_existing(df, ["companycodecurrency"]),
        "posting_date": pick_first_existing(df, ["postingdate"]),
    })

def map_to_payments(df):
    return pd.DataFrame({
        "payment_id": pick_first_existing(df, ["accountingdocument"]),
        "billing_id": pick_first_existing(df, ["referencekey1"]),
        "payment_date": pick_first_existing(df, ["postingdate"]),
        "amount": pick_first_existing(df, ["amountincompanycodecurrency"]),
        "method": pick_first_existing(df, ["paymentmethod"]),
        "status": pick_first_existing(df, ["clearingstatus"]),
    })

MAPPERS = {
    "customers": map_to_customers,
    "addresses": map_to_addresses,
    "products": map_to_products,
    "sales_orders": map_to_sales_orders,
    "sales_order_items": map_to_sales_order_items,
    "deliveries": map_to_deliveries,
    "delivery_item_links": map_to_delivery_item_links,
    "billing_documents": map_to_billing,
    "journal_entries": map_to_journal,
    "payments": map_to_payments,
}

# ------------------ CLEAN ------------------

def fit_and_clean(df, table):
    df = normalize_columns(df)
    mapped = MAPPERS[table](df)

    cols = TABLE_COLUMNS[table]
    for c in cols:
        if c not in mapped.columns:
            mapped[c] = None

    mapped = mapped[cols]
    pk = cols[0]

    mapped = mapped.drop_duplicates(subset=[pk])
    mapped = make_hashable(mapped)

    mapped = mapped[mapped[pk].notna()]
    mapped[pk] = mapped[pk].astype(str)

    return mapped

# ------------------ MAIN ------------------

def ingest_all():
    conn = connect_db()
    create_schema(conn)

    folders = [f for f in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, f))]
    print(f"[INFO] Found folders: {folders}")

    buckets = {t: [] for t in TABLE_COLUMNS.keys()}

    for folder in folders:
        if folder in ["processed", "raw"]:
            continue

        df = load_jsonl_folder(os.path.join(DATA_DIR, folder))
        if df.empty:
            continue

        target = TABLE_MAP.get(folder)
        if not target:
            print(f"[SKIP] {folder}")
            continue

        cleaned = fit_and_clean(df, target)
        buckets[target].append(cleaned)
        print(f"[OK] {folder} -> {target} ({len(cleaned)} rows)")

    # FK safe delete
    delete_order = [
        "payments", "journal_entries", "billing_documents",
        "delivery_item_links", "deliveries",
        "sales_order_items", "sales_orders",
        "addresses", "customers", "products"
    ]

    for t in delete_order:
        try:
            conn.execute(f"DELETE FROM {t}")
        except Exception as e:
            print(f"[WARN] {t}: {e}")

    # insert
    for table, dfs in buckets.items():
        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            pk = TABLE_COLUMNS[table][0]
            merged = merged.drop_duplicates(subset=[pk])
            merged = make_hashable(merged)

            merged.to_sql(table, conn, if_exists="append", index=False)
            print(f"[OK] Inserted {len(merged)} into {table}")

    conn.commit()
    conn.close()
    print("[DONE] Ingestion complete")