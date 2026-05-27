from qdrant_client.conversions.common_types import ScoredPoint
from matcher.lib.lookup_client import TokenMarker
from matcher.lib.token_enum import TokenSemanticEnum


def _filter_entities(entities, entity_filter: list[dict[str,str]]=[]) -> list[dict[str,str]]:
    if entities is None:
        return []
    entity_filtered = []

    for entity_item in entities:
        if isinstance(entity_item, ScoredPoint):
            entity_item = entity_item.payload

        excluded = False
        for filter_item in entity_filter:
            for key in filter_item.keys():
                if key == TokenMarker.BRAND:
                    key_s = TokenSemanticEnum.BRAND_ID.value
                elif key == TokenMarker.VENDOR:
                    key_s = TokenSemanticEnum.VENDOR_ID.value
                else:
                    key_s = None

                if key_s is None or not isinstance(entity_item, dict) or key_s not in entity_item:
                    continue

                if isinstance(entity_item[key_s], list):
                    compare_from = entity_item[key_s][0]
                else:
                    compare_from = entity_item[key_s]

                if isinstance(filter_item[key], tuple):
                    compare_to = filter_item[key][0]
                else:
                    compare_to = filter_item[key]

                if compare_from != compare_to:
                    excluded = True
                    break
        if not excluded:
            entity_filtered.append(entity_item)
    return entity_filtered

