from matcher.lib.lookup_client import TokenMarker
from matcher.lib.token_enum import TokenSemanticEnum
from matcher.token_matcher_decision import TokenMatcherDecision


class TokenMatcher:

    COLUMN_REASON = "reason"
    BATCH_SIZE = 1000

    def match_all_with_fallbacks(self, token_matcher_decision:TokenMatcherDecision, text: str) -> dict[str,str] | None:

        token:list = text.split()
        token_matcher_decision.set_token_list(token)

        token_matcher_decision.find(TokenMarker.PLACEHOLDER)
        token_matcher_decision.find(TokenMarker.VENDOR)
        token_matcher_decision.find(TokenMarker.BRAND)
        token_matcher_decision.find(TokenMarker.PRODUCT_SUB_SERIES)

        results = token_matcher_decision.get_result()

        if TokenMarker.PRODUCT_SUB_SERIES in results:
            normalized = (results[TokenMarker.PRODUCT_SUB_SERIES][3][TokenSemanticEnum.BRAND.value] + " " +
                          results[TokenMarker.PRODUCT_SUB_SERIES][3][TokenSemanticEnum.NORMALIZED.value])
            decision_reason = results[TokenMarker.PRODUCT_SUB_SERIES][2].value
            print(f'***ENTITY SUCHE: {token} - ***FOUND: {normalized} ***REASON: {decision_reason} -')
            return {TokenSemanticEnum.NORMALIZED.value: normalized, self.COLUMN_REASON: decision_reason,
                    TokenSemanticEnum.CSAF_REF.value: results[TokenMarker.PRODUCT_SUB_SERIES][3][TokenSemanticEnum.CSAF_REF.value]}
        print(f'***ENTITY SUCHE: {token} - FOUND: -')
        return None
