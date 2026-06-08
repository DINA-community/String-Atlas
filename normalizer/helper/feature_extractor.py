import json

from matcher.initialise.clients import redis_client
from matcher.lib.lookup_table import normalized_unique_token_key, redis_get_json
from string_miner.string_miner import StringMiner
from string_miner.string_miner_helper import StringMinerHelper


class FeatureExtractor:

    def __init__(self, string_miner: StringMiner):
        self.vendors = []
        self.string_miner = string_miner
        self.features = []
        self.features_dict = {}
        self.vendor_series_token = {}
        self.vendor_subseries_token = {}

        self.vendor_others_token_series = {}
        self.vendor_others_token_brand = {}
        self.vendor_others_token_global = []

        self.series_entity_index = {}

        self._init_series_token()

    def _init_series_token(self):
        search_key_prefix = "L_E_VENDOR:"
        keys = list(redis_client.scan_iter(match=search_key_prefix + "*", count=1000))
        keys = [key.decode("utf-8") if isinstance(key, bytes) else key for key in keys]
        for product_entity_key in keys:
            value = redis_get_json(product_entity_key)
            self.vendors.append(value['vendor'].lower())

        search_key_prefix = "L_E_PRODUCT:"
        keys = list(redis_client.scan_iter(match=search_key_prefix + "*", count=1000))
        keys = [key.decode("utf-8") if isinstance(key, bytes) else key for key in keys]
        for product_entity_key in keys:
            value = redis_get_json(product_entity_key)
            vendor = value['vendor'].lower()
            brand = value['brand'].lower()
            series = value['series'].lower()
            subseries = value['subseries'].lower()


            if vendor not in self.vendor_series_token:
                self.vendor_series_token[vendor] = set()
                self.vendor_subseries_token[vendor] = dict()

                self.vendor_others_token_series[vendor] = dict()
                self.vendor_others_token_brand[vendor] = dict()
                self.vendor_others_token_global = list()
                self.series_entity_index[vendor] = {}

            if subseries not in self.series_entity_index[vendor]:
                self.series_entity_index[vendor][subseries] = {}
            self.series_entity_index[vendor][subseries][brand] = product_entity_key


            self.vendor_series_token[vendor].update(vendor.split())
            self.vendor_series_token[vendor].update(brand.split())
            self.vendor_series_token[vendor].update(series.split())
            self.vendor_series_token[vendor].update(subseries.split())

            if subseries not in self.vendor_subseries_token[vendor]:
                self.vendor_subseries_token[vendor][subseries] = set()
            self.vendor_subseries_token[vendor][subseries].add(brand)

    def extract_features_from_text(self,  text:str, vendor:str):
        text = text.lower()
        if  vendor not in self.vendor_subseries_token:
            return
        for subseries, brands in self.vendor_subseries_token[vendor].items():
            if subseries not in text:
                continue

            for brand in brands:
                this_brand = True
                if len(brands) > 1:
                    count = 0
                    if brand not in text:
                        this_brand = False
                    else:
                        for brand_check in brands:
                            if brand_check in text:
                                count += 1
                        if count > 1:
                            this_brand = False

                other_words = [word for word in text.split() if word not in self.vendor_series_token[vendor]]
                for word in other_words:
                    if this_brand and word not in self.vendor_series_token[vendor]:
                        if subseries not in self.vendor_others_token_series[vendor]:
                            self.vendor_others_token_series[vendor][subseries] = {}
                        if brand not in self.vendor_others_token_brand[vendor]:
                            self.vendor_others_token_brand[vendor][brand] = []
                        if word not in self.vendor_others_token_brand[vendor][brand]:
                            self.vendor_others_token_brand[vendor][brand].append(word)
                        if brand not in self.vendor_others_token_series[vendor][subseries]:
                            self.vendor_others_token_series[vendor][subseries][brand] = []
                        if word not in self.vendor_others_token_series[vendor][subseries][brand]:
                            self.vendor_others_token_series[vendor][subseries][brand].append(word)


    def extract_features(self, df_filtered):
        for vendor in self.vendors:
            vendor_filtered_df = df_filtered.loc[
                df_filtered["vendor"].str.casefold() == vendor.casefold()
                ].copy()
            vendor_filtered_df.loc[:, 'product_name'].apply(lambda x: self.extract_features_from_text(x, vendor))

            if vendor not in self.vendor_others_token_series:
                continue

            for subseries, brands in self.vendor_others_token_series[vendor].items():
                same_brand_other_series_words = []
                same_vendor_other_brands_words = []
                other_vendors_other_words = []

                for brand, other_words in brands.items():
                    for subseries_compare, brands_compare in self.vendor_others_token_series[vendor].items():
                        if subseries == subseries_compare:
                            continue

                        for brand_compare, other_words_compare in brands_compare.items():
                            same_vendor_other_brands_words.extend(other_words_compare)
                            if brand == brand_compare:
                                same_brand_other_series_words.extend(other_words_compare)


                    for vendor_compare in self.vendors:
                        if vendor == vendor_compare:
                            continue
                        if vendor_compare not in self.vendor_others_token_series:
                            continue
                        for subseries_compare, brands_compare in self.vendor_others_token_series[vendor_compare].items():
                            if subseries == subseries_compare:
                                continue
                            for brand_compare, other_words_compare in brands_compare.items():
                                other_vendors_other_words.extend(other_words_compare)


                    for word in other_words:
                        score = 100
                        # todo config parameters
                        if word in same_brand_other_series_words:
                            score -= 20
                        if word in same_vendor_other_brands_words:
                            score -= 25
                        if word in other_vendors_other_words:
                            score -= 55

                        if score == 100:
                            token = self.string_miner.characterize(word)
                            if StringMinerHelper.is_unique(token,min_count=2):
                                #print(f"brand {brand} subseries {subseries} word: {word}")
                                key_token_unique = normalized_unique_token_key(word)
                                product_entity_key = self.series_entity_index[vendor][subseries][brand]
                                #print(key_token_unique)
                                redis_client.set(key_token_unique, json.dumps([product_entity_key]))
