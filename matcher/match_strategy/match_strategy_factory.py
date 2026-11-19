from matcher.match_strategy.match_strategy import MatchStrategy
from matcher.match_strategy.exact_match_strategy import ExactMatchStrategy
from matcher.match_strategy.fuzzy_match_strategy import FuzzyMatchStrategy
from matcher.match_strategy.oui_match_strategy import OUIMatchStrategy
from matcher.match_strategy.vector_match_strategy import VectorMatchStrategy

class MatchStrategyFactory:
    def __init__(self):
        self.instances = {
            "exact_match_strategy": ExactMatchStrategy(),
            "fuzzy_match_strategy": FuzzyMatchStrategy(),
            "vector_match_strategy": VectorMatchStrategy(),
            "oui_match_strategy": OUIMatchStrategy()
        }

    def get_strategies_by_names(self, searched:list[str]) -> list[MatchStrategy]:
        return [
            strategy
            for key, strategy in self.instances.items()
            if key in searched
        ]

    def get_all_strategies(self) -> list[MatchStrategy]:
        return list(self.instances.values())
