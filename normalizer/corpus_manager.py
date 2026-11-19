import json
import re
import pandas
import uuid

from matcher.initialise.clients import redis_client
from matcher.lib.lookup_table import redis_get_json
from normalizer.database.csaf_database_helper import CSAFDataBaseHelper
from normalizer.precleaner import PreCleaner
# TODO für Text Miner auslagern

# TODO remove later, just a test for comparing
from normalizer.semantics.semantics import *
from normalizer.tree.product_tree import VendorProductTree
from normalizer.tree.product_node import ProductNode
from normalizer.helper.dataframe_helper import DataFrameHelper
from string_miner.string_miner import StringMiner
from string_miner.string_miner_helper import StringMinerHelper
from string_miner.string_type import StringType


class CorpusManager:

    def __init__(self, config, corpus_data: pandas.DataFrame, string_miner:StringMiner=None):
        self.ngramm_index_by_vendor = {}
        self.config = config
        self.string_miner:StringMiner|None = string_miner
        self.corpus:DataFrameHelper = DataFrameHelper(corpus_data)
        self.product_trees:dict = {}
        self.csaf_vendors_extracted = {}
        self.legal_forms = StringMinerHelper.normalize_legal_entities(legal_entities_file_name=config['legal_entities_file_name'])
        with open(config['oui_lookup_file_name'], 'r', encoding='utf-8') as oui_file:
           self.oui_lookups = json.load(oui_file)
        self.oui_csaf_vendor_mapping:dict = {}


    def save_product_type_and_regex(self, database_helper: CSAFDataBaseHelper, regex:bool):
        for vendor in self.csaf_vendors_extracted:
            self.product_trees[vendor].save_product_type_and_regex(database_helper=database_helper, regex=regex)


    def bl_extract(self):
        self.pre_process_filter()
        self._bl_step_extract_csaf_vendors()

        # TODO CSAF_VENDOR_MAPPING MIT LERNOBJEKT das synonyme enthält
        if self.config['vendors_used'] !='All':
            vendors_used = list(set(self.config['vendors_used'].split(',')))
            self.csaf_vendors_extracted = {k: v for k, v in self.csaf_vendors_extracted.items()
                                           if k in vendors_used}
        for vendor in self.csaf_vendors_extracted:
            self._bl_step_extract_brands(vendor)


    def bl_extract_by_vendor(self, vendor):
        self._bl_step_extract_brands(vendor)


    def pre_process_filter(self):
        # TODO sysiphos auslagern
        # plural -> versions. stemming soll alle varianten abdecken, Modules, variants

        blacklist = ['family', 'process', 'and', 'for',
                     'all', 'versions', 'version', 'variants', 'or', 'first', '<', '>', '<=', '>=', 'series', 'relays', 'devices']
        blacklist = []

        corpus = self.corpus.filter_corpus_column(store_key_src=DataFrameHelper.DEFAULT_STORE_KEY,
                                                  store_key_tgt=DataFrameHelper.DEFAULT_STORE_KEY,
                                                  columns=['product_name'], search_terms=None, blacklist=blacklist)

        corpus.loc[:, 'product_name'] = corpus.loc[:, 'product_name'].astype(str)
        corpus.loc[:, 'product_name'] = corpus.loc[:, 'product_name'].str.rstrip('.,:')
        corpus.loc[:, 'product_name'] = corpus.loc[:, 'product_name'].apply(lambda x: StringMinerHelper.clean_parentheses(x) if x is not None else x)
        self.corpus.raw_save(DataFrameHelper.DEFAULT_STORE_KEY, corpus)


    def save_vendors_and_brands(self, database_helper: CSAFDataBaseHelper):
        database_helper.create_vendor_index()
        for vendor, vendor_data in self.csaf_vendors_extracted.items():
            key_vendor = 'vendor__'+vendor
            key_vendor = re.sub(r'[^a-zA-Z0-9\-:|]', '__', key_vendor)
            json_data = json.dumps(vendor_data)
            database_helper.save_json_data(key=key_vendor, json_value=json_data)

            for brand in vendor_data['brands']:
                key_brand = key_vendor+'brand__'+brand
                brand_data = {
                    'vendor_csaf_normalized': vendor,
                    'brand_csaf_normalized': brand,
                    # for approach in future to improve normalization
                    'brands_similar_learned': []
                }
                database_helper.save_json_data(key=key_brand, json_value=json.dumps(brand_data))


    def save_oui(self, database_helper: CSAFDataBaseHelper):
        database_helper.create_oui_index()
        for oui, vendor_data in self.oui_csaf_vendor_mapping.items():
            key = 'oui__'+oui.replace(':', '_')
            json_data = json.dumps(vendor_data)
            database_helper.save_json_data(key=key, json_value=json_data)


    def _bl_step_extract_csaf_vendors(self):
        df = self.corpus.raw_load(DataFrameHelper.DEFAULT_STORE_KEY)
        df['vendor'] = df['vendor'].apply(PreCleaner.pre_filter_csaf_vendors)
        self.corpus.raw_save(DataFrameHelper.DEFAULT_STORE_KEY, df)
        csaf_vendors = list(set(df['vendor'].dropna().unique().tolist()))
        csaf_vendors_check = csaf_vendors.copy()
        for csaf_vendor in csaf_vendors:
            if csaf_vendor in csaf_vendors_check:
                csaf_vendors_check.remove(csaf_vendor)
                similar_vendors = StringMinerHelper.find_similar_vendors(csaf_vendor, csaf_vendors_check)
                similar_vendors.append(csaf_vendor)
                csaf_vendors_check = list(set(csaf_vendors_check) - set(similar_vendors))
                normalized_vendor = self._normalize_csaf_vendors(similar_vendors)
                self.csaf_vendors_extracted[normalized_vendor] = {'vendor_csaf_normalized': normalized_vendor,
                                                                  'vendors_similar_csaf': similar_vendors,
                                                                  'vendors_similar_oui': [],
                                                                  'vendors_similar_all': similar_vendors,
                                                                  'brands': []}
        self._append_vendor_from_oui()


    def _normalize_csaf_vendors(self, similar_vendors):
        if len(similar_vendors) > 1:
            # pre_filter disturb
            filtered_vendors = [vendor for vendor in similar_vendors if ',' not in vendor]
            if len(filtered_vendors) == 1:
                return filtered_vendors[0]
            elif len(filtered_vendors) == 0:
                return self._normalize_vendor_in_corpus_context(similar_vendors)
            elif len(filtered_vendors) > 1:
                return self._normalize_vendor_in_corpus_context(filtered_vendors)
        else:
            return similar_vendors[0]


    def _normalize_vendor_in_corpus_context(self, vendors: []):
        df = self.corpus.raw_load(DataFrameHelper.DEFAULT_STORE_KEY)
        match_searching = vendors
        match_searching.extend([StringMinerHelper.remove_all_suffix_variants(item, self.legal_forms) for item in vendors])
        match_searching.extend([StringMinerHelper.clean_parentheses(item).strip() for item in vendors])
        match_searching.extend([item.lower() for item in vendors])
        match_searching.extend([item.upper() for item in vendors])
        match_searching.extend([item.lower().capitalize() for item in vendors])

        high_score = 0
        high_word = None
        high_score_detailed = 0
        high_word_detailed = None
        for search_vendor in match_searching:
            count = df['vendor'].str.contains(search_vendor, case=False, na=False, regex=False).sum()
            count_detailed = df['vendor'].str.contains(search_vendor, case=True, na=False, regex=False).sum()
            if count > high_score:
                high_score = count
                high_word = search_vendor
            if count_detailed > high_score_detailed:
                high_score_detailed = count_detailed
                high_word_detailed = search_vendor

        if high_word_detailed is None:
            return vendors[0]
        return high_word_detailed


    def _append_vendor_from_oui(self):
        oui_lookup, oui_lookup_without_legal_forms = (
            StringMinerHelper.normalize_oui_lookup(oui_lookups=self.oui_lookups, strip_legal_forms=self.legal_forms))

        vendors = list(set(oui_lookup_without_legal_forms.values()))
        vendors = [vendor for vendor in vendors if vendor.strip() != '']
        vendors_check = vendors.copy()
        for oui_vendor in vendors:
            if oui_vendor in vendors_check:
                vendors_check.remove(oui_vendor)
                try:
                    similar = StringMinerHelper.find_similar_vendors(oui_vendor, vendors_check)
                    similar.append(oui_vendor)
                    vendors_check = list(set(vendors_check) - set(similar))
                except AttributeError:
                    print("Error with oui vendor")
                    print(oui_vendor)
                    similar = []

                found = False
                for csaf_vendor, csaf_group in self.csaf_vendors_extracted.items():
                    if not found:
                        try:
                            similar_oui_vendors = StringMinerHelper.find_similar_vendors(csaf_vendor, similar)
                            if len(similar_oui_vendors) > 0:
                                found = True
                                if 'similar_oui_without_legal' not in self.csaf_vendors_extracted[csaf_vendor]:
                                    self.csaf_vendors_extracted[csaf_vendor]['similar_oui_without_legal'] = []
                                if 'vendors_similar_oui' not in self.csaf_vendors_extracted[csaf_vendor]:
                                    self.csaf_vendors_extracted[csaf_vendor]['vendors_similar_oui'] = []
                                self.csaf_vendors_extracted[csaf_vendor]['similar_oui_without_legal'].extend(list(set(similar)))
                                self.csaf_vendors_extracted[csaf_vendor]['vendors_similar_all'] = (
                                    list(set(self.csaf_vendors_extracted[csaf_vendor]['vendors_similar_all'] + similar_oui_vendors + self.csaf_vendors_extracted[csaf_vendor]['similar_oui_without_legal'])))
                                similar_ouis = set()
                                for similar_vendor in similar:
                                    oui = next((k for k, v in oui_lookup_without_legal_forms.items() if v == similar_vendor), None)
                                    similar_ouis.add(self.oui_lookups[oui])

                                    self.oui_csaf_vendor_mapping[oui] = {'vendor_csaf_normalized': csaf_vendor,
                                                                         'vendor_oui': oui_lookup[oui],
                                                                         'vendor_without_legal_oui':oui_lookup_without_legal_forms[oui],
                                                                         'oui': oui,
                                                                         'oui_search': oui.replace(':', '').replace('-', '')
                                                                         }
                                self.csaf_vendors_extracted[csaf_vendor]['vendors_similar_oui'].extend(list(similar_ouis))
                                self.csaf_vendors_extracted[csaf_vendor]['vendors_similar_all'] = \
                                   list(set(self.csaf_vendors_extracted[csaf_vendor]['vendors_similar_all']
                                         + self.csaf_vendors_extracted[csaf_vendor]['vendors_similar_oui']))


                        except AttributeError:
                            print('Error with csaf vendor and matching OUI vendors')
                            print(csaf_vendor)
                            similar = []
        for oui, oui_vendor in self.oui_lookups.items():
            if oui in self.oui_csaf_vendor_mapping:
                for oui_compare, oui_vendor_compare in self.oui_lookups.items():
                    if oui == oui_compare:
                        continue
                    if oui_vendor == oui_vendor_compare:
                        self.oui_csaf_vendor_mapping[oui_compare] = self.oui_csaf_vendor_mapping[oui]
                        self.oui_csaf_vendor_mapping[oui_compare]['vendor_oui'] = oui_lookup[oui_compare]
                        self.oui_csaf_vendor_mapping[oui_compare]['vendor_without_legal_oui'] = oui_lookup_without_legal_forms[oui_compare]


    def _check_suspected_outliers_token(self, suspected_outliers: dict) -> []:
        """
        rules also based on vendor, so use custom strategy pattern if you need to recognize token
        """
        cleaned_outliers = []
        for token, outlier_character in suspected_outliers.items():
            changed = False
            cleaned_token = token
            outlier_character_clean = outlier_character
            if len(outlier_character['segment_types']) > 1 and outlier_character['segment_types'][
                -1] == StringType.TYPE_SPECIAL:
                changed = True
                cleaned_token = cleaned_token.rstrip(outlier_character['segments'][-1][0])
            if changed:
                outlier_character_clean = self.string_miner.characterize(cleaned_token)
            cleaned_outliers.append(outlier_character_clean)
        return cleaned_outliers


    def create_n_gramm(self,text, vendor):
        tokens = text.split()
        if len(tokens) < 2:
            return []
        path = []
        for i in range(0, len(tokens) - 1):
            path_next = path.copy()
            path_next.append(tokens[i])

            following_token = tokens[i + 1]
            path_text = " ".join(path_next)
            if path_text not in self.ngramm_index_by_vendor[vendor]:
                self.ngramm_index_by_vendor[vendor][path_text] = []
            if following_token not in self.ngramm_index_by_vendor[vendor][path_text]:
                self.ngramm_index_by_vendor[vendor][path_text].append(following_token)
            path = path_next

        terminal_path_text = " ".join(tokens)
        if terminal_path_text not in self.ngramm_index_by_vendor[vendor]:
            self.ngramm_index_by_vendor[vendor][terminal_path_text] = []


    def create_ngramm_for_vendor(self, vendor, column:str):
        self.ngramm_index_by_vendor[vendor] = {}
        df_vendor = self.corpus.raw_load(vendor)
        df_vendor.loc[:, column].apply(lambda x: self.create_n_gramm(x, vendor))

    def _bl_step_extract_brands(self, vendor: str):
        print(f'extract brands from {vendor}')

        # TODO synonym group beachten, vendor sollte list sein
        vendor_filtered_df = self.corpus.init_vendor(DataFrameHelper.DEFAULT_STORE_KEY, vendor)
        self._filter_vendor_data(vendor=vendor)

        # TODO für Thesis wie ich auf die marken komme. formel, vorraussetzung, anzahl datensätze, updatemechanismus
        # TODO hybrid, brand kann im selben token auch die serie haben, man kann es auch als serie und unterserie sehen, kein festes format
        # 1. Ansatz, wörter kommen am häufigsten vor, sind am anfang des satzes und haben die häufigste varianten mit anderen -> 2. wort ist gleich group

        first_word_by_vendor = set(vendor_filtered_df['product_name'].str.split().str[0].tolist())
        first_two_words_by_vendor = vendor_filtered_df['product_name'].apply(
            lambda x: StringMinerHelper.extract_n_words_as_list(x, 2)).dropna().tolist()

        # Gewichtung durch anzahl wörter
        # TODO die gruppierung und splittung in unqiue raus
        # two_ngramm_words = [words[0] for words in self.temp_result[1] if words[0] in first_two_words_by_vendor]
        groups, unique = self.string_miner.group_token(list(set(first_word_by_vendor)))

        possible_brands = unique

        vendor_tree = VendorProductTree(vendor)
        for possible_brand in possible_brands:
            next_forced_words = set([words[1] for words in first_two_words_by_vendor if words[0] == possible_brand])
            vendor_tree.add_brand(self.string_miner.characterize(possible_brand))
            self._bl_step_extract_series(vendor_tree, possible_brand, next_forced_words)

        self.csaf_vendors_extracted[vendor]['brands'] = list(possible_brands.keys())

        print(f'VENDOR finished: {vendor} ---------------------------------------------------------')
        #vendor_tree.show_full_tree()
        self.product_trees[vendor] = vendor_tree


    def _filter_vendor_data(self, vendor):
        df_vendor = self.corpus.raw_load(store_key_src=vendor)
        df_vendor['product_name'] = df_vendor['product_name'].apply(
            lambda x : StringMinerHelper.remove_all_prefix_variants(x,
                        self.csaf_vendors_extracted[vendor]['vendors_similar_csaf']))
        self.corpus.raw_save(vendor, df_vendor)


    def justify_groups(self, groups: list, outliner: list):
        """
        groups: list with items
        """
        groups_justifiy = []
        for group in groups:
            group_justified = {}
            group_len = len(group)
            pos = 0
            compare_pos = None
            item_justify = None
            item_compare = None
            for key, item in group.items():
                if key in outliner:
                    if pos < group_len - 1:  # not last element
                        compare_pos = pos + 1
                    else:
                        compare_pos = pos - 1
                    item_justify = item
                    break
                else:
                    group_justified[key] = item
                pos = pos + 1
            if compare_pos is not None:
                pos = 0
                for key, item in group.items():
                    if pos == compare_pos:
                        item_compare = item
                        break
                    pos = pos + 1
                # TODO von Annotation abhängig
                # Use cases bei token matcher
                # groß klein schreibung -> als default hier genommen um zu testen, wird dann ausgelagert und erweitert
                item_justify['value'] = item_compare['value']
                if item_justify['value'] == item_justify['value'].lower():
                    group_justified[item_compare['value']] = item_compare
                else:
                    group_justified[item_justify['value']] = item_justify
            groups_justifiy.append(group_justified)
        return groups_justifiy


    def _cached_vendor_n_gramm_index(self, vendor: str):
        if vendor not in self.ngramm_index_by_vendor or self.ngramm_index_by_vendor[vendor] is None:
            self.create_ngramm_for_vendor(vendor, 'product_name')


    def _bl_step_extract_series(self, tree: VendorProductTree, brand, next_forced_words):
        self._cached_vendor_n_gramm_index(tree.get_vendor())
        self._bl_step_extract_series_recursive(tree, brand, next_forced_words, next_token=None, next_meta_info={'annotations': []})


    # TODO Refactoring: funktionen auslagern
    # Es funktioniert bis jetzt Baum von Links nach Rechts auszuwerten, aber nicht wenn es zwischen SIMATIC CP 200 und SIMATIC CP pro 200 ein Zwischenwort gibt
    # das ist dann ein Unterzweig ab pro
    # hier müsste ich pro als Zusatz (Featuremerkmal) identifierieren
    # Prefix Baum ist gleich, sagen wir n-Worte, und Suffix ist gleich mit gleichen Tokenschema, bei der die Serie erkannt worden ist.
    # d.h. 2. durchlauf nach 1. annotation wird nochmal erkannt ob es nach serie kommt oder eine pro Serie ist und damit eine eigenständige
    def _bl_step_extract_series_recursive(self, vendor_tree: VendorProductTree, brand: str, next_forced_words:[]=None,
                                          next_token=None,
                                          last_node: ProductNode = None,
                                          level_gramm: int = 0, next_meta_info: dict = None, parse_only_one=False, parsed_group_node=None) -> ProductNode|None:

        is_root_brand = False
        # TODO experimental for feature groups
        if parsed_group_node:
            last_node = parsed_group_node
            next_token = parsed_group_node.get_token()
        elif next_token is None:
            is_root_brand = True
            # todo cache
            next_token = self.string_miner.characterize(brand)
            last_node = vendor_tree.get_brand(brand)
        elif next_token is not None:
                token_list = [last_node.get_token_value()] + [next_token['value']]
                search_text = " ".join(token_list)
                found = False
                for ngram_key in self.ngramm_index_by_vendor[vendor_tree.get_vendor()].keys():
                    if ngram_key.startswith(brand) and ngram_key.endswith(search_text):
                        found = True
                if not found:
                    return None

        next_token_value: str = next_token['value']
        pos_token_gramm = level_gramm  # das varriert, hier dritte gruppe.

        types_before_check = last_node.get_meta_info('types_before')

        if not parsed_group_node:
            # TODO cache
            token_type, annotations = self.string_miner.annotate_token(token=next_token, token_before=last_node, next_meta_info=next_meta_info)

            if annotations is None:
                annotations = []

            # TODO
            if token_type is not None:
                pass

            if 'annotations' not in next_meta_info or next_meta_info['annotations'] is None:
                next_meta_info['annotations'] = []
            next_meta_info['annotations'].extend(annotations)

        if is_root_brand or parsed_group_node:
            current_node = last_node
        else:
            current_node = vendor_tree.add_parsed_result(brand=brand, last_node=last_node, next_token=next_token,
                                                         level_gramm=level_gramm,
                                                         pos_token_gramm=pos_token_gramm, meta_info=next_meta_info)

        if parse_only_one:
            return current_node

        # last found group type
        pos_series_start, pos_series_end = SemanticsState.get_last_series_kind_state(types_before_check, state_searched=Semantics.TOKEN_SERIES_LIST)
        last_forced_words = []
        group_feature_token = []
        following_group_feature_token = []
        if pos_series_start is not None:

            next_forced_words = None
            last_found_type = types_before_check[-pos_series_start]

        brand_next_token = []
        if next_forced_words is not None:
            brand_next_token = list(set(next_forced_words))
        elif len(last_forced_words) > 0:
            token_list = [brand] + last_forced_words
            search_text = " ".join(token_list)
            if search_text in self.ngramm_index_by_vendor[vendor_tree.get_vendor()]:
                brand_next_token = self.ngramm_index_by_vendor[vendor_tree.get_vendor()][search_text]
            if len(brand_next_token) == 0:
                return None

        elif len(group_feature_token) > 0:
            for group_token in group_feature_token:
                group_with_following_token = [group_token]
                group_with_following_token.extend(following_group_feature_token)
                brand_next_token.extend(self._get_n_gramm_with_all_words(n=len(group_with_following_token) + 1, token_list=group_with_following_token))
        else:
            brand_next_token = []
            for ngram_key in self.ngramm_index_by_vendor[vendor_tree.get_vendor()].keys():
                if ngram_key.startswith(brand) and ngram_key.endswith(next_token_value) and ngram_key.count(" ") == level_gramm - 1:
                    brand_next_token.extend(self.ngramm_index_by_vendor[vendor_tree.get_vendor()][ngram_key])

        brand_next_token = list(set(brand_next_token))
        children_tokens = brand_next_token
        # Annotation stopword 'with' -> sysiphos

        # TODO Auslagern Token Matcher-------------
        # TODO NLP in TokenCharakterizer reinnehmen -> TokenMatcher verwendet diesen Datentyp
        # TODO composition patterm auch möglich in eigener Klasse TokenMatcher -> characterizing function auch
        # TODO einzelne character werden verschluckt DRINGEND

        # TODO wenn MEnge nur nur eins ist dann kein gruppen vergleich

        groups = []
        no_matches = {}
        if len(children_tokens) > 0:
            # TODO hier auch den vorherigen Typ bestimmen, klammern wenn serien usw. bestimmt sind sollten anders verglichen werden s. unten
            # TODO hier bereits annotieren und nicht weiter oben, da Vergleich besser ist wenn es eine Annoation gefunden wird
            groups, suspected_outliers_before = self.string_miner.group_token(children_tokens)
            if len(suspected_outliers_before) > 0:
                suspected_outliers = self._check_suspected_outliers_token(suspected_outliers_before)  #dicts characters as paramter, returns ? [dict]
                # TODO check length
                tokens_to_rematch = [key for group_dict in groups for key, character in group_dict.items()]
                tokens_to_rematch.extend(suspected_outliers)
                groups_2nd_match, no_matches = self.string_miner.group_token(tokens_to_rematch, case=False)

                # kann nicht nur nach groß und kleinschreibung gruppiert werden -> muss angepasst werden. wenn zum Beispiel nur klein geschrieben -> dann muss die character groß, wortfrequenz
                suspected_outliers_tokens = set([item['value'] for item in suspected_outliers])

                # hier dann trotzdem orginalwerte übergeben.
                #no_matches
                group_new = set([key for group in groups_2nd_match for key, next_token in group.items()])
                intersection_operator = suspected_outliers_tokens & group_new
                if len(intersection_operator) > 0:
                    # annotate not orignal data extraktion, and why its is after second time equal. Semantics verwenden als Konstante
                    # TODO Basic vs BASIC -> genauer definieren ob alles groß, char-weise
                    groups = self.justify_groups(groups_2nd_match, list(intersection_operator))

                # unique items
                difference_operator = suspected_outliers_tokens - group_new

        types_before = current_node.get_meta_info('types_before')

        # group able meaning next token
        group_id = 0
        group_nodes = {}
        group_nodes_all = {}
        for group in groups:
            group_id = group_id + 1
            group_nodes[group_id] = []
            group_nodes_all[group_id] = []
            for key, next_token in group.items():
                next_type_for_group = SemanticsState.predict_new_state(types_before, True)
                types_for_group = types_before.copy()
                types_for_group.extend(next_type_for_group)

                # connect group immediately as objects, further children token can access on siblings parents token
                #if next_type_for_group == [Semantics.TOKEN_FEATURE_GROUP]:
                #    parse_only_one = True
                #else:
                parse_only_one = False
                group_node = self._bl_step_extract_series_recursive(vendor_tree, brand, next_forced_words=next_forced_words,
                                                   next_token=next_token, last_node=current_node, parse_only_one=parse_only_one,
                                                   level_gramm=level_gramm + 1,
                                                   next_meta_info={'type': next_type_for_group, 'group': True,
                                                                   'group_len': len(group), 'group_id': group_id,
                                                                   'types_before': types_for_group, 'annotations': []})

                if parse_only_one is True and group_node is not None:
                    group_nodes[group_id].append(group_node)

                if group_node is not None:
                    group_nodes_all[group_id].append(group_node) # without parsing recursive children

        for group_id, group_items in group_nodes_all.items():
            if len(group_items) > 0:
                unique_id = uuid.uuid4()
                group_characters = self.string_miner.characteristic_group([item.get_token() for item in group_items])
                for group_item in group_items:
                    group_item.set_group_characters(group_characters)
                    group_item.set_group_siblings(group_items)
                    group_item.set_group_unique(unique_id)

        #print("group_nodes")
        #print(group_nodes)
        for group_id, group_items in group_nodes.items():
            for group_item in group_items:
                # combine siblings also for series is useless though following feature groups cpu series are different
                # alle Varianten durchzählen, aber nicht imm n mal die gleiche sondern n - 1
                self._bl_step_extract_series_recursive(vendor_tree, brand, parsed_group_node=group_item,
                                                       parse_only_one=False, level_gramm=level_gramm + 1)

        # not group able meaning next token
        for key, next_token in no_matches.items():
            next_type_for_unique = SemanticsState.predict_new_state(types_before, False, next_token=next_token)
            types_for_unique = types_before.copy()
            types_for_unique.extend(next_type_for_unique)

            next_forced_words = None
            self._bl_step_extract_series_recursive(vendor_tree, brand, next_forced_words=next_forced_words,
                                                   next_token=next_token, last_node=current_node,
                                                   level_gramm=level_gramm + 1,
                                                   next_meta_info={'type': next_type_for_unique, 'group': False,
                                                                   'group_id': None, 'types_before': types_for_unique, 'annotations': []})
        current_node.set_children_groups_counts(len(groups))
        return current_node


    def after_cleanup(self):
        """
        TODO Extraktion der features und vergleich
        Liste der Produkte

        """
        values = []
        search_key_prefix = "L_E_PRODUCT:"
        keys = list(redis_client.scan_iter(match=search_key_prefix + "*", count=1000))
        keys = [key.decode("utf-8") if isinstance(key, bytes) else key for key in keys]
        for key in keys:
            value = redis_get_json(key)
            values.append(value)

        for vendor in self.product_trees.keys():
            df_vendor = self.corpus.raw_load(vendor)
            for value in values:
                pass

            print(f'after cleanup vendor: {vendor}')
            #self.product_trees[vendor].after_cleanup()
