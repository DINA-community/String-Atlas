import json
from enum import Enum

from qdrant_client.http.models import ScoredPoint

from matcher.initialise.clients import redis_client, qdrant_client
import logging
from matcher.lib.lookup_table import normalized_product_token_plus_vendor_key, normalized_index_token_key, \
    PREFIX_TOKEN_PRODUCT, normalized_vendor_entity_key, PREFIX_TOKEN_BRAND
from matcher.initialise.model_provider import get_sentenance_model
from matcher.lib.token_enum import TokenSemanticEnum
from qdrant_client.models import Filter, FieldCondition, MatchValue

logging.getLogger("qdrant").setLevel(logging.ERROR)
from transformers import logging
logging.set_verbosity_error()

class TokenMarker(Enum):
    VENDOR = 1
    DEVICE_MAC = 2
    VENDOR_OUI = 3
    LEGAL_FORM = 11
    BRAND = 4
    PRODUCT_FAMILY = 5
    PRODUCT_SUB_SERIES = 6
    PRODUCT_TYPE = 7
    FEATURE = 0
    PLACEHOLDER_FEATURE = -1
    PLACEHOLDER_PHYSICAL_UNIT = -2
    PLACEHOLDER_PHYSICAL_VALUE = -3
    DEVICE_TYP = -4
    UNIQUE_FEATURE = 8
    UNIQUE = 9
    PLACEHOLDER = -9
    UNCERTAIN = -10


def direct_lookup(token, prefix_token) -> list[dict[str,str]]|None:
    normalized_token = normalized_index_token_key(token)
    key_token_entity = f"{prefix_token}:{normalized_token}"

    result = redis_client.get(key_token_entity)
    if result:
        response = []
        entities_keys = json.loads(result)
        for entity_key in entities_keys:
            entity = json.loads(redis_client.get(entity_key))
            entity["id"] = entity_key
            if isinstance(entity["normalized"], list):
                entity["count"] = len(entity["normalized"])
            else:
                entity["count"] = len(entity["normalized"].split())
            entity["score"] = 100.00
            response.append(entity)
        return response
    return None

def lookup_similar(token, prefix_token, threshold:float, entity_filter=None) -> list[dict[str,str]]|None:
    from rapidfuzz import process
    from rapidfuzz import fuzz

    search_key_prefix = f"{prefix_token}:"
    restricted_product_search = False
    if prefix_token == PREFIX_TOKEN_PRODUCT:
        if entity_filter:
            for item in entity_filter:
                if TokenMarker.VENDOR in item:
                    vendor = item[TokenMarker.VENDOR]
                    if isinstance(vendor[3], dict):
                        normalized = vendor[3]["normalized"]
                        if isinstance(normalized, list):
                            normalized = normalized[0]
                        vendor_normalized = normalized
                    else:
                        vendor_normalized = vendor[3][0][0]
                    search_key_prefix = normalized_product_token_plus_vendor_key(
                        vendor=vendor_normalized, product_subseries_token=""
                    )
                    restricted_product_search = True

    normalized_token = normalized_index_token_key(token)
    keys = list(redis_client.scan_iter(match=search_key_prefix + "*", count=1000))
    keys = [key.decode("utf-8") if isinstance(key, bytes) else key for key in keys]

    if len(keys) == 0:
        return None

    compare = normalized_token
    if restricted_product_search:
        keys_compare = [key.rsplit("__", 1)[-1] for key in keys]
    else:
        keys_compare = [key.rsplit(":", 1)[-1] for key in keys]

    token_key_extracted = process.extractOne(query=compare, choices=keys_compare, scorer=fuzz.ratio)
    if token_key_extracted:
        # L_T_PRODUCT:siemens__s7xa1500 ('siemens__s7xa1500', 64.0, 0)

        token_key = keys[token_key_extracted[2]]
        score = token_key_extracted[1]
        # score is from 0.00 till 100.00
        if score < float(threshold * 100):
            return None

        try:
            entities_keys = json.loads(redis_client.get(token_key))
        except TypeError:
            print(keys_compare, token_key, token_key_extracted)
            print("JSON Token Key---------------------------------------------------")


        response = []
        for entity_id in entities_keys:
            entity = json.loads(redis_client.get(entity_id))
            entity["id"] = entity_id
            if isinstance(entity["normalized"], list):
                entity["count"] = len(entity["normalized"])
            else:
                entity["count"] = len(entity["normalized"].split())
            entity["score"] = float(score)
            response.append(entity)
        return response
    return None


def lookup_similiar_qadrant(token, prefix_token:str, threshold:float, entity_filter=None):

    must = []
    if prefix_token == PREFIX_TOKEN_PRODUCT or prefix_token == PREFIX_TOKEN_BRAND:
        if entity_filter:
            for item in entity_filter:
                if TokenMarker.VENDOR in item:
                    vendor_entity_tuple = item[TokenMarker.VENDOR]
                    must.append(FieldCondition(
                        key=TokenSemanticEnum.VENDOR_ID.value,
                        match=MatchValue(value=vendor_entity_tuple[0])
                    ))
                if TokenMarker.BRAND in item:
                    print("----------------------------- brand")
                    brand = item[TokenMarker.BRAND]
                    brand_enitty_id = brand[0]
                    must.append(FieldCondition(
                        key=TokenSemanticEnum.BRAND_ID.value,
                        match=MatchValue(value=brand_enitty_id)
                    ))


                    print(brand)
    # ({'vendor': 'EuroTel', 'brand': 'ETL3100', 'series': '', 'subseries': '', 'vendor_id': 'L_E_VENDOR:eurotel', 'brand_id': 'L_E_BRAND:etl3100', 'normalized': '', 'id': 254, 'count': 0, 'score': 0.6241014}, <TokenMatchReason.VECTOR_LOOKUP: 3>, <TokenMarker.PRODUCT_SUB_SERIES: 6>)]

    query_filter = Filter(must=must)


    model = get_sentenance_model()

    collection_name = prefix_token.lstrip("L_E_").lstrip("L_T_").lower()

    results: list[ScoredPoint] = qdrant_client.search(
        collection_name=collection_name,
        query_vector=model.encode(token),
        limit=10,
        query_filter=query_filter
    )
    responses = []
    for result in results:
        # "result.score" is in range from 0.000... till 1.0
        if result.score < threshold:
            continue

        entity = {}
        for key, value in result.payload.items():
            entity[key] = value
        entity["id"] = result.id
        if isinstance(entity["normalized"], list):
            entity["count"] = len(entity["normalized"])
        else:
            entity["count"] = len(entity["normalized"].split())
        entity["score"] = float(result.score)
        responses.append(entity)
    if len(responses) == 0:
        return None
    return responses
