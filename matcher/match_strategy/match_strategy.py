from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matcher.token_matcher_decision import TokenMatchReason


class MatchStrategy(ABC):

    def __init__(self, name):
        self.match_reason: TokenMatchReason | None = None
        self.name = name
        self.result_overwriting = None
        self.run_once = False
        self.decision_reason = None

    def get_name(self):
        return self.name

    @abstractmethod
    def match(self, token, prefix_token, entity_filter, threshold=None):
        pass

    def get_match_reason(self) -> TokenMatchReason | None:
        return self.match_reason

    def runs_only_onces(self) -> bool:
        return self.run_once

    def get_decision_reason(self):
        return self.decision_reason

