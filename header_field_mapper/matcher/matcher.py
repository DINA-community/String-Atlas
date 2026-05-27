import pandas as pd


class Matcher:
    params = {}
    field_name = None
    weight = None

    def __init__(self, params, field_name, weight):
        self.params = params
        self.field_name = field_name
        self.weight = weight

    def match_column_from_document(self, records: pd.DataFrame):
        pass
