import json
import re
from fuzzywuzzy import fuzz
import pandas
from fuzzywuzzy import fuzz, process
from rapidfuzz.distance.Levenshtein_py import similarity
from normalizer.semantics.semantics import Semantics


class StringMinerHelper:

    @staticmethod
    def extract_mac_normalized(text, oui=False):
        if oui is True:
            regex_mac = r'(?:[0-9a-fA-F]:?){6}'
        else:
            regex_mac = r'(?:[0-9a-fA-F]:?){12}'
        mac_parser = re.compile(regex_mac)
        matches = re.findall(mac_parser, text)
        if len(matches) > 0:
            return re.sub(r'[^0-9A-Fa-f]', ':', matches[0])
        regex_mac = r'(?:[0-9a-fA-F]-?){12}'
        mac_parser = re.compile(regex_mac)
        matches = re.findall(mac_parser, text)
        if len(matches) > 0:
            return re.sub(r'[^0-9A-Fa-f]', ':', matches[0])
        return None

    @staticmethod
    def extract_brand(match:dict):
        found = None
        for index, element in enumerate(match['types']):
            if element != Semantics.TOKEN_BRAND:
                found = index
                break
        return ' '.join(match['tokens'][0:found])

    @staticmethod
    def normalize_legal_entity(token):
        return token.replace("&", "").replace(".", "").replace(",", "").replace("(", "").replace(")", "").replace("-", "").replace("  ", " ")

    @staticmethod
    def normalize_legal_entities(legal_entities_file_name) -> []:
        with open(legal_entities_file_name, "r") as legal_entities_file:
            data = json.load(legal_entities_file)
            tokens = set()
            for country, entities in data.items():
                for entity in entities:
                    tokens.add(entity['short_form'])
                    tokens.add(entity['full_form'])
                    tokens.add(entity['short_form'].lower())
                    tokens.add(entity['short_form'].upper())
                    tokens.add(entity['full_form'].lower())
                    tokens.add(entity['full_form'].upper())
                    normalized_short_form = StringMinerHelper.normalize_legal_entity(entity['short_form'])
                    normalized_full_form = StringMinerHelper.normalize_legal_entity(entity['full_form'])
                    tokens.add(normalized_short_form)
                    tokens.add(normalized_full_form)
                    tokens.add(normalized_short_form.lower())
                    tokens.add(normalized_short_form.upper())
                    tokens.add(normalized_full_form.lower())
                    tokens.add(normalized_full_form.upper())
            return list(tokens)


    @staticmethod
    def normalize_oui_lookup(oui_lookups:dict, strip_legal_forms:[]) -> (dict, dict):
        """
        tuple with first element lookup oui -> vendor
        second element contains oui -> vendor without legal entities
        """
        oui_lookup_without_legal_forms = StringMinerHelper.strip_suffix_from_dict_values(oui_lookups, strip_legal_forms)
        return oui_lookups, oui_lookup_without_legal_forms

    @staticmethod
    def remove_all_suffix_variants(text:str, variants: []):
        text_to_strip: str = str(text)
        found = True
        while found:
            text_to_strip = text_to_strip.rstrip(',.')
            found = False
            for suffix in variants:
                if text_to_strip.lower().endswith(suffix.lower().rstrip(',.')):
                    text_to_strip = text_to_strip[:-len(suffix)].strip()
                    found = True
        return text_to_strip

    @staticmethod
    def remove_all_prefix_variants(text:str, variants: []):
        text_to_strip: str = str(text)
        found = True
        while found:
            text_to_strip = text_to_strip.lstrip(',.')
            found = False
            for prefix in variants:
                if text_to_strip.lower().startswith(prefix.lower().lstrip(',.')):
                    text_to_strip = text_to_strip[len(prefix):].strip()
                    found = True
        return text_to_strip

    @staticmethod
    def find_similar_vendors(target_vendor, vendors, threshold=70, threshold_first_word=80) -> []:
        """ used for csaf vendor """
        similar_vendors = []
        target_tokens = target_vendor.split()

        for vendor in vendors:
            if vendor.strip() == '':
                continue
            if target_vendor == vendor:
                continue

            vendor_tokens = vendor.split()

            if vendor_tokens[0].lower() != target_tokens[0].lower():
                continue

            if len(vendor_tokens) > len(target_tokens):
                longer = vendor
                len_longer = len(vendor_tokens)
                shorter = target_vendor
                len_shorter = len(target_tokens)

            else:
                len_longer = len(target_tokens)
                len_shorter = len(vendor_tokens)
                shorter = vendor
                longer = target_vendor

            longer = longer.lower()
            shorter = shorter.lower()

            if len_longer > 1 and len_shorter > 1:
                if longer.startswith(shorter):
                    similar_vendors.append(vendor)
                else:
                    score = fuzz.ratio(target_vendor, vendor)
                    if score >= threshold:
                        similar_vendors.append(vendor)
            elif len_longer > 1 and longer.startswith(shorter):
                similar_vendors.append(vendor)
            else:
                score_word = fuzz.ratio(longer, shorter)
                if score_word >= threshold_first_word:
                    similar_vendors.append(vendor)
        return similar_vendors

    @staticmethod
    def strip_suffix_from_dict_values(oui_items:dict, suffix_list:[]) -> dict:
        stripped_items = {}
        for oui, vendor in oui_items.items():
            vendor_to_strip = StringMinerHelper.remove_all_suffix_variants(vendor, suffix_list)
            stripped_items[oui] = vendor_to_strip.strip()
        return stripped_items

    @staticmethod
    def has_float_sequence(value) -> bool:
        version_regex = r'V?\d+(\.\d+)+'
        return re.match(version_regex, value) is not None

    @staticmethod
    def is_unique(token: dict, min_count:int = 5) -> bool:
        # TODO parameters in config and more complex alogrithmen
        if len(token['segment_types']) > min_count:
            return True
        return False

    # TODO stemming
    @staticmethod
    def is_plural(self, token):
        pass
        # Beispieltext
        # document = nlp(token)
        # Überprüfen, ob das Wort Plural ist
        #for token in document:
        #    if token.tag_ == 'NNS':  # Plural-Nomen
        #        return True
        # return False

    @staticmethod
    def remove_last_elements(list_to_modify, n):
        return list_to_modify[:-n] if n <= len(list_to_modify) else []

    @staticmethod
    def clean_parentheses(text):
        text = str(text)
        text = re.sub(r'\)+', ')', text)
        text = re.sub(r'\(+', '(', text)

        text = re.sub(r'\(', ' ( ', text)
        text = re.sub(r'\)', ' ) ', text)

        # remove empty parentheses
        text = re.sub(r'\(\s*\)', '', text)
        return text

    @staticmethod
    def extract_n_words_as_list(text, n):
        words = text.split()
        if len(words) < n:
            return None
        return words[:n]

    @staticmethod
    def generate_word_of_bags_variants(word_of_bag: list) -> []:
        words_of_bags_extended = word_of_bag
        words_of_bags_extended.extend([word.strip() for word in words_of_bags_extended])
        words_of_bags_extended.extend([word.lower() for word in word_of_bag])
        words_of_bags_extended.extend([word.upper() for word in word_of_bag])
        words_of_bags_extended.extend([word_split.lower() for word in word_of_bag for word_split in word.split() ])
        words_of_bags_extended.extend([word_split.upper() for word in word_of_bag for word_split in word.split() ])
        return words_of_bags_extended

    @staticmethod
    def remove_special_characters_from_word_of_bags(word_of_bag: list):
        return [re.sub(r'[^A-Za-z0-9]', ' ', word).strip() for word in word_of_bag]
