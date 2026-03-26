SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT,
    email TEXT,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS addresses (
    address_id TEXT PRIMARY KEY,
    customer_id TEXT,
    line1 TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    postal_code TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    unit_price REAL
);

CREATE TABLE IF NOT EXISTS sales_orders (
    sales_order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_date TEXT,
    status TEXT,
    total_amount REAL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS sales_order_items (
    so_item_id TEXT PRIMARY KEY,
    sales_order_id TEXT,
    product_id TEXT,
    quantity REAL,
    unit_price REAL,
    line_total REAL,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(sales_order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id TEXT PRIMARY KEY,
    sales_order_id TEXT,
    delivery_date TEXT,
    plant TEXT,
    status TEXT,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(sales_order_id)
);

CREATE TABLE IF NOT EXISTS delivery_item_links (
    link_id TEXT PRIMARY KEY,
    delivery_id TEXT,
    sales_order_id TEXT,
    sales_order_item_id TEXT,
    product_id TEXT
);

CREATE TABLE IF NOT EXISTS billing_documents (
    billing_id TEXT PRIMARY KEY,
    delivery_id TEXT,
    sales_order_id TEXT,
    billing_date TEXT,
    amount REAL,
    status TEXT,
    FOREIGN KEY (delivery_id) REFERENCES deliveries(delivery_id),
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(sales_order_id)
);

CREATE TABLE IF NOT EXISTS journal_entries (
    journal_entry_id TEXT PRIMARY KEY,
    billing_id TEXT,
    accounting_document TEXT,
    company_code TEXT,
    fiscal_year TEXT,
    amount REAL,
    currency TEXT,
    posting_date TEXT,
    FOREIGN KEY (billing_id) REFERENCES billing_documents(billing_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    billing_id TEXT,
    payment_date TEXT,
    amount REAL,
    method TEXT,
    status TEXT,
    FOREIGN KEY (billing_id) REFERENCES billing_documents(billing_id)
);
"""