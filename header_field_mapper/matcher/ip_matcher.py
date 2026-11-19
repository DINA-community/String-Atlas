import ipaddress
from .matcher import Matcher

import pandas as pd

class IpMatcher(Matcher):

    def __init__(self, params, field_name, weight):
        super().__init__(params=params, field_name=field_name, weight=weight)

    def match_value(self, value):
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    def match_column_from_document(self, records: pd.DataFrame):
        pass