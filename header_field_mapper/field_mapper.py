import json
import pandas as pd
from normalizer.semantics.semantics import Semantics
from string_miner.string_miner_helper import StringMinerHelper
from matcher.token_matcher import TokenMatcher
from .matcher.api_matcher import ApiMatcher
from .matcher.ip_matcher import IpMatcher
from .matcher.regex_matcher import RegexMatcher
from .matcher.dict_matcher import DictMatcher
from .matcher.word_of_bag import WordOfBagMatcher
from collections import defaultdict


class FieldMapper:
    RATING_MODE_MAXIMUM = 'maximum'
    RATING_MODE_AVERAGE = 'average'

    field_config: dict = None
    token_matcher: TokenMatcher = None

    def __init__(self, field_config:dict, token_matcher:TokenMatcher):
        self.field_config = field_config
        self.token_matcher = token_matcher

    def _normalize(self, values):
        # TODO truncate empty rows
        return records

    def _unique_winner_average(self, local_matches: []):
        accumulated = defaultdict(int)
        for hit in local_matches:
            for key, value in hit.items():
                accumulated[key] += value
        print(dict(accumulated))
        return self._unique_winner(dict(accumulated))

    def _unique_winner(self, hits: {}):
        # TODO parametrisieren
        threshold = 0.3
        min_value = min(hits.values())
        max_value = max(hits.values())

        max_threshold = max_value - 0.3
        if max_threshold < min_value:
            return None

        count = 0
        max_hit = None
        for column, value in hits.items():
            if value == max_value:
                count += 1
                max_hit = column
            elif value >= max_threshold:
                count += 1
        if count == 1:
            return max_hit
        return None

    def mapping_conventional(self, columns:[], values:[]) -> (dict, list):
        """
        matching: dict
        columns_left: []
        """
        values = self.normalise(values)
        df_document = pd.DataFrame(data=values, columns=columns)

        matching = {}
        for field_name, field_config in self.field_config['fields'].items():
            column_name = field_config['name']
            if column_name in matching:
                continue

            if len(field_config['scoring']) > 1:
                local_matches = []
                rate_mode = field_config['score_rating']
                winner = None
                for score_match_item in field_config['scoring']:
                    if winner is None or rate_mode == 'average':
                        winner, hits = self._run_matcher(score_match_item, column_name, score_match_item['score_weight'],
                                                         df_document)
                        if winner is not None and rate_mode != 'average':
                            matching[column_name] = winner
                            df_document.drop(columns=winner, inplace=True)
                        elif hits is not None:
                            local_matches.append(hits)
                if rate_mode == 'average' and len(local_matches) > 0:
                    winner = self._unique_winner_average(local_matches)
                    if winner is not None:
                        matching[column_name] = winner
                        df_document.drop(columns=winner, inplace=True)
            else:
                for score_match_item in field_config['scoring']:
                    winner, hits = self._run_matcher(score_match_item, column_name, 1.0, df_document)
                    if winner is not None:
                        matching[column_name] = winner
                        df_document.drop(columns=winner, inplace=True)
        return matching, df_document.columns.tolist()

    def mapping_with_miner(self, columns: list, values: list):
        columns_to_find = Semantics.COLUMNS_TO_FIND
        df_document = pd.DataFrame(data=values, columns=columns)
        df_document_copy = df_document.copy()
        # first try to catch everything possible with regex without mining
        matching, document_columns_left = self.mapping_conventional(columns, values)
        columns_to_find = list(set(columns_to_find) - set(matching.keys()))

        # matching => { match, value, normalized }

        df_document_copy.drop(columns=matching.values(), inplace=True)
        for index, row in df_document_copy.iterrows():
            if len(columns_to_find) > 0:
                row_dict = row.to_dict()

                if Semantics.COLUMN_VENDOR in columns_to_find:
                    column, vendor_info, additional_info = self.token_matcher.match_vendor_by_row(row_dict)
                    if column is not None:
                        columns_to_find.remove(Semantics.COLUMN_VENDOR)
                        matching[Semantics.COLUMN_VENDOR] = column
                        df_document_copy.drop(columns=[column], inplace=True)
                        del row_dict[column]

                if Semantics.COLUMN_FAMILY in columns_to_find:
                    # TODO vendor as param if it exists look in matching, column => { match, value, normalized }
                    column, brand_info, additional_info = self.token_matcher.match_brand_by_row(row_dict)
                    if column is not None:
                        columns_to_find.remove(Semantics.COLUMN_FAMILY)
                        matching[Semantics.COLUMN_FAMILY] = column
                        df_document_copy.drop(columns=[column], inplace=True)
                        del row_dict[column]

        if Semantics.COLUMN_PRODUCT_TYPE in columns_to_find:
            found_type = False
        else:
            found_type = True
        tries = 5
        tries_type = 5
        last_match_type = None
        for index, row in df_document_copy.iloc[0:tries].iterrows():
            if len(columns_to_find) > 0:
                row_dict = row.to_dict()

                matches = self.token_matcher.match_product_type_by_row(row_dict)
                if len(matches) == 0:
                    continue

                match = matches[0]
                column = match['request_column']
                if Semantics.COLUMN_PRODUCT_TYPE in columns_to_find:
                    if match['match_reason'] in [Semantics.TOKEN_PARENTHESES_FEATURE_GROUP,
                                                 Semantics.TOKEN_SUB_SERIES,
                                                 Semantics.TOKEN_SERIES_AND_SUB_SERIES_MIX,
                                                 Semantics.TOKEN_FEATURE_GROUP]:
                        del row_dict[column]
                        columns_to_find.remove(Semantics.COLUMN_PRODUCT_TYPE)
                        df_document_copy.drop(columns=[column], inplace=True)
                        found_type = True
                        matching[Semantics.COLUMN_PRODUCT_TYPE] = column

                    elif match['match_reason'] in [Semantics.TOKEN_SERIES,
                                                   Semantics.TOKEN_FEATURE_SERIE]:
                        if tries_type > 1:
                            last_match_type = match
                        elif tries_type == 0:
                            del row_dict[column]
                            columns_to_find.remove(Semantics.COLUMN_PRODUCT_TYPE)
                            df_document_copy.drop(columns=[column], inplace=True)
                            found_type = True
                            matching[Semantics.COLUMN_PRODUCT_TYPE] = column
                        tries_type = tries_type - 1

        if found_type is False and last_match_type is not None:
            column = last_match_type['request_column']
            columns_to_find.remove(Semantics.COLUMN_PRODUCT_TYPE)
            df_document_copy.drop(columns=[column], inplace=True)
            matching[Semantics.COLUMN_PRODUCT_TYPE] = column

        if found_type and Semantics.COLUMN_PRODUCT_NAME in columns_to_find:
            for index, row in df_document_copy.iloc[0:tries].iterrows():
                if len(columns_to_find) > 0:
                    row_dict = row.to_dict()
                    matches = self.token_matcher.match_product_type_by_row(row_dict)
                    if len(matches) == 0:
                        continue

                    match = matches[0]
                    column = match['request_column']
                    matching[Semantics.COLUMN_PRODUCT_NAME] = column
                    columns_to_find.remove(Semantics.COLUMN_PRODUCT_NAME)
                    df_document_copy.drop(columns=[column], inplace=True)
                    break
        return matching

    def mapping_with_miner_normalize(self, columns: [], values: []) -> (dict, []):

        matching = self.mapping_with_miner(columns, values, normalize_data=True)

        df_document = pd.DataFrame(data=values, columns=columns)
        df_document_copy = df_document.copy()

        columns_to_check = [Semantics.COLUMN_PRODUCT_TYPE, Semantics.COLUMN_VENDOR, Semantics.COLUMN_FAMILY]
        intersection = list(set(columns_to_check) & set(matching.keys()))

        new_column_vendor = False
        new_column_product_type = False
        new_column_brand = False

        for index, row in df_document_copy.iterrows():
            row_dict = row.to_dict()

            if (Semantics.COLUMN_VENDOR in intersection or
                    Semantics.COLUMN_MAC in matching or
                    Semantics.COLUMN_OUI in matching):
                oui_value = None
                vendor_info = None
                if Semantics.COLUMN_MAC in matching:
                    column_mac = matching[Semantics.COLUMN_MAC]
                    if column_mac in row_dict:
                        mac_value = StringMinerHelper.extract_mac_normalized(row_dict[column_mac])
                        if mac_value is not None:
                            oui_value = ':'.join(mac_value.split(':')[:3])
                elif Semantics.COLUMN_OUI in matching:
                    column_oui = matching[Semantics.COLUMN_OUI]
                    if column_oui in row_dict:
                        oui_value = StringMinerHelper.extract_mac_normalized(row_dict[column_oui], oui=True)
                if oui_value is not None:
                    vendor_info, descr = self.token_matcher.match_vendor_by_oui(oui_value)

                column_match = None
                # if oui and mac no hits but vendor column itself still exists
                if not vendor_info and Semantics.COLUMN_VENDOR in intersection:
                    column_match = matching[Semantics.COLUMN_VENDOR]
                    search_vendor_dict = {column_match: row_dict[column_match]}
                    column_match, vendor_info, additional_info = self.token_matcher.match_vendor_by_row(search_vendor_dict)

                # if mac or oui exists but no vendor column exists -> open new column
                if not Semantics.COLUMN_VENDOR in intersection and vendor_info:
                    column_match = Semantics.COLUMN_VENDOR
                    matching[Semantics.COLUMN_VENDOR] = Semantics.COLUMN_VENDOR
                    if new_column_vendor is False:
                        new_column_vendor = True
                        df_document_copy[column_match] = None

                if column_match is not None:
                    df_document_copy.loc[index, column_match] = vendor_info

            # TODO vendor mitliefern wenn vorhanden
            if Semantics.COLUMN_FAMILY in intersection:
                column_product_family = matching[Semantics.COLUMN_FAMILY]
                column, brand_info, additional_info = self.token_matcher.match_brand_by_row({column_product_family:
                                                                                                 row_dict[column_product_family]})
                if brand_info and Semantics.COLUMN_VENDOR not in matching:
                    vendor_info = additional_info['vendor']
                    matching[Semantics.COLUMN_VENDOR] = Semantics.COLUMN_VENDOR
                    if new_column_vendor is False:
                        df_document_copy[Semantics.COLUMN_VENDOR] = None
                        new_column_vendor = True
                    df_document_copy.loc[index, Semantics.COLUMN_VENDOR] = vendor_info

                if brand_info is not None:
                    df_document_copy.loc[index, column_product_family] = brand_info

            if Semantics.COLUMN_PRODUCT_TYPE in intersection:
                column_product_type = matching[Semantics.COLUMN_PRODUCT_TYPE]
            else:
                if new_column_product_type is False:
                    new_column_product_type = True
                    df_document_copy[Semantics.COLUMN_PRODUCT_TYPE] = None
                column_product_type = Semantics.COLUMN_PRODUCT_TYPE

            row_for_type_search = row_dict.copy()
            remove_fields = [Semantics.COLUMN_MAC, Semantics.COLUMN_OUI, Semantics.COLUMN_IP]
            for remove_field in remove_fields:
                if remove_field in matching:
                    del row_for_type_search[matching[remove_field]]

            matches = self.token_matcher.match_product_type_by_row(row_for_type_search)
            if len(matches) > 0:
                if len(matches) > 1:
                    match = self._reevaluate_matches(matching, matches, row_for_type_search)
                else:
                    match = matches[0]

                product_type_series_suggest = match['product_type_series_suggest']
                probability = match['probability']
                vendor = match['vendor']
                brand = StringMinerHelper.extract_brand(match)

                # TODO threshold parameter how much weight give product_types
                if probability > 60:
                    if Semantics.COLUMN_FAMILY in matching:
                        column_brand = matching[Semantics.COLUMN_FAMILY]
                        brand_compare = df_document_copy.loc[index, column_brand]
                        if brand_compare != brand:
                            df_document_copy.loc[index, column_brand] = brand
                    else:
                        if new_column_brand is False:
                            new_column_brand = True
                            df_document_copy[Semantics.COLUMN_FAMILY] = None
                        column_brand = Semantics.COLUMN_FAMILY
                        df_document_copy.loc[index, column_brand] = brand

                    if not Semantics.COLUMN_VENDOR in intersection and new_column_vendor is False:
                        if new_column_vendor is False:
                            new_column_vendor = True
                            df_document_copy[Semantics.COLUMN_VENDOR] = None
                        matching[Semantics.COLUMN_VENDOR] = Semantics.COLUMN_VENDOR

                    column_vendor = matching[Semantics.COLUMN_VENDOR]

                    # overwrite because of better match from product_type
                    df_document_copy.loc[index, column_product_type] = product_type_series_suggest
                    df_document_copy.loc[index, column_vendor] = vendor
        return matching, df_document_copy

    # TODO nach token matcher verlagern
    def _reevaluate_matches(self, matching, matches, row_for_type_search):
        if Semantics.COLUMN_FAMILY in matching:
            brand = row_for_type_search[matching[Semantics.COLUMN_FAMILY]]
            brand_found = False
            found = []
            for match in matches:
                whole_tokens = match['tokens']
                if match['match_reason'] in [Semantics.TOKEN_SERIES,
                                    Semantics.TOKEN_SERIES_AND_SUB_SERIES_MIX,
                                    Semantics.TOKEN_SUB_SERIES,
                                    Semantics.TOKEN_FEATURE_GROUP,
                                    Semantics.TOKEN_FEATURE_SERIE,
                                    Semantics.TOKEN_PARENTHESES_FEATURE_STATIC]:
                    brand_compare = StringMinerHelper.extract_brand(match)
                    if brand_compare.lower() == brand.lower():
                        brand_found = True
                        found.append(match)
            if len(found) == 1:
                return found[0]
        # TODO weiter eingrenzen mit weiteren Token
        return matches[0]

    def _run_matcher(self, score_match_item, column_name, score_weight, records) -> (str | None, {}):
        matcher = self._load_matcher(score_match_item['matcher'], score_match_item['params'], column_name, score_weight)
        hits = matcher.match_column_from_document(records)
        if hits is not None:
            return self._unique_winner(hits), hits
        return None, hits

    # TODO not used
    def rating_local_score(self, local_matches: list, rate_mode: str):
        local_result_matching = {}
        if rate_mode == self.RATING_MODE_MAXIMUM:
            for matching in local_matches:
                for key, value in matching.items():
                    if key not in local_result_matching.keys():
                        local_result_matching[key] = value
                    elif value > local_result_matching[key]:
                        local_result_matching[key] = value
            return local_result_matching
        elif rate_mode == self.RATING_MODE_AVERAGE:
            count = len(local_matches)
            for matching in local_matches:
                for key, value in matching.items():
                    if key not in local_result_matching.keys():
                        local_result_matching[key] = value
                    else:
                        local_result_matching[key] = float(local_result_matching[key] + value)
            for matching in local_matches:
                for key, value in matching.items():
                    local_result_matching[key] = float(local_result_matching[key] / count)
            return local_result_matching

    def _load_matcher(self, matcher_name:str, params:dict, field_name:str, weight:float) -> Semantics:
        if matcher_name == 'word_of_bag':
            return WordOfBagMatcher(params=params, field_name=field_name, weight=weight)
        if matcher_name == 'ip':
            return IpMatcher(params=params, field_name=field_name, weight=weight)
        elif matcher_name == 'regex':
            return RegexMatcher(params=params, field_name=field_name, weight=weight)
        elif matcher_name == 'dict':
            return DictMatcher(params=params, field_name=field_name, weight=weight)
