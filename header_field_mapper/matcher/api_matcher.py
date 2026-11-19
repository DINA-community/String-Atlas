import json

from normalizer.semantics.semantics import Semantics
from string_miner.string_miner_helper import StringMinerHelper
from api_client.string_atlas_client import StringAtlasAPIClient
from .match_helper import MatchHelper
from .matcher import Matcher

# TODO not used
class ApiMatcher(Matcher):
    word_of_bags = None
    word_of_bags_extended = None
    api_client: StringAtlasAPIClient = None

    def __init__(self, params, field_name, weight, api_client: StringAtlasAPIClient):
        super().__init__(params=params, field_name=field_name, weight=weight)
        self.api_client = api_client


    @staticmethod
    def match_colum_from_document(df):
        print("runs")
        matching_rules = {}
        df_copy = df.copy()
        print(df_copy.head(1))
        use_all_records = 'data_use_all' in self.params and self.params['data_use_all'] == 'True'
        if use_all_records:
            limit = self.params['data_limit']
            is_column_found = True
            while is_column_found:
                column_found, column_type = self._exclude_columns(df_copy, limit)
                if column_found is None:
                    is_column_found = False
                else:
                    matching_rules[column_type] = column_found
                    df_copy.drop(columns=column_found, inplace=True)
        print(matching_rules)
        import sys
        sys.exit()
        hits = {}
        columns = df.columns
        for column in columns:
            columns_extended = StringMinerHelper.remove_special_characters_from_word_of_bags([column])
            columns_extended = StringMinerHelper.generate_word_of_bags_variants(columns_extended)
            common_words = list(set(columns_extended) & set(self.word_of_bags))
            hits[column] = len(common_words) * self.weight * 2
            common_words_extended = list(set(columns_extended) & set(self.word_of_bags))
            hits[column] = hits[column] + (len(common_words_extended) * self.weight)
        return MatchHelper.normalize_hits_scores(hits)
