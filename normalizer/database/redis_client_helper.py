import json
import redis
import pandas as pd
from openpyxl import load_workbook
import os

from matcher.lib.token_enum import TokenSemanticEnum


def _coerce_document(data):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return None

    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
        data = data[0]

    if isinstance(data, dict):
        return data

    return None


def load_documents(keys):
    documents = []

    for key in keys:
        data = None
        try:
            host = os.environ.get("REDIS_HOST", "redis2026")
            port = os.environ.get("REDIS_PORT", 6379)
            r = redis.Redis(host=host, port=port, decode_responses=True)
            data = r.json().get(key)
        except Exception as e:
            # Fallback: normaler String
            raw = r.get(key)
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except:
                continue

        document = _coerce_document(data)
        if document is not None:
            documents.append(document)

    return documents

def get_all_keys(pattern="*"):
    keys = []
    cursor = 0
    host = os.environ.get("REDIS_HOST", "redis2026")
    port = os.environ.get("REDIS_PORT", 6379)
    r = redis.Redis(host=host, port=port, decode_responses=True)
    while True:
        cursor, batch = r.scan(cursor=cursor, match=pattern, count=1000)
        keys.extend(batch)
        if cursor == 0:
            break

    return keys

def extract_rows_vendor_and_brand(documents):
    rows = []

    for doc in documents:
        # --- 1. Hersteller & Brand ---
        vendor = doc.get("vendor_csaf_normalized")
        brand = doc.get("brand_csaf_normalized")
        if not vendor:
            vendor = doc.get("vendor")

        if vendor or brand:
            row = {
                TokenSemanticEnum.VENDOR.value: vendor,
                TokenSemanticEnum.BRAND.value: brand,
            }
            rows.append(row)
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

def extract_rows_product_type(documents):
    rows = []

    for doc in documents:
        meta = doc.get("meta_info", {})
        if not isinstance(meta, dict):
            meta = {}

        vendor = doc.get("vendor") or meta.get("vendor")
        tokens: list = meta.get("whole_tokens", doc.get("whole_tokens", []))
        types = meta.get("types", doc.get("types", []))

        brand = []
        if "brand" in types:
            pos = 0
            for type in types:
                if type == "brand":
                    brand.append(tokens[pos])
                pos = pos + 1

        series = []
        if "series" in types:
            pos = 0
            for type in types:
                if type == "series":
                    series.append(tokens[pos])
                pos = pos + 1
        found = False
        sub_series = []
        if "sub_series" in types or "series_and_sub_series" in types:
            pos = 0
            for type in types:
                if type in ["sub_series", "series_and_sub_series"]:
                    sub_series.append(tokens[pos])

                    #if "S7-1500" == tokens[pos]:
                        #found = False
                        #print("S7-1500      <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                        #print(vendor, brand, series)
                pos = pos + 1

        annotations = meta.get("annotations", doc.get("annotations", {}))
        annotation_pos = 0
        uniques = []
        for annotations_token in annotations:
            if "unique" in annotations_token:
                uniques.append(tokens[annotation_pos])
            annotation_pos += 1

        if len(sub_series) == 1 and sub_series[0] == '':
            continue

        if vendor is not None and brand is not None and series is not None:
            """
            {'Vendor': 'Siemens', 'Brand': ['SIPLUS'], 'Subseries': ['S7-1500'], 'Series': [], 'Unique': ['6AG1511-1FK00-2AB0']}
            """
            row = {
                TokenSemanticEnum.VENDOR.value: vendor,
                TokenSemanticEnum.BRAND.value: brand,
                TokenSemanticEnum.SERIES.value: series,
                TokenSemanticEnum.SUBSERIES.value: sub_series,
                TokenSemanticEnum.UNIQUE.value: uniques
            }
            rows.append(row)
            if found:
                print(row)
    return rows


def group_and_count(rows):
    df = pd.DataFrame(rows)
    return df
