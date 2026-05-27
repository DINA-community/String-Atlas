import re
import pandas as pd
from .matcher import Matcher


class RegexMatcher(Matcher):
    pattern = None

    def __init__(self, params, field_name, weight):
        super().__init__(params=params, field_name=field_name, weight=weight)
        self.pattern = re.compile(self.params['pattern'])

    def match_column_from_document(self, records: pd.DataFrame):
        #hits = {}
        #columns = df.values
        #for column in columns:
        # TODO implement
        hits = {}
        return MatchHelper.normalize_hits_scores(hits)


    def match_value(self, value):
        if self.pattern.fullmatch(value):
            return True
        else:
            return False
