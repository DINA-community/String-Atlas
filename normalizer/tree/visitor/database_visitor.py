import re
import json
from normalizer.database.csaf_database_helper import CSAFDataBaseHelper
from normalizer.tree.visitor.visitor import Visitor


class DatabaseVisitor(Visitor):
    token_list = None
    product_type_list = None
    product_type_regex_list = None
    structure = None
    string_m = None
    group_uuid = {}

    def __init__(self, database_helper:CSAFDataBaseHelper, vendor, brand):
        super().__init__(database_helper, vendor, brand)

        self.product_type_list = {}
        self.product_type_regex_list = {}
        self.token_list = {}
        self.structure = {'vendor': vendor, 'brand': brand, 'product_types': []}
        self.group_uuid = []
        from string_miner.string_miner import StringMiner
        self.string_m = StringMiner()

    def _save_group_regex_keys(self, product_type:str, token_value:str, token_segment_types:[], group_regex:[], token_regex:[],
                               group_uuid, types:[], annotations:[], whole_tokens:[], token_pos: int):
        short_type_index = self.database_helper.short_type_index(token_segment_types)

        # TODO key with brand
        token_key = ('regex_uuid:' + str(group_uuid) + '___' + 'regex_type:' + short_type_index + '___regex_detail_type:' + ',,'.join(group_regex)
        + '___regex_token:' + ',,'.join(token_regex)
        + '___vendor:' + self.vendor +'___product_type:' + product_type +'___token_value:' + token_value)
        # token_key = re.sub(r'[^a-zA-Z0-9\-:|]', '__', token_key)
        json_data = json.dumps({
            "vendor": self.vendor,
            "product_type": product_type,
            "types": types,
            "annotations": annotations,
            "short_type_index": short_type_index,
            "token_value": token_value,
            "group_regex": ',,'.join(group_regex),
            "token_regex": ',,'.join(token_regex),
            "token_segment_types": token_segment_types,
            "regex_uuid": str(group_uuid),
            "whole_tokens": whole_tokens,
            "token_pos": token_pos
        })
        self.database_helper.save_json_data(token_key, json_data)

    def visit(self, node):
        self.structure['product_types'] = []
        self._visit_children(node)
        self._save_product_type_keys()

    def _visit_children(self, node, parents_path=None):

        if parents_path is None:
            parents_path = []
        current_meta_info = node.get_full_meta_info()

        if node.is_member_of_group() and len(node.get_group_characters()):
            current_meta_info['group_regex'] = node.get_group_characters()
            current_meta_info['group_uuid'] = node.get_group_unique()
        elif 'group_regex' in current_meta_info:
            del(current_meta_info['group_regex'])

        full_path = parents_path + [(node.get_token(), current_meta_info)]

        if node.get_count_children() == 0:
            whole_tokens = []
            group_ids = []
            groups = []
            group_lengths = []
            annotations = []
            group_regexes = []
            last_meta_info = None
            for token, meta_info in full_path:
                # token is characterized dict from string miner
                token_value = token['value']
                whole_tokens.append(token_value)
                last_meta_info = meta_info

                if 'group_id' in meta_info:
                    group_ids.append(meta_info['group_id'])
                groups.append(meta_info['group'])
                if 'annotations' in meta_info:
                    meta_info_item_annotations = []
                    for item in meta_info['annotations']:
                        if isinstance(item, list):
                            meta_info_item_annotations.extend(item)
                        else:
                            meta_info_item_annotations.append(item)
                    annotations.append(meta_info_item_annotations)
                if 'group_len' in meta_info:
                    group_lengths.append(meta_info['group_len'])
                else:
                    group_lengths.append(None)
                if 'group_regex' in meta_info:
                    group_regexes.append(meta_info['group_regex'])
                else:
                    group_regexes.append(None)

            product_type = ' '.join(whole_tokens)

            last_meta_info['annotations'] = annotations

            last_meta_info['whole_tokens'] = whole_tokens
            last_meta_info['group_ids'] = group_ids
            last_meta_info['group'] = groups
            last_meta_info['group_len'] = group_lengths
            last_meta_info['group_regexes'] = group_regexes
            last_meta_info['vendor'] = self.structure['vendor']
            if "type" in last_meta_info.keys():
                del last_meta_info['type']
            if "children_groups_count" in last_meta_info.keys():
                del last_meta_info['children_groups_count']
            if "group_id" in last_meta_info.keys():
                del last_meta_info['group_id']

            if "types_before" in last_meta_info.keys():
                last_meta_info['types'] = last_meta_info['types_before']
                del last_meta_info['types_before']
            else:
                last_meta_info['types'] = []
            self.product_type_list[product_type] = last_meta_info

            pos = 0
            for token, meta_info in full_path:
                if 'group_regex' in meta_info and meta_info['group_regex'] is not None:

                    token_segment_types = token['segment_types']
                    group_uuid = meta_info['group_uuid']
                    short_type_index = self.database_helper.short_type_index(token_segment_types)
                    full_regex = token['full_regex']

                    own_character = group_uuid + ':' + ',,' + short_type_index + ':' + ',,'.join(full_regex)
                    if own_character not in self.group_uuid:
                        self.group_uuid.append(own_character)
                    else:
                        continue

                    token_value = token['value']

                    if full_regex not in self.product_type_regex_list:
                        self.product_type_regex_list[full_regex] = []
                    meta_info['token_regex_detail'] = self.string_m.characteristic_group([token, token])
                    meta_info['token_pos'] = pos
                    meta_info['types'] = last_meta_info['types']
                    meta_info['annotations'] = last_meta_info['annotations']
                    meta_info['whole_tokens'] = last_meta_info['whole_tokens']
                    meta_info['vendor'] = last_meta_info['vendor']
                    self.product_type_regex_list[full_regex].append((token_value, token_segment_types, product_type, meta_info))
                pos = pos + 1
            return []

        children_info = []
        for child in node.get_children():
            children_info.extend(self._visit_children(child, full_path))
        return children_info

    def _save_product_type_keys(self):
        for token_regex, regex_type_list in self.product_type_regex_list.items():
            for item in regex_type_list:
                token_value, token_segment_types, product_type, meta_info = item
                types = meta_info['types']
                annotations = meta_info['annotations']
                group_uuid = meta_info['group_uuid']
                group_regex = meta_info['group_regex']
                token_regex_detail = meta_info['token_regex_detail']
                whole_tokens = meta_info['whole_tokens']
                token_pos = meta_info['token_pos']

                # only unique regex patterns for same groups to save computing and database resources

                self._save_group_regex_keys(product_type, token_value, token_segment_types, group_regex, token_regex_detail,
                                            group_uuid, types, annotations, whole_tokens, token_pos)


        token_key_prefix = 'vendor:' + self.vendor + ',brand:' + self.brand
        token_key_without_brand_prefix = 'vendor:' + self.vendor + ',brand:' + self.brand
        for product_type, meta_info_list in self.product_type_list.items():

            current_token_key = token_key_prefix + ',product_type:' + product_type
            current_token_key_without_brand = token_key_without_brand_prefix + ',product_type:' + product_type

            # product type can contain special chars which describes features
            key = re.sub(r'[^a-zA-Z0-9\-:|]', '__', current_token_key)
            key_without_brand = re.sub(r'[^a-zA-Z0-9\-:|]', '__', current_token_key_without_brand)
            json_data = json.dumps({
                "vendor": self.vendor,
                "product_type": product_type,
                "meta_info": meta_info_list
            })
            self.database_helper.save_json_data(key, json_data)
            self.database_helper.save_json_data(key_without_brand, json_data)

    def get_structure(self):
        return self.structure
