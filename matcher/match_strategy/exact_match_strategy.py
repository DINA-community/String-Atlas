from matcher.lib.lookup_client import direct_lookup
from matcher.match_strategy.common import _filter_entities
from matcher.match_strategy.match_strategy import MatchStrategy
from matcher.token_matcher_decision import TokenMatchReason


class ExactMatchStrategy(MatchStrategy):
    def __init__(self):
        super().__init__(name="exact_match_strategy")
        self.match_reason: TokenMatchReason = TokenMatchReason.DIRECT_LOOKUP

    def match(self, token, prefix_token, entity_filter, threshold=None):
        entities = direct_lookup(token, prefix_token=prefix_token)
        return _filter_entities(entities=entities, entity_filter=entity_filter)
