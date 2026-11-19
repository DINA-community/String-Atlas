"""
    Note: String matching can be improved by implementing different distance metrics.
    For example, when multiple results are found, preference can be given to results with just a two-character
    difference, such as when neighboring characters are switched, as in 'Test' and 'Tset'."
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
import re
import re as regex

from nlp_miner import result_miner

import pandas
import pandas as pd
import yaml
from string_helperfunctions import find_file

IS_LEV = False
try:
    from rapidfuzz.distance import Levenshtein
except ModuleNotFoundError:

    IS_LEV = False
else:
    IS_LEV = True

# NOTE: The following definitions are used by default and can be customized if changes are made to the regex collection or corpus.

# Default path to the file containing a regex collection (file type .yaml) used for regex matching. Modify file and path if using a custom file.
DEFAULT_REGEX_COLLECTION_FILE = find_file("re_data.yaml")
# Default list of the regex categories to use from the regex collection file. Add or remove entries from the list to limit or extend the regex matching. Ensure that the spelling matches the entries in the regex file.
DEFAULT_REGEX_CATEGORIES = ["Device Family", "Device Type", "Article Number", "Version"]
# Default path to the corpus file (file type .xlsx) used for levenshtein distance matching. Modify the corpus file and path for custom data.
DEFAULT_CORPUS_FILE = find_file("device_list.xlsx")
# Default list of columns to use from the corpus file. Add or remove column entries from the list to limit or extend the levenshtein distance matching. Ensure that the spelling matches the columns from the corpus file.
DEFAULT_CORPUS_COLUMNS = ["Device Family", "Device Type", "Article Number"]
# Default column for filtering, here manufacturer specific filtering from the corpus file.
DEFAULT_FILTER_COLUMN = "Manufacturer"


class StringMiner:
    """
    The StringMiner class provides methods for matching target strings with regular expressions and levenshtein distance.
    """

    def __init__(
            self,
            regex_collection_path: str = DEFAULT_REGEX_COLLECTION_FILE,
            regex_categories: list = DEFAULT_REGEX_CATEGORIES,
            corpus_data: pandas.DataFrame = None,
            corpus_path: str = DEFAULT_CORPUS_FILE,
            corpus_search_cols: list = DEFAULT_CORPUS_COLUMNS,
            corpus_filter_col: str = DEFAULT_FILTER_COLUMN,
    ):
        """
        Initializes the StringMiner object.

        Parameters:
        - regex_collection_path: str, Path to the file containing a regex collection (file type .yaml) used for regex matching. Modify file and path if using a custom file.
        - regex_categories: list, A list of the regex categories to use from the regex collection file. Add or remove entries from the list to limit or extend the regex matching.
        - corpus_path: str, Path to the corpus file (file type .xlsx) used for levenshtein distance matching. Modify the corpus file and path for custom data.
        - corpus_search_cols: list, A list of columns to use from the corpus file. Add or remove column entries from the list to limit or extend the levenshtein distance matching.
        - corpus_manufacturer_col: str, The column for filtering, here manufacturer specific filtering from the corpus file.
        """
        # Load the regular expressions from the file
        with open(regex_collection_path, "r", encoding='utf-8') as file:
            self.regex_dict = yaml.safe_load(file)

        # Read the search strings from the Excel file
        if corpus_data is not None:
            self.search_strings_df = corpus_data
        else:
            self.search_strings_df = pd.read_excel(corpus_path)
        self.fill_nan()
        self.re_attributes = regex_categories
        self.corpus_search_cols = corpus_search_cols
        self.corpus_vendor_col = corpus_filter_col

    def match(
            self, target_string: str, vendor_filter: str = "", strip_target: bool = False
    ):
        """
        Matches a target string with search strings using fuzzy matching and returns the matching attributes as a dictionary.

        Parameters:
        - target_string: str, the target string to match with search strings
        - vendor_filter: str, the vendor name to filter the search strings (default: "")
        - ignore_case: always on
        - strip_target: bool, whether to strip leading/trailing whitespace from the target string (default: False)

        Returns:
        - result: dict, a dictionary mapping attribute names to matching values
        """
        return self.match_fuzzy(target_string, 0, vendor_filter, strip_target)

    # TODO Pandas Operator Komponente
    def fill_nan(self, replace='', corpus: pandas.DataFrame = None):
        if corpus is None:
            self.search_strings_df.loc[:, :] = self.search_strings_df.fillna(replace)
            return self.search_strings_df
        else:
            corpus.loc[:, :] = corpus.fillna(replace)
            return corpus

    def match_fuzzy(
            self,
            target_string: str,
            max_errors: int = 1,
            vendor_filter: str = "",
            strip_target: bool = False,
    ):
        """
        Matches a target string with search strings using fuzzy matching and returns the matching attributes as a dictionary.

        Parameters:
        - target_string: str, the target string to match with search strings
        - max_errors: int, the maximum number of errors allowed in the fuzzy matching (default: 1)
        - vendor_filter: str, the vendor name to filter the search strings (default: "")
        - ignore_case: always on
        - strip_target: bool, whether to strip leading/trailing whitespace from the target string (default: False)

        Returns:
        - result: dict, a dictionary mapping attribute names to matching values
        """
        result = {}
        if strip_target:
            target_string = target_string.strip()

        for attribute in self.re_attributes:
            if (
                    matching_attributes := self._match_attribute_fuzzy(
                        target_string, max_errors, attribute, vendor_filter
                    )
            ) is not None:
                if matching_attributes:
                    result[attribute] = matching_attributes

        return result

    def _match_attribute_fuzzy(
            self, target_string: str, max_errors: int, attribute: str, vendor_filter: str = ""):
        """
        Matches a target string with a fuzzy regular expression for a specific attribute and returns the matching string or None.

        Parameters:
        - target_string: str, the target string to match with the fuzzy regular expression
        - max_errors: int, the maximum number of errors allowed in the fuzzy matching
        - attribute: str, the attribute name to match with the fuzzy regular expression
        - vendor_filter: str, the vendor name to filter the search strings (default: "")
        - re_flag: int, the flag for the fuzzy matching algorithm (default: regex.BESTMATCH)

        Returns:
        - result: str or None, the matching string or None if no match is found
        """
        result = None
        for k, regex_str in self.regex_dict[attribute].items():
            if not regex_str:
                continue
            if vendor_filter and vendor_filter != k:
                continue
            if type(regex_str) is list:
                for re_list in regex_str:
                    for i in range(max_errors + 1):
                        pattern = "(?:" + re_list + "){e<=" + str(i) + "}"
                        if match := regex.search(pattern, target_string, flags=regex.I):
                            result = match.group(0)
                            break
                    if result != None:
                        break
            else:
                for i in range(max_errors + 1):
                    pattern = "(?:" + regex_str + "){e<=" + str(i) + "}"
                    if match := regex.search(pattern, target_string, flags=regex.I):
                        result = match.group(0)
                        break
                if result is not None:
                    break
        return result

    def _find_similar_substrings(self, target_string, search_string, threshold):
        """
        Finds similar substrings in a target string based on Levenshtein distance.

        Parameters:
        - target_string: str, the target string to search for similar substrings
        - search_string: str, the search string to compare with substrings in the target string
        - threshold: float, the minimum similarity score threshold for a substring to be considered similar

        Returns:
        - similar_substrings: list, a list of tuples containing the similar substrings and their similarity scores
        """
        if not IS_LEV:
            return None

        similar_substrings = []

        for i in range(len(target_string) - len(search_string) + 1):
            substring = target_string[i: i + len(search_string)]
            similarity_score = Levenshtein.normalized_similarity(substring, search_string)

            if similarity_score >= threshold:
                similar_substrings.append((substring, similarity_score))

        return similar_substrings

    def match_levenshtein(
            self, target_string: str, threshold: float = 0.85, vendor_filter: str = "", strip_target: bool = False
    ):
        """
        Matches a target string with search strings using Levenshtein distance and returns the matching attributes as a dictionary.

        Parameters:
        - target_string: str, the target string to match with search strings
        - threshold: float, the minimum similarity score threshold for a substring to be considered a match (default: 0.85)
        - vendor_filter: str, the vendor name to filter the search strings (default: "")
        - strip_target: bool, whether to strip leading/trailing whitespace from the target string (default: False)

        Returns:
        - result_dict: dict, a dictionary mapping attribute names to matching values
        """
        if not IS_LEV:
            return None

        results = []
        if strip_target:
            target_string = target_string.strip()

        if vendor_filter:
            search_df = self.search_strings_df[self.search_strings_df[self.corpus_vendor_col] == vendor_filter]
            search_df = search_df[self.corpus_search_cols]
        else:
            search_df = self.search_strings_df[self.corpus_search_cols]

        for _, search_attributes in search_df.iterrows():
            for search_key, search_string in search_attributes.items():
                if search_string:
                    res = self._find_similar_substrings(target_string, str(search_string), threshold)
                    if len(res) > 0:
                        for r in res:
                            results.append([search_key, r[0].strip(), r[1]])
        result_df = pd.DataFrame(results, columns=["attribute", "value", "confidence"])
        result_df.drop_duplicates(inplace=True)
        result_df["confidence"] = pd.to_numeric(result_df["confidence"])
        max_confidence_indices = result_df.groupby("attribute")["confidence"].idxmax()
        result_df = result_df.loc[max_confidence_indices]
        result_df.drop("confidence", axis=1, inplace=True)
        result_dict = result_df.set_index("attribute").to_dict()["value"]

        return result_dict

    def statistic_words(self, index=1):
        # TODO check if boundary

        # Extrahieren des zweiten Wortes aus jeder Zeile
        self.search_strings_df['second_word'] = self.search_strings_df['product_name'].apply(
            lambda x: x.split()[index] if len(x.split()) > index else '')

        # Einzigartige (unique) zweite Wörter
        unique_second_words = self.search_strings_df['second_word'].unique()
        return unique_second_words

    def create_co_occurrence(self, corpus: list):
        vectorizer = CountVectorizer()
        X = vectorizer.fit_transform(corpus)
        co_occurrence_matrix = (X.T @ X).toarray()

        # Erstellen eines DataFrames für bessere Lesbarkeit
        vocab = vectorizer.get_feature_names_out()
        co_occurrence_df = pd.DataFrame(co_occurrence_matrix, index=vocab, columns=vocab)

        # Anzeige der Kookkurrenzmatrix
        # print(co_occurrence_df)

        if 'simatic' in vocab:
            # Abfrage der Zeile oder Spalte für "SIMATIC"
            simatic_occurrence = co_occurrence_df.loc['simatic']
            # print(simatic_occurrence)

    # TODO wurde ausgelagert
    def find_corpus_product_type(self, custom_corpus: pandas.DataFrame, search_terms, blacklist: list = [],
                                 regex_pattern=[]) -> pandas.DataFrame:
        if custom_corpus is None:
            corpus = self.search_strings_df
        else:
            corpus = custom_corpus

        if search_terms is None:
            if isinstance(search_terms, list) and len(regex_pattern) > 0:
                filtered_df = corpus[corpus['product_name'].apply(
                    lambda x: not any(
                        term in x for term in blacklist) and bool(
                        pd.Series(x).str.contains(regex_pattern[0], regex=True).any()))]
            else:
                # TODO blacklist anwenden
                filtered_df = corpus[corpus['product_name'].apply(
                    lambda x: not any(term in x for term in blacklist))]
        else:
            if isinstance(search_terms, list) and len(regex_pattern) > 0:
                filtered_df = corpus[corpus['product_name'].apply(
                    lambda x: all(term in x for term in search_terms) and not any(
                        term in x for term in blacklist) and bool(
                        pd.Series(x).str.contains(regex_pattern[0], regex=True).any()))]
            elif isinstance(search_terms, list):
                filtered_df = corpus[corpus['product_name'].apply(
                    lambda x: all(term in x for term in search_terms) and not any(term in x for term in blacklist))]
            else:
                # TODO blacklist anwenden
                filtered_df = corpus[corpus['product_name'].str.contains(search_terms, case=False)]
        return filtered_df

    def prepare_categories(self, vendor='Siemens', ):
        filtered_simatic = self.search_strings_df['product_name'][
            self.search_strings_df['product_name'].str.contains('SIMATIC')
            & ~self.search_strings_df['product_name'].str.contains('family', case=False, na=False)
            & ~self.search_strings_df['product_name'].str.contains('variants', case=False, na=False)]
        # case=False macht die Suche unabhängig von Groß- und Kleinschreibung.
        # na=False verhindert, dass NaN-Werte Fehler verursachen, indem sie als False behandelt werden.
        # Konvertieren der gefilterten Werte in eine Liste
        simatic_list = filtered_simatic.tolist()
        print(simatic_list)

        # rausfiltern von family und 'SIMATIC IPC427E (incl. SIPLUS variants)'
        # TODO hier in CSAF Dokument schauen ob die einzelnen produzct_tree_branch da sind hier nur nicht erfasst werden. dann spare ich mir die arbeit

    # TODO chatgpt

    def trim_vendor(self, text, vendor):
        words = text.split()  # Teilt den Text in Wörter
        if words[0].lower() == vendor:  # Prüft, ob das erste Wort "Siemens" ist
            return ' '.join(words[1:])  # Gibt den Text ohne das erste Wort zurück
        return text  # Gibt den Originaltext zurück, wenn das erste Wort nicht "Siemens" ist

    # Text Mining funktion
    # für Eingabe und korpus (aus CSAF) gleichzeitig verwendbar
    def detect_token(self, token1, token2):

        # version
        # [V][0-9][.][0-9]
        # syntaktisch
        # All versions prior to V2.8.1"
        pass

    # TODO category
    def create_pattern(self, token):
        pattern = []
        current_segment = ''
        segment_type = None

        # Iteriere über jedes Zeichen des Tokens
        for char in token:
            if char.isalpha():
                # Wenn der aktuelle Typ 'Buchstabe' ist, füge hinzu
                if segment_type == 'alpha':
                    current_segment += char
                else:
                    # Neuen Segmenttyp beginnen
                    if current_segment:
                        pattern.append(self.create_pattern(segment_type, current_segment))
                    current_segment = char
                    segment_type = 'alpha'
            elif char.isdigit():
                # Wenn der aktuelle Typ 'Zahl' ist, füge hinzu
                if segment_type == 'digit':
                    current_segment += char
                else:
                    # Neuen Segmenttyp beginnen
                    if current_segment:
                        pattern.append(self.create_pattern(segment_type, current_segment))
                    current_segment = char
                    segment_type = 'digit'
            else:
                # Wenn Sonderzeichen, direkt hinzufügen und Segment abschließen
                if current_segment:
                    pattern.append(self.create_pattern(segment_type, current_segment))
                pattern.append(re.escape(char))
                current_segment = ''
                segment_type = None

        # Letztes Segment hinzufügen, falls vorhanden
        if current_segment:
            pattern.append(self.create_pattern(segment_type, current_segment))
        return pattern

    # TODO chatgpt
    def create_segment_pattern(segment_type, segment, digit_additional_allowed=2):
        length = len(segment)
        if segment_type == 'alpha':
            return f'[A-Za-z]{{{length}}}'  # Buchstaben mit spezifischer Länge
        elif segment_type == 'digit':
            return f'\\d{{{length},{length + digit_additional_allowed}}}'  # Ziffern mit spezifischer Länge
        return ''

    # TODO tokens as parameter

    def components_from_token(self, token):
        pass

    # reine corpus features annotation function
    # man geht davon aus das es series beinhaltet
    def split_token_generic_series(self, corp, nr, semantic_location=False):

        # TODO mit annotieren beginnen
        annotation = []

        # TODO unterschied ich habe bei input daten korpus zur hilfe
        # an example mit Siemens ausprobieren


        corp['product_name'].to_json('C:\\Users\\itsic\\OneDrive\\PycharmProjects\\Masterarbeit\\3_BSI_Repos_Netbox und Plugin\\String-Atlas\\product_names.json', orient='values', indent=4)

        product_list = corp['product_name'].unique().tolist()
        for line in product_list:
            result_miner(line)


        import sys
        sys.exit()



        components_list = []
        components_for_sure = []
        for index, row in enumerate(corp['product_name'].tolist()):
            # TODO ganzer produkttypname
            print(row)
            continue
            # print(f"Index: {index}, Row as List: {row}")
            component_row = []
            tokens = row.split()
            token = tokens[0]

            if token == 'HMI':
                test = 1
            if len(tokens) > 1:
                next_token = tokens[1]
            else:
                components_for_sure.append(token)
                continue

            pattern = r'^[A-Za-z]+$|^\d+$'

            if '-' not in next_token and re.match(pattern, next_token) and '-' not in token and re.match(pattern,
                                                                                                         token):
                component1 = token
                component2 = next_token
                component_row = [component1, component1 + ' ' + component2]
                components_list.append(component_row)
            else:
                continue
        df = pd.DataFrame(components_list, columns=['Component_single', 'Component_pair'])
        # Zählen der Häufigkeit jeder Komponente

        # rekursiv
        for index, single_word in enumerate(df['Component_single'].tolist()):
            print(single_word)
            single_list = df[df['Component_single'] == single_word]
            double_list = df[df['Component_pair'].str.startswith(single_word)]
            double_list = double_list['Component_pair'].unique()


    # TODO
            # function result_miner

            # Folgewort Buchstabe oder Zahl -> oder mix -> Zahl und mix deuten auf unterserie hin
            # for word in words

            if single_word == 'WinCC':
                following_words = df['Component_pair'].str.replace(single_word, '', regex=False).str.strip().unique()
                print(following_words)

# TODO für design ORG, Named Entity Recognition (NER)


                # rekursiv count words

                # hier überlegen was folgewort ist
                # rekursiv wie lösen ?
                    # hersteller und marke sind shcon draußen
                    # unbekannte feature Character holen
            # > 1 -> mehrere Varianten

            # == 1 -> Annotiere Token als Serie

            # outlier -> wieviel von wieviel enthalten weitere token

            single_count = len(single_list)
            double_count = len(double_list)
            print(single_word, single_count, double_count)

            # Serie 1 WinCC - Unterserie - Runtime -
            # ['WinCC Runtime' 'WinCC flexible' 'WinCC OA' 'WinCC Professional'
            #  'WinCC TeleControl' 'WinCC Unified']

            # ['PCS 7' 'PCS neo']


            # paraemeter trheshold
            #

        #single_freq = df['Component_single'].value_counts()
        #print(single_freq)
        #pair_freq = df['Component_pair'].value_counts()
        #print(pair_freq)

        # Zusammenführen der Häufigkeiten in einen DataFrame
        #combined_freq = pd.concat([single_freq, pair_freq], axis=1, keys=['Single_Freq', 'Pair_Freq'])
        # NaN-Werte durch 0 ersetzen
        #combined_freq = combined_freq.fillna(0)
        # Ausgabe der kombinierten Häufigkeiten
        # print(combined_freq['Pair_Freq'])

        import sys
        sys.exit()

        current_flat_list = [sublist for sublist in split_tokens for component in sublist]
        flat_list.extend(current_flat_list)
        index = index + 1

        # Komponente (Drive Controller) -> kategorie wie erkennen ? -> Drive Controller CPU 1504D TF (6ES7615-4DF10-0AB0) ->hinweise in klammer, cpu nummer enthalten, herstellerspezifisch
        # Alle komponentne
        # flat_list = [component for sublist in split_tokens for component in sublist]

        df = pd.DataFrame(flat_list, columns=['Component'])
        # Zählen der Häufigkeit jeder Komponente
        frequency = df['Component'].value_counts()

        SEPERATOR = ['-']  # hat semantische bedeutung -> subseries
        # erstmal muss ermittelt werden ob das (haupt)-serie ist
        # components[0]

        # gibt es nochmal variatonen mit BuchstabenZahl mix, worauf deutet Zahl an ? kann man andere Varriatonen erfassen,
        # kann man bei anderen Varianten subseries, auch auf gleiches muster schließen -> components[1]

        #TODO hier auch exceptions berücksichtigen

        # TODO kontext beachten, nächstes Wort, token selbst betrachten, enthält es entitäten
        # TODO Chat gpt
        # startet mit Buchstabe und hat am ende zahl ? Splitten von Trennzeichen
        # todo alle sonderzeichen
        if isinstance(token, float):  #nan value exception
            print(token)
            import sys
            sys.exit()

        # TODO Semntaic rückgabe
        # regex rückgabe

        if '-' in token:  # S7-XXX: 1560
            token_seperated = token.split('-')
            # todo semantic_location
            # Falls ein Minus enthalten ist, kombiniere Buchstaben und Zahlen wie 'S7' und '300'
            components = re.findall(r'[A-Za-z]+\d+|\d+', token_seperated[0])

            # TODO hier muss nach bindestrich die zweite co
        else:  # SIMATIC S7 PLCSIM Advanced -> Software
            together = True
            # Falls kein Minus enthalten ist, trenne Buchstaben und Zahlen einzeln
            # vielleicht haben einzelne buchstaben innerhalb ABC auch sematinsche bedeutung -> muster
            components = re.findall(r'[A-Za-z]+|\d+', token)

            #if token1.startswith('PC'):
            #    pass
            #    print(token2)
            #    import sys
            #    sys.exit()
        import sys
        sys.exit()

        if len(components) > 0:
            # S => S7 PLCSIM Advanced
            if len(str(components[0]).strip()) == 1:
                # print(product_name)
                return [token]  #TODO kann auch länger sein als 2 Charakters
            return [components[0]]
        else:
            return []

    # kann für beide genutzt werden, corpus und eingabe
    def extract_entities(self, csaf):
        # alle entiäten wie swtich pc usw.
        # kennzeichnen
        # kann aber auch model sein.
        # IM Interface Modul
        # synonyme
        pass

    def cluster_product_types(self, vendor='Siemens', filtered_data=None):
        if filtered_data is None:
            vendor_filtered = self.search_strings_df[self.search_strings_df['vendor'].str.startswith('Siemens')]
        else:
            vendor_filtered = filtered_data
        # TODO Series ermitteln, Subseries spielt keine rolle
        # vendor_filtered['product_name'] = vendor_filtered['product_name'].apply(self.remove_subseries)
        # vendor_filtered['product_name_cleaned'] = vendor_filtered['product_name'].apply(self.pre_cleaning)
        # vendor_filtered['product_name_additol_info'] = vendor_filtered['product_name'].apply(self.pre_cleaning) # TODO hier klammer werte rausholen, entities, incl. etc, syntaktisch

        # ---------------------
        # remediations
        # info ob software oder hardware
        # Hardware bezogene seltener explizite Versionsangaben
        # firmware update

        # häufigste wörter tabelle

        # SIMATIC -> 500

        # Sätze mit SIMATIC


        #TODO wieder nachzählen, rausfiltern



        # folgewörter wie häufig


        # TODO auslagern
        # Brand ermitteln -----
        # Hersteller aus Produktnamen entfernen
        vendor_filtered_origin = vendor_filtered.copy()
        # vendor_filtered['product_name_brand'] =  vendor_filtered['product_name'].apply(lambda x: self.trim_vendor(x, 'siemens'))
        # vendor_filtered['product_name_brand_erstes_wort'] = vendor_filtered['product_name_brand'].str.split().str[0]
        # first_word_counts = vendor_filtered['product_name_brand_erstes_wort'].value_counts()
        # print(first_word_counts)

        # SIMATIC ET Series
        # filtered_df = vendor_filtered_origin[
        #    vendor_filtered_origin['product_name'].str.contains(r'^SIMATIC E', case=False, na=False) &
        #    ~vendor_filtered_origin['product_name'].str.contains(r'SIMATIC ET', case=False, na=False)]
        # SIMATIC Series
        vendor_filtered = vendor_filtered[
            vendor_filtered_origin['product_name'].str.contains(r'^SIMATIC', case=False, na=False)]
        vendor_filtered['product_name'] = vendor_filtered['product_name'].apply(
            lambda x: self.trim_vendor(x, 'simatic'))

        frequency = self.get_token_frequency(vendor_filtered, 0, neighbours=3)

        # Roles Entitys zuweisen ->
        # CFU 12
        # CFU(Compact Field Unit): nicht gefunden, ABER:

        # RTU 24 Einträge -> GIBT ES IN C:\Users\itsic\OneDrive\PycharmProjects\Masterarbeit\3_BSI_Repos_Netbox und Plugin\DDDC-Netbox-plugin\plugins\d3c\data\repo\device-roles\RTU_PLC.yaml
        # Reader -> kann folgewörter enthalten die sagen was für reader -> für device role

        # TODO wörter finden die in jeder Markte auftauchen

        # todo all words -> entitys finden -> Software, Controller -> nachbarwörter -> CPU
        # immer paar weiße betrachen, maximal 3 wörter nebeneinander
        print(frequency)
        # "name": "SIMATIC Industrial PCs"
        # "name": "SIMATIC Industrial PCs"

        # filter Software -> rausfiltern
        # filter family -> rausfiltern

        # formel, gewichtung position, und typ der entiät
        # stoppwörter and usw. hinweis das keine Kategorie
        # filter

        # Folgewort für S7 betrachten da hier kein S7-XXX vorkommt

        # TODO Generation, Wort
        # TODO danach rausfiltern und nächst häufisgste wort von übrigen suchen -> bezug ob es auch bei anderen modellen vorkommt ist wichtig -> aber wird getrennt nach simatic
        #print(filtered_df)
        # split_tokens = [self.split_token_generic_series(token) for token in filtered_df['product_name_series_1nd_word'].tolist()]
        # split_tokens = [self.split_token_generic_series(token) for token in filtered_df['product_name_series_2nd_word'].tolist()]
        # Tokenzerlegung
        # flat_list = [sublist[0] for sublist in split_tokens for component in sublist]

        # 4642   Siemens  SIMATIC ITC1500 V3.1 PRO
        # 4940   Siemens      RUGGEDCOM ROX RX1500

        # Ausreiser nachschauen von original menge
        # filtered_ausreiser = vendor_filtered_origin[vendor_filtered_origin['product_name'].str.contains('INTRALOG', case=False, na=False)]
        # filtered_ausreiser = vendor_filtered_origin[vendor_filtered_origin['product_name'].str.contains('S7', case=False, na=False)]
        # print(filtered_ausreiser['product_name'].tolist())

        # 'SIMATIC ET200ecoPN,

        # family entfernen
        # 'SIMATIC S7 CPU family (incl. related ET200 CPUs and SIPLUS variants)'

        # Software - bezogene
        # Schlüsselwörter: "Software", "Application", "App", "Service", "System", "Tool", "Framework", "Platform".

        # clustering nach brand -> product typ
        # hersteller strippen
        # 1. wort = brand -> set anlegen bei bestimmter häufigkeit

        # products = filtered_df['product_name_series']
        return
        # Text zu Vektoren konvertieren
        vectorizer = TfidfVectorizer(stop_words='english')
        X = vectorizer.fit_transform(products)

        # SIMATIC S7-400 CPU
        dbscan = DBSCAN(eps=0.5, min_samples=2)
        dbscan.fit(X)
        # Cluster-Zuweisungen
        labels = dbscan.labels_

        # TODO Quelle Abschnitt ChatGPT
        # Produkte nach Cluster trennen
        clustered_data = {}
        for label, product in zip(labels, products):
            # if label == -1:
            #    continue  # Ignoriere Outlier
            if label not in clustered_data:
                clustered_data[label] = []
            clustered_data[label].append(product.split())
        # TODO Quelle Abschnitt ChatGPT
        sentences_per_cluster = {label: self.find_ordered_common_sequence(products) for label, products in
                                 clustered_data.items()}
        print(sentences_per_cluster)
        print(len(sentences_per_cluster))

    def get_token_frequency(self, data: pandas.DataFrame, n, neighbours=1):
        # TODO outliner -> length = 1 wie z.B. S
        # filter software step and family
        # TODO was filter man noch raus für produkte die als Ziel kategorien verwendet werden -> das filtern muss später aber auch für
        # TODO case insensitive einstellen
        # Synonyme von Software -> Process ? SIMATIC Process Historian ist eine Softwarelösung
        data = self.find_corpus_product_type(custom_corpus=data, search_terms=None,
                                             blacklist=['family', 'software', 'Software', 'Process'])

        flat_list = []
        produkt_name_tokens = data['product_name'].str.split()
        # data['annotation_product_name'] = []
        index = 0
        for tokens in produkt_name_tokens:
            #data['product_name_series_'+i+'_word'] = produkt_name_tokens.str[i]
            #token_list.append(data['product_name_series_'+i+'_word'].tolist())
            #token_list.append(data['product_name'])
            #flattened_list = list(zip(*token_list))
            # tokens: list [word1, word2]
            data = self.fill_nan(replace='', corpus=data)
            split_tokens = self.split_token_generic_series(corp=data, nr=index, semantic_location=True)

            current_flat_list = [sublist for sublist in split_tokens for component in sublist]
            flat_list.extend(current_flat_list)
            index = index + 1

        # Komponente (Drive Controller) -> kategorie wie erkennen ? -> Drive Controller CPU 1504D TF (6ES7615-4DF10-0AB0) ->hinweise in klammer, cpu nummer enthalten, herstellerspezifisch
        # Alle komponentne
        # flat_list = [component for sublist in split_tokens for component in sublist]
        df = pd.DataFrame(flat_list, columns=['Component'])
        # Zählen der Häufigkeit jeder Komponente
        frequency = df['Component'].value_counts()
        return frequency

    # def neighbours_token(self, token1, token2):

    # TODO chat gpt
    def remove_subseries(self, value: str):
        # if 'S7' in product_name:
        # print(product_name)
        # print(re.sub(r'\b([A-Z0-9]+?)-\d+\b', r'\1', product_name).strip())
        # import sys
        # sys.exit()
        return re.sub(r'\b([A-Z0-9]+)-\d+\b', r'\1', value).strip()

    def pre_cleaning(self, value):
        if 'S7' in value and '(' in value:
            print(value)
            print(re.sub(r'\s*\(.*?\)', '', value).strip())
        # TODO remove all mit klammern
        return re.sub(r'\s*\(.*?\)', '', value).strip()

    # Corpus Class
    # modell - Initial
    # precleaning operation
    # feature extracted
    # -> persist in Datenbank

    # 1. DataFrame
    # ClusterID hinzufügen
    # Brand Spalte
    # Version Spalte

    # pandas datenstrutkur zweites pandas datenframe
    # Spalte - id zu product_name verlinkung
    # Spalte - cluster_id zu verlinkung
    # Spalte - feature_attribut
    # Spalte - feature_wert

    # GeForce ist brand
    def extract_feature_brand(self, vendor='Siemens'):
        # 'SIMATIC'
        #
        pass

    #Serie (RTX):
    def extract_feature_series(self, vendor='Siemens'):
        # 'SIMATIC MV560'
        #
        pass

    # Optionals
    # Unterserie (3070)
    def extract_feature_sub_series(self, vendor='Siemens'):
        pass

    # Der Produkttyp-Name umfasst die Bezeichnung, die spezifisch genug ist, um das Modell innerhalb der Produktfamilie zu identifizieren, aber nicht den Hersteller.
    # Der Produkttyp-Name „RTX 3070“ ist damit die Kombination aus der Serienbezeichnung „RTX“ und der Unterserie „3070“, was dieses Modell eindeutig identifiziert.
    def extract_feature_modell_type(self, vendor='Siemens'):

        pass

    def extract_version(self, vendor='Siemens'):
        # TODO regex vorlage in json
        pass

    def extract_hardware_features(self, vendor='Siemens'):
        pass

    def extract_additional_features(self, vendor='Siemens'):
        # TODO synoynmsuche
        pass

    # TODO function Quelle: ChatGPT!!!
    # Funktion zur Bestimmung der geordneten Schnittmenge mit bis zu zwei Ausnahmen
    def find_ordered_common_sequence(self, products, max_exceptions=2):
        # Erstelle eine Liste der Positionen der Wörter
        word_positions = {}

        # Zähle die Positionen der Wörter
        for product in products:
            for idx, word in enumerate(product):
                if idx not in word_positions:
                    word_positions[idx] = []
                word_positions[idx].append(word)

        # Bestimme die häufigsten Wörter an jeder Position und erlaube bis zu max_exceptions
        common_sequence = []
        for pos in sorted(word_positions.keys()):
            word_count = Counter(word_positions[pos])
            most_common_words = [word for word, count in word_count.items() if len(products) - count <= max_exceptions]

            if most_common_words:
                # Nimm das häufigste Wort
                common_sequence.append(most_common_words[0])

        # Erstelle den finalen Satz aus der geordneten Schnittmenge
        return ' '.join(common_sequence)


if __name__ == "__main__":
    # NOTE: The following code provides examples on how to use the class above as well as testing it's functionality.
    sm = StringMiner()


    def test_all(target_string, vendor_filter="Siemens"):
        """
        This function tests various matching methods on a target string and prints the results.

        Args:
            target_string (str): The string to be tested.
            vendor_filter (str, optional): The vendor filter to be applied. Defaults to "Siemens".

        Prints:
            The function prints the results of three matching methods on the target string:
            - Normal RE: The result of a normal regex match with the vendor filter.
            - Fuzzy RE: The result of a fuzzy regex match with the vendor filter and maximum 1 error allowed.
            - Levenshtein: The result of a Levenshtein distance match with the vendor filter.
        """
        print(f"\nTesting: '{target_string}'")
        print("Normal RE  : ", sm.match(target_string, vendor_filter=vendor_filter))
        print("Fuzzy RE   : ", sm.match_fuzzy(target_string, vendor_filter=vendor_filter, max_errors=1))
        print("Levenshtein: ", sm.match_levenshtein(target_string, vendor_filter=vendor_filter))


    test_nmap = [
        "annotation: SIMATIC S7-1500                   6ES7 672-5DC01-0YA0      0 V  2  1  7\x00",
        "annotation: SIMATIC S7-1200                   6ES7 212-1AE40-0XB0      7 V  4  5  1\x00",
        "annotation: SIMATIC S7-1500                   6ES7 672-5DC01-0YA0      0 V2.1.7\x00",
        "annotation: SIMATIC S7-1200                   6ES7 212-1AE40-0XB0      7 V4.5.1\x00",
        "annotation: SIMATIC S7-1500                   6ES7 672-5DC01-0YA0      0 V 2.1.7\x00",
        "annotation: SIMATIC S7-1200                   6ES7 212-1AE40-0XB0      7 V 4.5.1\x00",
        "annotation: S7-1200                   6ES7 212-1AE40-0XB0      7 V  4  5  1\x00",
        "annotation: S7-1500                   6ES7 512-1DK01-0AB0      4 V  2  9  2\x00",
        "annotation: AXL F BK PN               2701815                  2 V  1  0  4\x00",
        "annotation: JVL-MOTOR                 MIS340C12EPH285          4 V  3 40 12\x00",
        "annotation: S7=1500                   6ES7672-5DC01-0YA0      0 V  2  1  7\x00",
        "annotation: S71200                   6ES7:212-1AE40-0XB0      7 V  4  5  1\x00",
        "annotation: S6-1200                   6ES7 212-1AE40-0XB0      7 V  4  5  1\x00",
        "annotation: S7-150                    6ES7 512-1DK01:0AB0      4 V  2  9  2\x00",
        "annotation: AXL F BK PN               2701815                  2 V  1  0  4\x00",
        "annotation: JVL-MOTOR                 MIS340C12EPH285          4 V  3 40 12\x00",
        "annotation: PlcNext Axc f 2152",
        "SIMATIC CP 1623 (6GK1162-3AA00)",
        "SIMATIC CP 1628 (6GK1162-8AA00)",
        "SIMATIC CP 1543-1 (6GK7543-1AX00-0XE0)",
        "SIMATIC MV540 H (6GF3540-0GE10)",
        "SIMATIC MV550 H (6GF3550-0GE10)",
        "SIMATIC MV560 U (6GF3560-0LE10)",
        "RUGGEDCOM RM1224 family (6GK6108-4AM00)"
    ]

    # ----------- default regex ----------- #
    print("\n# ----------- default regex ----------- #")
    for l in test_nmap:
        print(sm.match(l))

    # ----------- default regex only Siemens ----------- #
    print("\n# ----------- default regex only Siemens ----------- #")
    for l in test_nmap:
        print(sm.match(l, vendor_filter="Siemens"))

    # ----------- default regex only PhoenixContact ----------- #
    print("\n# ----------- default regex only PhoenixContact ----------- #")
    for l in test_nmap:
        print(sm.match(l, vendor_filter="Phoenix Contact"))

    # ----------- default regex stripping whitespaces + ignorecase ----------- #
    print("\n# ----------- default regex stripping whitespaces + ignorecase ----------- #")
    for l in test_nmap:
        print(sm.match(l, strip_target=True))

    # ----------- Tests with fuzzy regex ----------- #
    print("\n# ----------- Tests with fuzzy regex ----------- #")
    for l in test_nmap:
        print(sm.match_fuzzy(l, max_errors=1))

    # ----------- Tests with levenshtein distance ----------- #
    print("\n# ----------- Tests with levenshtein distance ----------- #")
    for l in test_nmap:
        print(sm.match_levenshtein(l, 0.8))

    # ----------- Tests with levenshtein distance only Siemens ----------- #
    print("\n# ----------- Tests with levenshtein distance ----------- #")
    for l in test_nmap:
        print(sm.match_levenshtein(l, threshold=0.85, vendor_filter="Siemens"))

    # ----------- Some manual test string provied by BSI ----------- #
    test_all("SSA-350757: Improper Access Control [...] Related ET200 CPUs and SIPLUS variants.")
    test_all("SSA-350757: Improper Access Control [...] Related ET 200 CPUs and SIPLUS variants.")
    test_all("SIMATIC CP 1623 (6GK1162-3AA00)")
    test_all("SIMATIC CP 1628 (6GK1162-8AA00)")
    test_all("SIMATIC CP 1543-1 (6GK7543-1AX00-0XE0)")
    test_all("SIMATIC MV540 H (6GF3540-0GE10)")
    test_all("SIMATIC MV550 H (6GF3550-0GE10)")
    test_all("SIMATIC MV560 U (6GF3560-0LE10)")
    test_all("RUGGEDCOM RM1224 family (6GK6108-4AM00)")

    # ----------- Tests with data from Siemens CSAF files ----------- #
    print("\n# Test StringChecker with data from Siemens CSAF files")
    test_all(
        "SIMATIC S7-400 CPU devices contain an input validation vulnerability that could allow an attacker to create a Denial-of-Service condition."
    )
    test_all(
        "A restart is needed to restore normal operations.\n\nSiemens has released an update for SIMATIC S7-410 V10 CPU family"
    )
    test_all("and SIMATIC S7-400 H V6 CPU family.")
    test_all("(incl. SIPLUS variants for both) and recommends to update to the latest version.")
    test_all("Affected models of the S7-1500 CPU product family do not contain an Immutable Root of Trust in Hardware.")
    test_all("Two vulnerabilities have been identified in the SIMATIC S7-400 CPU family.")
    test_all("Multiple Vulnerabilities in SCALANCE SC-600 Family before V3.0")
    test_all("Multiple vulnerabilities affecting various third-party components of the SCALANCE SC-600 family.")
    test_all(
        "SIMATIC S7-1500 CPUs and related products protect the built-in global private key in a way that cannot be considered sufficient any longer."
    )
    test_all(
        "SIMATIC S7-1200 CPUs and related products protect the built-in global private key in a way that cannot be considered sufficient any longer."
    )
    test_all("Vulnerabilities in Third-Party Component Mbed TLS of LOGO! CMR Family and SIMATIC RTU 3000 Family")
    test_all("Web Vulnerabilities in SCALANCE S-600 Family")
    test_all(
        "SIMATIC S7-400 CPU devices contain an input validation vulnerability that could allow an attacker to create a Denial-of-Service condition."
    )
    test_all(
        "A restart is needed to restore normal operations.\n\nSiemens has released an update for SIMATIC S7-410 V10 CPU family"
    )
    test_all("and SIMATIC S7-400 H V6 CPU family")
    test_all("(incl. SIPLUS variants for both)")
    test_all("Improper Access Control Vulnerability in TIA Portal Affecting S7-1200 and ... Web Server")
    test_all("Improper Access Control Vulnerability in TIA Portal Affecting ... and S7-1500 CPUs Web Server")
    test_all("(Incl. Related ET200 CPUs and SIPLUS variants)")
