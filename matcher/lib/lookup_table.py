import re
import json
from normalizer.initialise.csaf_dataframe import df_filtered, find_by_tokens
from matcher.initialise.clients import redis_client, qdrant_client
from matcher.lib.keywords_loader import load_keyword_config
from matcher.lib.token_enum import TokenSemanticEnum
from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector

PREFIX_TOKEN_UNIQUE = "L_T_UNIQUE"
PREFIX_TOKEN_VENDOR = "L_T_VENDOR"
PREFIX_TOKEN_BRAND = "L_T_BRAND"
PREFIX_TOKEN_PRODUCT = "L_T_PRODUCT"
PREFIX_ENTITY_PRODUCT = "L_E_PRODUCT"
PREFIX_ENTITY_VENDOR = "L_E_VENDOR"
PREFIX_ENTITY_BRAND = "L_E_BRAND"
PREFIX_TOKEN_PRODUCT_PLUS_VENDOR = "L_T_PRODUCT_V"
PREFIX_ENTITY_PLACEHOLDER = "L_E_PLACEHOLDER"
PREFIX_TOKEN_PLACEHOLDER = "L_T_PLACEHOLDER"


def normalized_index_token_key(token):#
    CHAR_MAP = {
        "-": "xa",
        "!": "xb",
        ",": "xc",
        ";": "xd",
        ".": "xe",
        "ö": "xoe",
        "ü": "xue",
        "ä": "xae",
    }

    """ to avoid wrong duplicate index keys """
    token = token.strip()
    token = token.strip(",")
    token = token.strip(";")
    token = token.strip(".")
    token = token.lower()

    def repl(match):
        ch = match.group(0)
        return CHAR_MAP.get(ch, "x")

    return re.sub(r"[^a-zA-Z0-9]", repl, token)


def normalized_index(entity):
    if not isinstance(entity, str):
        return None
    tokens = entity.split()
    normalized_tokens = []
    for token in tokens:
        token = normalized_index_token_key(token)
        normalized_tokens.append(token)
    return "_".join(normalized_tokens)

def normalized_product_token_key(product_subseries_token):
    key_product_subseries_token = normalized_index_token_key(product_subseries_token)
    return PREFIX_TOKEN_PRODUCT+":"+ key_product_subseries_token

def normalized_product_entity_key(vendor, product_subseries_token):
    key_vendor = normalized_index_token_key(vendor)
    key_product_subseries_token = normalized_index_token_key(product_subseries_token)
    return PREFIX_ENTITY_PRODUCT+":"+key_vendor + "__" + key_product_subseries_token

def normalized_vendor_entity_key(vendor):
    key_vendor = normalized_index_token_key(vendor)
    return PREFIX_ENTITY_VENDOR+":"+key_vendor

def normalized_brand_entity_key(brand):
    key_vendor = normalized_index_token_key(brand)
    return PREFIX_ENTITY_BRAND+":"+key_vendor

def normalized_unique_token_key(unique):
    key_unique = normalized_index_token_key(unique)
    return PREFIX_TOKEN_UNIQUE+":"+key_unique

def normalized_product_token_plus_vendor_key(vendor, product_subseries_token):
    key_vendor = normalized_index_token_key(vendor)
    key_product_subseries_token = normalized_index_token_key(product_subseries_token)
    return PREFIX_TOKEN_PRODUCT_PLUS_VENDOR+":"+key_vendor+":"+key_vendor + "__" + key_product_subseries_token

