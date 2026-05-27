import pandas as pd
from normalizer.database.redis_client_helper import get_all_keys, load_documents, extract_rows_vendor_and_brand, \
    group_and_count, extract_rows_product_type
from normalizer.initialise.csaf_dataframe import df_filtered
from normalizer.initialise.csaf_dataframe import find_by_tokens
from matcher.initialise.model_provider import get_sentenance_model
from matcher.lib.keywords_loader import load_keyword_config
from matcher.lib.lookup_table import normalized_vendor_entity_key, normalized_brand_entity_key
from matcher.lib.token_enum import TokenSemanticEnum
from matcher.initialise.clients import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct


def create_collections(word_of_bags, payload_keys: list[str], normalized_fields: list[str]):
    for prefix in word_of_bags.keys():

        df = word_of_bags[prefix].reset_index(drop=True)

        texts = (
            df[prefix]
            .fillna("")
            .astype(str)
            .tolist()
        )
        vectors = model.encode(texts)
        collection_name = prefix.lower()
        if qdrant_client.collection_exists(collection_name):
            qdrant_client.delete_collection(collection_name)
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE, on_disk=False),
        )

        points = []
        payload_information = word_of_bags[prefix]
        for i in range(len(vectors)):
            payload = {
                key.lower(): df.iloc[i][key]
                for key in payload_keys
            }

            vendor = None
            brand = None
            if TokenSemanticEnum.VENDOR.value in payload_keys:
                vendor = normalized_vendor_entity_key(payload[TokenSemanticEnum.VENDOR.value])
                payload[TokenSemanticEnum.VENDOR_ID.value] = vendor
            if TokenSemanticEnum.BRAND.value in payload_keys:
                brand = normalized_brand_entity_key(payload[TokenSemanticEnum.BRAND.value])
                payload[TokenSemanticEnum.BRAND_ID.value]  = brand

            normalized = [payload_information.iloc[i][x].strip() for x in normalized_fields if
                 payload_information.iloc[i][x].strip() != ""]

            payload[TokenSemanticEnum.NORMALIZED.value] = " ".join(normalized)
            # TODO refactor magic string
            if collection_name == "product":
                payload[TokenSemanticEnum.CSAF_REF.value] = find_by_tokens(df_all=df_filtered, vendor=vendor,
                                                                 words=[brand] + normalized)

            p_struct = PointStruct(
                id=i,
                vector=vectors[i],
                payload=payload
            )
            points.append(p_struct)

        batch_size = 1000
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            qdrant_client.upsert(
                collection_name=collection_name,
                points=batch
            )

print("Qdrant - Vendors - Start")

# embedding Modell
model = get_sentenance_model()

# TODO refactor magic string
keys_vendor_and_brand = get_all_keys("vendor__*")
documents_vendor_and_brand = load_documents(keys_vendor_and_brand)
rows_vendor_and_brand = extract_rows_vendor_and_brand(documents_vendor_and_brand)
grouped_vendor_and_brand = group_and_count(rows_vendor_and_brand)


# vendor and brands
grouped_vendor_and_brand[TokenSemanticEnum.VENDOR.value] = grouped_vendor_and_brand[TokenSemanticEnum.VENDOR.value].apply(
        lambda x: " ".join(map(str, x)) if isinstance(x, list)
        else "" if pd.isna(x)
        else str(x)
    )
grouped_vendor_and_brand[TokenSemanticEnum.BRAND.value] = grouped_vendor_and_brand[TokenSemanticEnum.BRAND.value].apply(
        lambda x: " ".join(map(str, x)) if isinstance(x, list)
        else "" if pd.isna(x)
        else str(x)
    )

word_of_bags = {TokenSemanticEnum.VENDOR.value: grouped_vendor_and_brand}
create_collections(word_of_bags=word_of_bags, payload_keys=[TokenSemanticEnum.VENDOR.value],
                   normalized_fields=[TokenSemanticEnum.VENDOR.value])

