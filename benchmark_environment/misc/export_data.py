import json
import redis
import pandas as pd
from openpyxl import load_workbook

r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

def load_documents(keys):
    documents = []

    for key in keys:
        try:
            # Versuch RedisJSON (ReJSON / Redis Stack)
            data = r.json().get(key)
        except:
            # Fallback: normaler String
            raw = r.get(key)
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except:
                continue

        if isinstance(data, dict):
            documents.append(data)

    return documents

def get_all_keys(pattern="*"):
    keys = []
    cursor = 0

    while True:
        cursor, batch = r.scan(cursor=cursor, match=pattern, count=1000)
        keys.extend(batch)
        if cursor == 0:
            break

    return keys

def extract_rows(documents):
    rows = []

    for doc in documents:
        # --- 1. Hersteller & Brand ---
        vendor = doc.get("vendor_csaf_normalized")
        brand = doc.get("brand_csaf_normalized")

        # Fallback (falls aus zweitem JSON)
        if not vendor:
            vendor = doc.get("vendor")

        if not brand:
            # versuche aus tokens zu lesen
            meta = doc.get("meta_info", {})
            tokens = meta.get("whole_tokens", [])
            types = meta.get("types", [])

            if "brand" in types:
                brand = tokens[types.index("brand")]

        # --- 2. Produktserie extrahieren ---
        meta = doc.get("meta_info", {})
        tokens = meta.get("whole_tokens", [])
        types = meta.get("types", [])

        series = None
        if "series_and_sub_series" in types:
            series = tokens[types.index("series_and_sub_series")]

        # --- 3. Nur gültige Datensätze ---
        if vendor and brand and series:
            rows.append({
                "Hersteller": vendor.upper(),
                "Brand": brand.upper(),
                "Produktserie": series
            })

    return rows


def export_to_excel(rows, filename="output.xlsx"):
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
    # --- Spaltenbreite setzen ---
    wb = load_workbook(filename)
    ws = wb.active
    # ca. 100px ≈ 14–15 width
    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 15

    ws.auto_filter.ref = ws.dimensions

    wb.save(filename)
    print(f"Excel erstellt: {filename}")


# --- Beispieldaten ---
documents = [
    {
        "vendor_csaf_normalized": "Siemens",
        "brand_csaf_normalized": "Scalance"
    },
    {
        "vendor": "Siemens",
        "product_type": "SCALANCE W748-1 RJ45",
        "meta_info": {
            "whole_tokens": ["SCALANCE", "W748-1", "RJ45"],
            "types": ["brand", "series_and_sub_series", "feature_series"]
        }
    }
]

def group_and_count(rows):
    import pandas as pd

    df = pd.DataFrame(rows)

    # Gruppieren nach Hersteller + Brand + Produktserie
    grouped = (
        df.groupby(["Hersteller", "Brand", "Produktserie"])
        .size()
        .reset_index(name="Anzahl")
    )

    return grouped

keys = get_all_keys("*")
documents = load_documents(keys)
rows = extract_rows(documents)
grouped = group_and_count(rows)
# TODOModifiy


export_to_excel(grouped)