def create_vendor_and_brand_lookup_tables(df):
    """
    create lookup tables for vendors and brands
    """
    prefixes_tokens = [PREFIX_TOKEN_VENDOR, PREFIX_TOKEN_BRAND]
    prefixes_entities = [PREFIX_ENTITY_VENDOR, PREFIX_ENTITY_BRAND]
    df_columns = [TokenSemanticEnum.VENDOR.value, TokenSemanticEnum.BRAND.value]

    oui_keys_filled = set()

    if df.empty or not set(df_columns).issubset(df.columns):
        return

    for i in range(len(prefixes_tokens)):
        entities = df[df_columns[i]].unique()

        brand_token_index = {}
        brand_entity_index = {}
        prefix_token = prefixes_tokens[i]
        prefix_entity = prefixes_entities[i]

        is_vendor = df_columns[i] == TokenSemanticEnum.VENDOR.value

        for entity in entities:

            if isinstance(entity, float):
                continue

            entity_tokens = entity.split()
            if is_vendor:
                key_entity = normalized_vendor_entity_key(entity)

                for redis_key in _iter_redis_keys("oui__*"):
                    if redis_key in oui_keys_filled:
                        continue
                    oui = redis_get_json(redis_key, source_is_json=True)
                    if oui is not None and TokenSemanticEnum.TEXTMINER_VENDOR_NORMALIZED.value in oui \
                        and oui[TokenSemanticEnum.TEXTMINER_VENDOR_NORMALIZED.value] == entity:
                        redis_client.json().set(redis_key, TokenSemanticEnum.VENDOR_ID.value, key_entity)
            else:
                key_entity = normalized_brand_entity_key(entity)

            if key_entity not in brand_entity_index:
                brand_entity_index[key_entity] = True
                key_entity_selected = key_entity
            else:
                count = 1
                key_entity_selected = key_entity + count*"x"
                while  key_entity_selected in brand_entity_index:
                    count = count + 1
                    brand_entity_index[key_entity_selected] = True
                    key_entity_selected = key_entity + count * "x"
                brand_entity_index[key_entity_selected] = True


            if is_vendor:
                manufacturers_entity_id = normalized_vendor_entity_key(entity)
                manufacturers_entity = entity
            else:
                manufacturers = df[df[TokenSemanticEnum.BRAND.value] == entity][TokenSemanticEnum.VENDOR.value].unique()
                manufacturers_entity_id = normalized_vendor_entity_key(next(iter(manufacturers)))
                manufacturers_entity = next(iter(manufacturers))

            payload = {TokenSemanticEnum.NORMALIZED.value: entity_tokens,
           TokenSemanticEnum.VENDOR.value: manufacturers_entity, TokenSemanticEnum.VENDOR_ID.value: manufacturers_entity_id}

            if not is_vendor:
                payload[TokenSemanticEnum.BRAND_ID.value] = key_entity_selected

            redis_client.set(key_entity_selected, json.dumps(payload))

            for token in entity_tokens:
                token_normalized = normalized_index_token_key(token)
                key_token = f"{prefix_token}:{token_normalized}"

                if key_token not in brand_token_index:
                    brand_token_index[key_token] = []

                brand_token_index[key_token].append(key_entity_selected)


        for key_token, brand_entities in brand_token_index.items():
            redis_client.set(key_token, json.dumps(brand_entities))


