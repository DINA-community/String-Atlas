from matcher.lib.lookup_client import lookup_similiar_qadrant
from matcher.match_strategy.match_strategy import MatchStrategy
from matcher.token_matcher_decision import TokenMatchReason


class VectorMatchStrategy(MatchStrategy):

    def __init__(self):
        super().__init__(name="vector_match_strategy")
        self.match_reason: TokenMatchReason = TokenMatchReason.VECTOR_LOOKUP

    def match(self, token, prefix_token, entity_filter, threshold=None):
        return lookup_similiar_qadrant(token, prefix_token=prefix_token, threshold=threshold, entity_filter=entity_filter)
