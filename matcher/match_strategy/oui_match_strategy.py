import re

from matcher.lib.lookup_client import TokenMarker
from matcher.lib.lookup_table import redis_get_json
from matcher.lib.token_enum import TokenSemanticEnum
from matcher.match_strategy.match_strategy import MatchStrategy
from matcher.token_matcher_decision import TokenMatchReason, DecisionReason


class OUIMatchStrategy(MatchStrategy):
    def __init__(self):
        super().__init__(name="oui_match_strategy")
        self.match_reason: TokenMatchReason = TokenMatchReason.MARKER_OVERWRITTEN
        self.result_overwriting = TokenMarker.VENDOR
        self.run_once = True
        self.decision_reason = DecisionReason.UNIQUE

    def match(self, token, prefix_token, entity_filter, threshold=None):
        OUI_REGEX = re.compile(
            r"([0-9A-Fa-f]{2}[^A-Za-z0-9]+){2}[0-9A-Fa-f]{2}"
        )
        match = OUI_REGEX.search(token)
        response = []
        print("YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYEEEES")
        print(token)
        print(match)
        if match:
            oui = "oui__"+re.sub(r"[^A-Fa-f0-9]", "-", match.group()).upper()
            oui_entity = redis_get_json(oui, source_is_json=True)
            if oui_entity and TokenSemanticEnum.VENDOR_ID.value in oui_entity:
                vendor_entity_id = oui_entity[TokenSemanticEnum.VENDOR_ID.value]
                if vendor_entity_id:
                    entity = redis_get_json(vendor_entity_id)
                    entity["id"] = vendor_entity_id
                    if isinstance(entity["normalized"], list):
                        entity["count"] = len(entity["normalized"])
                    else:
                        entity["count"] = len(entity["normalized"].split())
                    entity["score"] = 100.00
                    response.append(entity)
        return response