def create_product_lookup_tables(df):
    """
    create lookup tables for product types
    """
    brands_safety = {}

    unique_token_index: dict[str, list[str]] = {}
    product_entity_index: dict[str, bool] = {}
    token_entity_index: dict[str, list[str]] = {}
    token_entity_index_plus_vendor: dict[str, list[str]] = {}
    subseries = df[TokenSemanticEnum.SUBSERIES.value].explode().unique().tolist()
    for subserie in subseries:

        # handle before, supposed not to land in this column
        if isinstance(subserie, float):
            continue

        tmp = df.explode(TokenSemanticEnum.SUBSERIES.value)
        vendor = tmp[tmp[TokenSemanticEnum.SUBSERIES.value] == subserie][TokenSemanticEnum.VENDOR.value].unique().tolist()

        if isinstance(vendor, list):
            vendor = vendor[0]
        series = (
            tmp[tmp[TokenSemanticEnum.SUBSERIES.value] == subserie][TokenSemanticEnum.SERIES.value]
            .explode()
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda x: x != ""]
            .unique()
            .tolist()
        )

        brands = tmp[tmp[TokenSemanticEnum.SUBSERIES.value] == subserie][TokenSemanticEnum.BRAND.value].tolist()
        uniques = tmp[tmp[TokenSemanticEnum.SUBSERIES.value] == subserie][TokenSemanticEnum.UNIQUE.value].tolist()

        for brand in brands:
            if not isinstance(brand, list):
                continue
            brand_entity_id = normalized_brand_entity_key(" ".join(brand))

            product_key = " ".join(series + [subserie])
            norm_product_entity_key = normalized_product_entity_key(vendor, product_key)

            for unique in uniques:
                if len(unique) > 0 and isinstance(unique[0], str):
                    unique = unique[0]
                    key_token_unique = normalized_unique_token_key(unique)
                    unique_token_index[key_token_unique] = [norm_product_entity_key]

            if norm_product_entity_key not in product_entity_index:
                product_entity_index[norm_product_entity_key] = True

                normalized = []
                if len(series) > 0:
                    normalized = normalized + series
                if len(subserie) > 0:
                    normalized = normalized + [subserie]

                row = {TokenSemanticEnum.BRAND_ID.value: brand_entity_id,
                       TokenSemanticEnum.VENDOR_ID.value: normalized_vendor_entity_key(vendor),
                       TokenSemanticEnum.BRAND.value: " ".join(brand),
                       TokenSemanticEnum.VENDOR.value: vendor,
                       TokenSemanticEnum.SERIES.value: " ".join(series),
                       TokenSemanticEnum.SUBSERIES.value: subserie,
                       TokenSemanticEnum.NORMALIZED.value: " ".join(normalized),
                       TokenSemanticEnum.CSAF_REF.value: find_by_tokens(df_all=df_filtered, vendor=vendor,
                                                                  words=brand + normalized)
                       }
                redis_client.set(norm_product_entity_key, json.dumps(row))

                if brand_entity_id not in brands_safety:
                    brands_safety[brand_entity_id] = 1
                else:
                    brands_safety[brand_entity_id] += 1

            for token in series + [subserie]:

                token = str(token)

                token_normalized = normalized_product_token_key(token)
                if token_normalized not in token_entity_index:
                    token_entity_index[token_normalized] = []
                if norm_product_entity_key not in token_entity_index[token_normalized]:
                    token_entity_index[token_normalized].append(norm_product_entity_key)

                token_normalized_plus_vendor = normalized_product_token_plus_vendor_key(vendor, token)

                if token_normalized_plus_vendor not in token_entity_index_plus_vendor:
                    token_entity_index_plus_vendor[token_normalized_plus_vendor] = []
                token_entity_index_plus_vendor[token_normalized_plus_vendor].append(norm_product_entity_key)

        for key_token, product_entity_list in token_entity_index.items():
            redis_client.set(key_token, json.dumps(product_entity_list))

        for key_token, product_entity_list in token_entity_index_plus_vendor.items():
            redis_client.set(key_token, json.dumps(product_entity_list))

        for key_token, linked_entities in unique_token_index.items():
            redis_client.set(key_token, json.dumps(linked_entities))

    for brand_entity_key,count in brands_safety.items():
        if count > 1:
            try:
                value = redis_get_json(brand_entity_key)
                value[TokenSemanticEnum.MULTIPLE.value] = count
                redis_client.set(brand_entity_key, json.dumps(value))
            except Exception as e:
                print(e)
                print(brand_entity_key+" not found")


def _iter_redis_keys(pattern, batch_size=1000):
    for key in redis_client.scan_iter(match=pattern, count=batch_size):
        if isinstance(key, bytes):
            key = key.decode("utf-8")
        yield key


def _entity_key_suffix(key):
    return key.split(":", 1)[1] if ":" in key else key


def _product_entity_suffix(key):
    suffix = _entity_key_suffix(key)
    return suffix.rsplit("__", 1)[-1]


def redis_get_json(key, source_is_json:bool=False):
    if source_is_json:
        value = redis_client.json().get(key)
    else:
        value = redis_client.get(key)

    if value is None:
        return None

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    if isinstance(value, str):
        return json.loads(value)

    return value

def is_brand_of_product(brand_entity, product_entity):
    if brand_entity[TokenSemanticEnum.VENDOR_ID.value] != product_entity[TokenSemanticEnum.VENDOR_ID.value] \
            or brand_entity[TokenSemanticEnum.BRAND_ID.value] == product_entity[TokenSemanticEnum.BRAND_ID.value]:
        return False
    return True


