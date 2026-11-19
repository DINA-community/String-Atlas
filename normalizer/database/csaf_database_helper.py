class CSAFDataBaseHelper:
    def __init__(self):
        pass

    def search_token(self, token, offset, batch_size, vendor=None, brand=None):
        pass

    def search_vendor(self, text:str, count_matches=1):
        pass

    def search_oui(self, oui: str, count_matches=1):
        pass

    def search_brand(self, text:str, vendor:str):
        pass

    def create_product_type_index(self):
        pass

    def create_regex_product_type_index(self):
        pass

    def save_json_data(self, key, json_value):
        """ use json.dumps for json_value before"""
        pass

    def short_type_index(self, token_segment_types:[]):
        pass

    # TODO not used
    def fetch_regexes(self, vendor:str, short_type_index:str) -> []:
        pass

    def fetch_regexes_by_group(self, vendor:str, group_regex:str, short_type_index:str, brand:str=None) -> list:
        pass

    # TODO unique Key index ? ja für lerneffekt
    def get_value_by_uuid(self, uuid):
        pass

    def create_vendor_index(self):
        pass

    def create_brand_index(self):
        pass

    def create_oui_index(self):
        pass

    # TODO not yet used, for learn effekt
    def save_vendors(self):
        pass

    # TODO not yet used, for learn effekt
    def save_brands(self):
        pass

    def clean_tokens(self, df, vendor=None, brand=None):
        pass

    def get_value(self, key:str):
        pass

    def set_value(self, key:str, value:str):
        pass

