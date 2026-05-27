from matcher.lib.lookup_client import lookup_similar
from matcher.match_strategy.common import _filter_entities
from matcher.match_strategy.match_strategy import MatchStrategy
from matcher.token_matcher_decision import TokenMatchReason


class FuzzyMatchStrategy(MatchStrategy):
    def __init__(self):
        super().__init__(name="fuzzy_match_strategy")
        self.match_reason: TokenMatchReason = TokenMatchReason.SIMILAR_LOOKUP

    def match(self, token, prefix_token, entity_filter, threshold=None):
        entities = lookup_similar(token, prefix_token=prefix_token, threshold=threshold,entity_filter=entity_filter)
        return _filter_entities(entities=entities, entity_filter=entity_filter)