# TOOD explain in masterwork
def cleanup_brands_and_producttypes_in_lookup_tables(batch_size=1000) -> None:
    brand_keys_by_suffix = {}
    for brand_key in _iter_redis_keys(f"{PREFIX_ENTITY_BRAND}:*", batch_size=batch_size):
        brand_keys_by_suffix.setdefault(_entity_key_suffix(brand_key), []).append(brand_key)

    deleted_brand_keys = set()
    for product_token_key in _iter_redis_keys(f"{PREFIX_TOKEN_PRODUCT}:*", batch_size=batch_size):
        suffix = _product_entity_suffix(product_token_key)

        for brand_key in brand_keys_by_suffix.get(suffix, []):

            refer_to_common_product_entity_key = redis_get_json(product_token_key)
            if refer_to_common_product_entity_key is not None:

                if not isinstance(refer_to_common_product_entity_key, list):
                    refer_to_common_product_entity_key = [refer_to_common_product_entity_key]

                for product_entity_key in refer_to_common_product_entity_key:
                    product_entity = redis_get_json(product_entity_key)

                    if product_entity is None:
                        continue

                    if brand_key in deleted_brand_keys:
                        continue

                    brand_entity = redis_get_json(brand_key)

                    if TokenSemanticEnum.MULTIPLE.value in brand_entity and \
                        brand_entity[TokenSemanticEnum.MULTIPLE.value] > 1:
                        continue

                    if is_brand_of_product(brand_entity, product_entity):
                        # same vendor
                        redis_client.delete(brand_key)
                        print("QuickFix: deleted {}".format(brand_key))

                        qdrant_client.delete(collection_name=TokenSemanticEnum.BRAND.value,
                                             points_selector=FilterSelector(filter=Filter(must=[
                                                 FieldCondition(key=TokenSemanticEnum.VENDOR_ID.value, match=MatchValue(
                                                     value=brand_entity[TokenSemanticEnum.VENDOR_ID.value])),
                                                 FieldCondition(key=TokenSemanticEnum.NORMALIZED.value,
                                                                match=MatchValue(value=" ".join(brand_entity[
                                                                                                    TokenSemanticEnum.NORMALIZED.value])))])))

                        for token in brand_entity[TokenSemanticEnum.NORMALIZED.value]:
                            normalized_token = normalized_index_token_key(token)
                            brand_token_key_delete = f"{PREFIX_TOKEN_BRAND}:{normalized_token}"
                            token_entity = redis_get_json(brand_token_key_delete)
                            if isinstance(token_entity, list):
                                token_entity.remove(brand_key)
                                deleted_brand_keys.add(brand_key)
                                if len(token_entity) > 0:
                                    redis_client.set(brand_token_key_delete, json.dumps(token_entity))
                                    print("QuickFix: shrinked {}".format(brand_token_key_delete))
                                else:
                                    redis_client.delete(brand_token_key_delete)
                                    print("QuickFix: deleted {}".format(brand_token_key_delete))


def create_functional_words_and_placeholders_lookup_tables():

    keywords = load_keyword_config()
    placeholder_keywords = keywords["placeholder_keywords"]
    version_placeholder_keywords = keywords["version_placeholder_keywords"]
    function_keywords = keywords["function_keywords"]

    for function_key_word in function_keywords:
        token_key = f"{PREFIX_TOKEN_PLACEHOLDER}:"+normalized_index_token_key(function_key_word)
        redis_client.set(token_key, json.dumps(["PLACEHOLDER_FUNCTIONAL"]))

    for version_key_word in version_placeholder_keywords:
        token_key = f"{PREFIX_TOKEN_PLACEHOLDER}:" + normalized_index_token_key(version_key_word)
        redis_client.set(token_key, json.dumps(["PLACEHOLDER_VERSION"]))

    for general_key_word in placeholder_keywords:
        token_key = f"{PREFIX_TOKEN_PLACEHOLDER}:" + normalized_index_token_key(general_key_word)
        redis_client.set(token_key, json.dumps(["PLACEHOLDER_VERSION"]))

    for placeholder_entity in ["PLACEHOLDER_FUNCTIONAL", "PLACEHOLDER_VERSION", "PLACEHOLDER_GENERAL"]:
        redis_client.set(placeholder_entity, json.dumps({"id": placeholder_entity, TokenSemanticEnum.NORMALIZED.value: placeholder_entity}))
