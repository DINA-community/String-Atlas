from enum import Enum
from matcher.lib.common import is_number
from matcher.lib.lookup_table import PREFIX_TOKEN_VENDOR, PREFIX_TOKEN_BRAND, PREFIX_TOKEN_PRODUCT, \
    PREFIX_TOKEN_PLACEHOLDER
from matcher.lib.lookup_client import TokenMarker
from matcher.lib.token_enum import TokenSemanticEnum
from matcher.match_strategy.match_strategy import MatchStrategy


class TokenMatchReason(Enum):
    DIRECT_LOOKUP = 1
    SIMILAR_LOOKUP = 2
    VECTOR_LOOKUP = 3
    REGEX_LOOKUP = 4
    MARKER_OVERWRITTEN = 0
    NOT_FOUND = 10
    NOT_SEARCHED = 20


class DecisionReason(Enum):
    UNIQUE = 0
    DIRECT_FULL_MATCH_MULTIPLE_TOKEN = 1
    DIRECT_FULL_MATCH_SINGLE_TOKEN = 2
    FULL_MATCH_MULTIPLE_TOKEN = 3
    FULL_MATCH_SINGLE_TOKEN = 4
    PARTIAL_MATCH_MULTIPLE_TOKEN = 5
    NO_DECISION_MATCH = 100
    """
    example
    GESUCHT Siemens Energy

    DIREKT: Siemens Energy
        DIRECT_FULL_MATCH_MULTIPLE_TOKEN = 1
        DIRECT_FULL_MATCH_SINGLE_TOKEN = 2
    SIMILAR: Seimens Energy
        All tokens found for Siemens Energy
            FULL_MATCH_MULTIPLE_TOKEN = 3
            Seimens Energy
            FULL_MATCH_SINGLE_TOKEN = 4
                Seimens
        Partial Token FileNotFoundError
            Energy (1/2)
            PARTIAL_MATCH_MULTIPLE_TOKEN = 5
    """


