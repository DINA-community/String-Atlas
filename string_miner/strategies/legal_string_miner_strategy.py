from normalizer.tree.product_node import ProductNode
from string_miner.string_miner import StringMinerStrategy
from string_miner.string_miner_helper import StringMinerHelper


class VendorAndLegalStringMinerStrategy(StringMinerStrategy):
    NAME = 'Legal String Miner'
    legal_forms = None
    oui_lookup = None
    oui_lookup_without_legal_forms = None

    def __init__(self, legal_entities_file_name, oui_lookup_file_name, csaf_vendors:[]):
        super().__init__(name=self.NAME)

        print('OUI Vendors')
        # print(self.oui_lookup, self.oui_lookup_without_legal_forms)
        print(self.oui_lookup_without_legal_forms)
        import sys
        sys.exit()

    def annotate_token(self, token, token_before:ProductNode=None, token_after=None, next_meta_info=None, level=0) -> ():
        return None, None
