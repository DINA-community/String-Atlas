import json
from string_miner.string_miner_helper import StringMinerHelper
from .match_helper import MatchHelper
from .matcher import Matcher
import pandas as pd
from pandas import DataFrame as df


class WordOfBagMatcher(Matcher):
    word_of_bags: list = None
    word_of_bags_extended: list = None

    def __init__(self, params, field_name, weight):
        super().__init__(params=params, field_name=field_name, weight=weight)
        if params["source"]["source_type"] == 'file':
            with open(params["source"]["source_path"], "r") as source_file:
                word_of_bag_file = json.load(source_file)
                self.word_of_bags = word_of_bag_file[params["source"]['json_field']]
        self.word_of_bags = StringMinerHelper.remove_special_characters_from_word_of_bags(self.word_of_bags)
        self.word_of_bags_extended = StringMinerHelper.generate_word_of_bags_variants(self.word_of_bags)

    def match_column_from_document(self, records: pd.DataFrame):
        hits = {}
        columns = df.columns
        for column in columns:
            columns_extended = StringMinerHelper.remove_special_characters_from_word_of_bags([column])
            columns_extended.extend(StringMinerHelper.generate_word_of_bags_variants(columns_extended))
            common_words = list(set(columns_extended) & set(self.word_of_bags))
            hits[column] = len(common_words) * self.weight * 2
            common_words_extended = list(set(columns_extended) & set(self.word_of_bags))
            hits[column] = hits[column] + (len(common_words_extended) * self.weight)
        return MatchHelper.normalize_hits_scores(hits)
