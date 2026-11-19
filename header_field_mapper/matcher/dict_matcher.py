from .matcher import Matcher
import pandas as pd
import process_csaf_files
import os
import Levenshtein


class DictMatcher(Matcher):
    SOURCE_CSAF = 'csaf'
    source_type = None

    # TODO singleton pattern, wird 4 mal geladen im test
    vendors_set = set()
    product_set = set()
    product_family_set = set()

    def __init__(self, params, field_name, weight):
        super().__init__(params=params, field_name=field_name, weight=weight)
        # TODO überprüfen und aus parameter laden
        # TODO generische source_type wie csv mit spaltenangabe (n) laden.
        self.source_type = self.SOURCE_CSAF

        if os.path.exists(r"D:\CSAF\csaf_files\OT\white\2024"):
            print("yes exist")
        else:
            print("no exist")
        df: pd.DataFrame = process_csaf_files.get_csaf_sources(r"D:\CSAF\csaf_files")

        # TODO strategie für weitere sourcen laden, einheitliches format dann. welche quellen kann man noch heranziehen
        # TODO wiederverwendbarkeit für texthomogenisierung!!! Eventuell dictmatcher rein auf vergleich konzentieren und für sourcen dictsource klassen auslagern

        df = df.iloc[1:].reset_index(drop=True)
        product_set = set()
        product_family_set = set()
        vendors_set = set()
        for row in df.itertuples(index=False):
            file_data = process_csaf_files.read_csaf_file(row.path)
            all_data = process_csaf_files.flatten_tree_data(file_data)

            product_data = list(all_data["product_name"].tolist())
            product_family_data = list(all_data["full_product_name_branch"].tolist())
            vendors = list(all_data["vendor"].tolist())
            vendors_set = set(vendors + list(vendors_set))
            product_set = set(product_data + list(product_set))
            product_family_set = set(product_family_data + list(product_family_set))

        self.vendors_set = vendors_set
        self.product_set = product_set
        self.product_family_set = product_family_set

    def match_value(self, value):
        # TODO was ist wenn es leerer String ist -> nicht bewertbar. muss davor abgefangen werden

        # TODO keine magic string, muss aus parameter kommen
        if self.params['attribute'] == 'vendor':
            compare_set = self.vendors_set
        elif self.params['attribute'] == 'product_name':
            compare_set = self.product_set
        elif self.params['attribute'] == 'product_family':
            compare_set = self.product_family_set
            # TODO speziell aufbereiten aus den csaf files

        if value in compare_set:
            return True
        else:
            # TODO in 2. runde wenn gar nichts gefunden wurde Use-Case direkter match. 2. runde ist dann ähnlichkeitsvergleich nach threshold. das kann sich für jede Spalte unterscheiden.
            # da rechenintensiv
            for vendor_name in compare_set:
                if self.match_similar(value, vendor_name, self.params['threshold']):
                    return True
            return False

    # TODO über String Miner gehen
    def match_similar(self, value, compare_value, threshold=0.4):
        if self.match_levenshtein(value, compare_value, threshold):
            return True
        elif self._find_similar_substrings(compare_value, value, threshold):
            return True
        return False
        # TODO String_miner hat hier schon implementierung. warum das nicht mit wörterbüchern füttern und darauf basieren ?
        # TODO threshold

    def _find_similar_substrings(self, target_string, search_string, threshold):
        # TODO fehlerbehandlung searchstring
        if search_string == '' or target_string == '':
            return False

        similar_substrings = []

        for i in range(len(target_string) - len(search_string) + 1):
            substring = target_string[i: i + len(search_string)]
            distance = Levenshtein.distance(substring, search_string)
            similarity_score = 1 - (distance / max(len(substring), len(search_string)))

            if similarity_score >= threshold:
                similar_substrings.append((substring, similarity_score))

        return similar_substrings

    def match_levenshtein(self, word: str, search_string: str, threshold: float):
        distance = Levenshtein.distance(word, search_string)
        similarity_score = 1 - (distance / max(len(word), len(search_string)))
        if similarity_score >= threshold:
            return True
        else:
            return False