word_of_bags = {TokenSemanticEnum.BRAND.value: grouped_vendor_and_brand}
create_collections(word_of_bags=word_of_bags, payload_keys=[TokenSemanticEnum.VENDOR.value, TokenSemanticEnum.BRAND.value],
                   normalized_fields=[TokenSemanticEnum.BRAND.value])

print("Qdrant - Vendors - Done")


print("Qdrant - Product Types - Start")

# Product types
# TODO refactor magic string
keys_product_type = get_all_keys("*product__type*")
documents_product_type = load_documents(keys_product_type)
rows_product_type = extract_rows_product_type(documents_product_type)
grouped_product_type = group_and_count(rows_product_type)

required_product_columns = [
    TokenSemanticEnum.VENDOR.value,
    TokenSemanticEnum.BRAND.value,
    TokenSemanticEnum.SERIES.value,
    TokenSemanticEnum.SUBSERIES.value,
]
if not grouped_product_type.empty and set(required_product_columns).issubset(grouped_product_type.columns):
    grouped_product_type[TokenSemanticEnum.VENDOR.value] = grouped_product_type[TokenSemanticEnum.VENDOR.value].apply(
        lambda x: " ".join(x) if isinstance(x, list) else str(x)
    )

    grouped_product_type[TokenSemanticEnum.BRAND.value] = grouped_product_type[TokenSemanticEnum.BRAND.value].apply(
        lambda x: " ".join(x) if isinstance(x, list) else str(x)
    )

    grouped_product_type[TokenSemanticEnum.SERIES.value] = grouped_product_type[TokenSemanticEnum.SERIES.value].apply(
        lambda x: " ".join(x) if isinstance(x, list) else str(x)
    )
    grouped_product_type[TokenSemanticEnum.SUBSERIES.value] = grouped_product_type[TokenSemanticEnum.SUBSERIES.value].apply(
        lambda x: " ".join(x) if isinstance(x, list) else str(x)
    )

    grouped_product_type["Product"] = (grouped_product_type[TokenSemanticEnum.BRAND.value] + " " +
                                       grouped_product_type[TokenSemanticEnum.SERIES.value] + " " + grouped_product_type[TokenSemanticEnum.SUBSERIES.value])

    word_of_bags = {"Product": grouped_product_type }
    create_collections(word_of_bags=word_of_bags, payload_keys=[TokenSemanticEnum.VENDOR.value, TokenSemanticEnum.BRAND.value,
                                                                TokenSemanticEnum.SERIES.value, TokenSemanticEnum.SUBSERIES.value], normalized_fields=
                       [TokenSemanticEnum.SERIES.value, TokenSemanticEnum.SUBSERIES.value])

print("Qdrant - Product Types - Done")


print("Qdrant - Placeholders - Start")

keywords = load_keyword_config()
placeholder_keywords = keywords["placeholder_keywords"]
version_placeholder_keywords = keywords["version_placeholder_keywords"]
function_keywords = keywords["function_keywords"]

# TODO refactor magic string
collection_name = "placeholder"
texts = function_keywords + version_placeholder_keywords + placeholder_keywords
vectors = model.encode(texts)
if qdrant_client.collection_exists(collection_name):
    qdrant_client.delete_collection(collection_name)
qdrant_client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE, on_disk=False),
)
points = []
for i in range(len(vectors)):
    payload = {
        # TODO refactor magic string
        "Entity": "PLACEHOLDER",
        TokenSemanticEnum.NORMALIZED.value: texts[i]
    }
    p_struct = PointStruct(
        id=i,
        vector=vectors[i],
        payload=payload
    )
    points.append(p_struct)

batch_size = 1000
for i in range(0, len(points), batch_size):
    batch = points[i:i + batch_size]
    qdrant_client.upsert(
        collection_name=collection_name,
        points=batch
    )
print("Qdrant - Placeholders - Done")
