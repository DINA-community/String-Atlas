from normalizer.semantics.semantics import Semantics
from normalizer.tree.visitor.database_visitor import DatabaseVisitor


class ProductNode:
    brand = False
    brand_name = None
    token = None
    level = None
    children = None
    group_parent = None
    parent_filter = None
    meta_info = None
    parent_node = None
    group_siblings = None
    group_characters:[] = None
    group_unique = None

    def __init__(self, token, level, brand_name=None, group_parent=None):
        self.brand_name = brand_name
        self.token = token
        self.level = level
        self.children = []
        self.group_parent = group_parent
        self.meta_info = {'children_groups_count': 0, 'types_before': [], 'annotations': [], 'group_id': None}
        self.group_counts = 0
        self.parent_filter = None
        self.group_siblings = {}
        self.group_characters:[] = None
        self.group_unique = None

    def set_group_unique(self, unique):
        self.group_unique = unique

    def get_group_unique(self):
        return str(self.group_unique)

    def set_group_siblings(self, group_siblings):
        self.group_siblings = group_siblings

    def set_group_characters(self, group_characters:[]):
        self.group_characters = group_characters

    def get_group_characters(self):
        return self.group_characters

    def get_group_siblings_token(self):
        return [sibling.get_token_value() for sibling in self.group_siblings]

    def get_parent(self):
        return self.parent_node

    def add_parent(self, parent_node):
        self.parent_node = parent_node

    def has_annotation(self, annotation_search):
        return annotation_search in self.meta_info['annotations']

    def is_brand_node(self):
        return self.brand_name is not None

    def get_full_meta_info(self):
        return self.meta_info

    def add_child(self, child):
        self.children.append(child)
        child.add_parent(self)

    def set_children(self, children):
        self.children = children

    def get_meta_info(self, key, default=None):
        if key in self.meta_info:
            return self.meta_info[key]
        return default

    def get_token(self):
        return self.token

    def get_token_value(self):
        return self.token['value']

    def is_member_of_group(self):
        return self.meta_info['group'] is True

    def set_children_groups_counts(self, group_count):
        self.meta_info['children_groups_count'] = group_count

    def get_children_group_counts(self):
        if 'children_groups_count' not in self.meta_info:
            raise ValueError
        return self.meta_info['children_groups_count']

    def get_group_parent(self):
        return self.group_parent

    def filter(self, parent_filter):
        self.parent_filter = parent_filter
        return self

    def get_children(self):
        return self.children

    def get_children_in_group(self) -> list:
        return [child for child in self.children if child.is_member_of_group()]

    def get_children_not_in_group(self):
        return [child for child in self.children if child.is_member_of_group() is False]

    def get_count_children(self):
        return len(self.children)

    def is_filtered(self, filter):
        if self.parent_filter is not None:
            for filter_item in self.parent_filter:
                if not self._match_filter_value(filter_item):
                    return True

        if filter is not None:
            for key, value in filter.items():
                if key in self.meta_info and self.meta_info[key] != value:
                    return True
        return False

    def _match_filter_value(self, filter_item):
        if 'type' in filter_item:
            type_match = filter_item['type']
            if type_match == self.get_meta_info('type'):
                if 'contains' in filter_item:
                    contains = filter_item['contains']
                    if isinstance(contains, list):
                        for value in contains:
                            if not value in self.get_token_value():
                                return False
                    else:
                        if not contains in self.get_token_value():
                            return False
        return True

    def _show_additional_info(self, show_meta_info: list):
        additional_info = ''
        if self.meta_info is not None:
            for key in show_meta_info:
                if key in self.meta_info:
                    if key == 'type':
                        value = self.meta_info[key][0]
                    else:
                        value = self.meta_info[key]
                    additional_info += str(value) + ' - '
        return additional_info.rstrip(' - ')

    def __repr__(self, level=0, show_meta_info=['type', 'group_len'], filter=None, parent_filter=None) -> str:

        #if parent_filter is not None:
        #    self.filter(parent_filter)

        #if self.is_filtered(filter):
        #    return ""  # have to be string

        additional_info = self._show_additional_info(show_meta_info)

        node_info = "\t" * self.level + repr(self.token['value']) + "[{}]".format(additional_info) + "\n"

        children_level = self.level + 1

        # TODO in group in nicht group splitten
        for child in self.get_children():
            node_info = node_info + "\t" * children_level + child.__repr__(children_level + 1,
                                                                           show_meta_info=['type', 'group_len',
                                                                                           'annotations'],
                                                                           parent_filter=self.parent_filter)

        return node_info


    # TODO strategy pattern
    def __repr2__(self, level=0, show_meta_info=['type', 'group_len'], filter=None, parent_filter=None) -> str:

        if parent_filter is not None:
            self.filter(parent_filter)

        if self.is_filtered(filter):
            return ""  # have to be string

        additional_info = self._show_additional_info(show_meta_info)

        node_info = "\t" * self.level + repr(self.token['value']) + "[{}]".format(additional_info) + "\n"

        # TODO hier filter für unterelemente, series_subsereis wird nicht weiter angezeigt

        parenthesis_bonus = 0
        if self.get_meta_info('type')[0] in Semantics.PARENTHESIS_LIST:
            parenthesis_bonus = 1

        children_level = self.level + 1

        # Gruppierte ausgeben und unterscheiden von unique
        if self.get_children_group_counts() > 0:
            node_info = node_info + "\t" * children_level + '==== Gruppe <start>' + "\n"
            for group_id in range(1, self.get_count_children() + 1):
                for child in self.get_children_in_group():
                    node_info += child.__repr__(children_level + 1, show_meta_info=['type', 'group_len', 'annotations'],
                                                filter={'group_id': group_id}, parent_filter=self.parent_filter)
            node_info = node_info + "\t" * children_level + '==== Gruppe <end>' + "\n"

        for child in self.get_children_not_in_group():
            node_info = node_info + "\t" * children_level + child.__repr__(children_level + 1, show_meta_info=['type', 'group_len', 'annotations'],
                                        parent_filter=self.parent_filter)

        return node_info


    def add_meta_info(self, meta_info):
        self.meta_info = self.merge_dicts(self.meta_info, meta_info)


    def merge_dicts(self, a, b):
        d = {}
        for key in a.keys() | b.keys():
            if key in a and key in b:
                if key == 'annotations':
                    d[key] = a[key] + b[key]
                if isinstance(a[key], list) and isinstance(b[key], list):
                    # Merge lists and remove duplicates
                    d[key] = b[key]
                else:
                    # If not a list, keep the value from dictionary 'b'
                    d[key] = b[key]
            elif key in a:
                d[key] = a[key]
            else:
                d[key] = b[key]
        return d

    # TODO interface visitor
    def accept(self, visitor: DatabaseVisitor):
        visitor.visit(self)
