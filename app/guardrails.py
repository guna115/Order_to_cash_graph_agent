DOMAIN_KEYWORDS = [
    "sales order", "order", "delivery", "billing", "invoice", "journal", "payment",
    "customer", "product", "flow", "document", "order-to-cash", "o2c"
]

OUT_OF_SCOPE_REPLY = "This system is designed to answer questions related to the provided dataset only."

def is_in_domain(question: str) -> bool:
    q = (question or "").lower().strip()
    if not q:
        return False
    return any(k in q for k in DOMAIN_KEYWORDS)