class TokenMatcherDecision:

    def __init__(self, match_strategies: list[MatchStrategy], config={}):
        self.config:dict = config
        self.match_strategies: list[MatchStrategy] = match_strategies
        self.tokens: list[str] = []
        self.ran_strategy:dict[str,bool] = {}
        self.run_once = False

        for strategy in self.match_strategies:
            if strategy.runs_only_onces():
                self.run_once_before = True
                break

    # TODO fetch default threshold from config
    def _get_strategy_threshold(self, strategy: MatchStrategy, default: float = 0.7) -> float:
        threshold_key = strategy.get_name() + '_threshold'
        if threshold_key in self.config:
            threshold = self.config[threshold_key]
        else:
            threshold = self.config.get("threshold", default)
        return float(threshold)

    def _initialise_tokens(self):
        """
        tuple for temporary search results
        0 = Entity oder Entities
            { "id" = L_E_<KEY>, "count": <count token as int>, "score": float}
        1 = TokenMatcherReason
        2 = TokenMarker
        """
        self.meta_tokens: list[tuple[dict[str, str], TokenMatchReason, TokenMarker]] = []


        """
        decided entities for token match

        0 = count all token for certain entity - zero if no match
        1 = Token Position
        2 = Decision Reason
        3 = Token Marker
        """
        self.decision_tokens: list[tuple[int, int, DecisionReason, TokenMarker]] = []


        """
        key: TokenMarker - f. e. Vendor

        0: Entity Key Id
        1: list - token positions
        2: Decision Reason
        3: Entity oder Entities
            { "id" = L_E_<KEY>, "count": <count token as int>}
        """
        self.entities: dict[TokenMarker, tuple[str, list[int], DecisionReason, dict[str, str]]] = {}

        for i in range(0, len(self.tokens)):
            self.meta_tokens.append(({}, TokenMatchReason.NOT_SEARCHED, TokenMarker.UNCERTAIN))
            self.decision_tokens.append((0, i, DecisionReason.NO_DECISION_MATCH, TokenMarker.UNCERTAIN))


    def set_token_list(self, token_list: list[str]):
        self.tokens:list[str] = token_list
        self._initialise_tokens()

    def find(self, token_marker: TokenMarker):
        prefix_token = ''
        # TODO filter
        entity_filter: list[dict[str, str]] = []
        if token_marker == TokenMarker.PLACEHOLDER:
            prefix_token = PREFIX_TOKEN_PLACEHOLDER
        elif token_marker == TokenMarker.VENDOR:
            prefix_token = PREFIX_TOKEN_VENDOR
        elif token_marker == TokenMarker.BRAND:
            prefix_token = PREFIX_TOKEN_BRAND
            if TokenMarker.VENDOR in self.entities:
                entity_filter = [{TokenMarker.VENDOR: self.entities[TokenMarker.VENDOR]}]
        else:
            prefix_token = PREFIX_TOKEN_PRODUCT
            if TokenMarker.VENDOR in self.entities:
                entity_filter.append({TokenMarker.VENDOR: self.entities[TokenMarker.VENDOR][3][TokenSemanticEnum.VENDOR_ID.value]})
            if TokenMarker.BRAND in self.entities:
                entity_filter.append({TokenMarker.BRAND: self.entities[TokenMarker.BRAND]})

        # todo in richtiger reihenfolge so wie strategies gesetzt sind, auch wenn vendor bereits gefunden nicht mehr nötigt usw.
        if not self.ran_strategy and self.run_once:
            self.run_one_time_stategy()
            self.ran_strategy = True


        self._find_tokens(prefix_token=prefix_token, marker=token_marker,
                          entity_filter=entity_filter)

        print("FILTER")
        print(entity_filter)
        self._decide(token_marker=token_marker)


        print(f"DECIDED: {token_marker} --------------------")
        if token_marker in self.entities:
            print(self.entities[token_marker])
        else:
            print("None")
            print("Debug: ---")
            print(self.meta_tokens)

    # TODO not whole text yet only single tokens
    def run_one_time_stategy(self, strategy: MatchStrategy):
            tokens_search_pos = self._get_unmatched_token_pos()
            for token_pos in tokens_search_pos:
                token = self.tokens[token_pos]
                if is_number(token):
                    continue
                else:
                    token = str(token)

                threshold = self._get_strategy_threshold(strategy)
                entity_filtered = strategy.match(token, prefix_token=None, entity_filter=[], threshold=threshold)
                if entity_filtered is not None and len(entity_filtered) > 0:
                    lst = list(entity_filtered)
                    lst.append(strategy.get_match_reason())
                    token_marker = strategy.result_overwriting
                    lst.append(token_marker)
                    self.meta_tokens[token_pos] = tuple(lst)
                    token_description = (1, [token_pos], strategy.get_decision_reason(),
                                         token_marker)
                    self.decision_tokens[token_pos] = token_description
                    self.entities[token_marker] = (lst[0]["id"], [token_pos], strategy.get_decision_reason(), lst[0])


    def _get_unmatched_token_pos(self) -> list[int]:
        pos = 0
        token_positions = []
        for value in self.decision_tokens:
            if value[2].value == DecisionReason.NO_DECISION_MATCH.value:
                token_positions.append(pos)
            pos = pos + 1
        return token_positions


    def _decide(self, token_marker: TokenMarker) -> None:
        """

        key:str EntityKey

        tuple
        0: count all for entitiy id tokens
        1: list - suggested tokens position which entity build of in total token amount
        2: DecisionReason - decision reason suggested temporaly
        3: TokenMatcherReason
        """
        entity_ids_counter: dict[str, tuple[int, list[int], TokenMatchReason]] = {}

        tokens_search_pos = self._get_unmatched_token_pos()

        # counting token
        token_pos: int = -1
        for token_metas in self.meta_tokens:
            token_pos = token_pos + 1

            # fehlerquelle : hat für selbe position mehre token plaziert iund ist dann multiple token
            # direct lookup sollte rulen. anstatt multiple partial
            for token_meta in token_metas:
                if not isinstance(token_meta,dict):
                    continue

                if isinstance(token_meta, TokenMatchReason) or isinstance(token_meta, TokenMarker):
                    continue

                token_matcher_reason = token_metas[-2]
                if token_pos not in tokens_search_pos:
                    continue

                #print(token_meta)
                if not token_metas[-1].value == token_marker.value:
                    continue

                if token_marker == TokenMarker.PLACEHOLDER:
                    # decision relies on threshold
                    token_description = (1, [token_pos], DecisionReason.FULL_MATCH_SINGLE_TOKEN,
                                         token_marker)
                    self.decision_tokens[token_pos] = token_description
                    continue

                entity_id = token_meta["id"]
                count_token_total_for_id: int = int(token_meta["count"])
                if entity_id not in entity_ids_counter:
                    compare_entity = (count_token_total_for_id, [token_pos], token_matcher_reason)
                else:
                    compare_entity = entity_ids_counter[entity_id]
                    compare_entity = (count_token_total_for_id, compare_entity[1] + [token_pos], token_matcher_reason)
                entity_ids_counter[entity_id] = compare_entity

        # decide for best score and reason
        min_decision = None
        min_decision_id = None
        min_decision_status = None
        for entity_id, suggestion in entity_ids_counter.items():
            count_token_total_for_id: int = suggestion[0]
            count_token_pos: int = len(suggestion[1])
            suggestion_status = DecisionReason.NO_DECISION_MATCH
            if count_token_pos < count_token_total_for_id:
                if count_token_total_for_id > 1:
                    suggestion_status = DecisionReason.PARTIAL_MATCH_MULTIPLE_TOKEN
            else:
                if count_token_total_for_id > 1:
                    if suggestion[2].value == TokenMatchReason.DIRECT_LOOKUP.value:
                        suggestion_status = DecisionReason.DIRECT_FULL_MATCH_MULTIPLE_TOKEN
                    else:
                        suggestion_status = DecisionReason.FULL_MATCH_MULTIPLE_TOKEN
                else:
                    if suggestion[2].value == TokenMatchReason.DIRECT_LOOKUP.value:
                        suggestion_status = DecisionReason.DIRECT_FULL_MATCH_SINGLE_TOKEN
                    else:
                        suggestion_status = DecisionReason.FULL_MATCH_SINGLE_TOKEN

            if min_decision is None or suggestion_status.value < min_decision_status.value \
                or \
                (suggestion_status.value == min_decision_status.value and
                 suggestion[2].value < min_decision[2].value):
                min_decision_id = entity_id
                min_decision_status = suggestion_status
                min_decision = suggestion

        if min_decision is None or min_decision == DecisionReason.NO_DECISION_MATCH or len(min_decision[1]) == 0:
            return None
        else:

            # trim overloaded suggestions
            # for example if more tokens are matched then originally used
            count_token_total_for_id = min_decision[0]
            token_pos_elements = min_decision[1]
            if count_token_total_for_id < len(token_pos_elements):
                token_pos_elements = self._decide_operation_limit_token_matches(count_token_total_for_id,
                                                                                token_pos_elements)

            for token_pos_element in token_pos_elements:
                token_description = (count_token_total_for_id, token_pos_elements, min_decision_status, token_marker)
                self.decision_tokens[token_pos_element] = token_description

            entity_selected = None
            entities = self.meta_tokens[token_pos_elements[0]]
            for entity in entities:
                if entity["id"] == min_decision_id:
                    entity_selected = entity
                    break

            self.entities[token_marker] = (min_decision_id, token_pos_elements, min_decision_status, entity_selected)

            if token_marker.value == TokenMarker.BRAND.value:
                if TokenMarker.VENDOR not in self.entities and len(entity_selected[TokenSemanticEnum.VENDOR.value]) == 1:
                    fetched_vendor = entity_selected[TokenSemanticEnum.VENDOR_ID.value]
                    if isinstance(fetched_vendor, list):
                        vendor = fetched_vendor[0]
                    else:
                        vendor = fetched_vendor

                    self.entities[TokenMarker.VENDOR] = (0, [], entity_selected["score"], {TokenSemanticEnum.VENDOR_ID.value: vendor})
        return None

    def _decide_operation_limit_token_matches(self, count_all, token_pos_elements):
        """
        reduces suggested token by score and if still more exists cut the tail of token ending
        """

        tokens_positions = token_pos_elements
        score_max = {}
        token_count_reducing = len(token_pos_elements) - count_all

        for i in range(1, count_all):
            for token_pos_element in tokens_positions:
                token_meta = self.meta_tokens[token_pos_element]
                if token_meta[1] == TokenMatchReason.DIRECT_LOOKUP:
                    continue
                else:
                    score_max[token_pos_element] = token_meta[0]["score"]

        sorted_dict = dict(sorted(score_max.items(), key=lambda item: item[1]))

        if token_count_reducing <= len(sorted_dict):
            removing = sorted_dict[0:token_count_reducing]
            for remove_item in removing:
                tokens_positions.remove(remove_item)
            token_count_reducing = token_count_reducing - len(removing)
        elif len(sorted_dict) > 0:
            token_count_reducing = token_count_reducing - len(sorted_dict)
            for remove_item in token_count_reducing:
                tokens_positions.remove(remove_item)

        # cut end because position is deciding
        if token_count_reducing > 0:
            tokens_positions = tokens_positions[:-token_count_reducing]

        return tokens_positions



    def _find_tokens(self, prefix_token, marker=TokenMarker.UNCERTAIN, entity_filter: list[dict[str,str]]=[]):

        tokens_search_pos = self._get_unmatched_token_pos()

        for token_pos in tokens_search_pos:
            token = self.tokens[token_pos]

            # TODO regex Version numbers. physical units for future ideas
            if is_number(token):
                continue
            else:
                token = str(token)

            for strategy in self.match_strategies:

                if strategy.runs_only_onces():
                    if strategy.get_name() not in self.ran_strategy:
                        self.ran_strategy[strategy.get_name()] = True
                        self.run_one_time_stategy(strategy)
                    continue

                threshold = self._get_strategy_threshold(strategy)
                entity_filtered = strategy.match(token, prefix_token=prefix_token, entity_filter=entity_filter, threshold=threshold)
                if entity_filtered is not None and len(entity_filtered) > 0:
                    lst = list(entity_filtered)
                    lst.append(strategy.get_match_reason())
                    if strategy.get_match_reason() == TokenMatchReason.MARKER_OVERWRITTEN:
                        lst.append(strategy.result_overwriting)
                    else:
                        lst.append(marker)
                    self.meta_tokens[token_pos] = tuple(lst)
                    break

    def get_result(self):
        return self.entities
