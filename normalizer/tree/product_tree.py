from normalizer.database.csaf_database_helper import CSAFDataBaseHelper
from normalizer.tree.product_node import ProductNode
from normalizer.tree.visitor.database_visitor import DatabaseVisitor


# TODO sollte nicht im baum gelöst werden. nur dei Profeature extraktion
# n-gramme anschauen
class VendorProductTree:
    vendor = None
    brands = {}

    def save_product_type_and_regex(self, database_helper:CSAFDataBaseHelper):

        database_helper.create_product_type_index()
        database_helper.create_regex_product_type_index()
        database_helper.create_brand_index()
        database_helper.create_vendor_index()

        for brand in self.get_brands():
            brand_node = self.get_brand(brand)
            visitor = DatabaseVisitor(database_helper=database_helper, vendor=self.vendor, brand=brand)
            brand_node.accept(visitor)

    def __init__(self, vendor):
        self.vendor = vendor
        self.brands = {}

    def get_flat_list(self, node: ProductNode, parent_tokens=None):
        if parent_tokens is None:
            parent_tokens = []

        current_path = parent_tokens + [node.get_token_value()]

        if node.get_count_children() == 0:
            return [current_path]

        all_products = []
        # Ansonsten rekursiv weiter durch die Kinder gehen und Pfade generieren
        for child_node in node.get_children():
            all_products.extend(self.get_flat_list(child_node, current_path))
        return all_products

    def get_token_type_list(self, node: ProductNode, parent_tokens=None):
        if parent_tokens is None:
            all_products = []
            parent_tokens = []

        current_path = parent_tokens + [node.get_token_value()]

        if node.get_count_children() == 0:
            return [current_path]

        all_products = []
        # Ansonsten rekursiv weiter durch die Kinder gehen und Pfade generieren
        for child_node in node.get_children():
            all_products.extend(self.get_token_type_list(child_node, current_path))
        return all_products

    def add_brand(self, character):
        brand_node = ProductNode(token=character, level=0, brand_name=character['value'])
        brand_node.add_meta_info(meta_info={'type': 'brand', 'group': False, 'group_id': 0, 'types_before': ['brand'], 'annotations': [[]]})
        self.brands[character['value']] = brand_node

    def get_vendor(self):
        return self.vendor

    def show_full_tree(self):
        for key in self.brands.keys():
            print(self.get_brand(key))

    def get_brand(self, brand) -> ProductNode:
        return self.brands[brand]

    def get_brands(self):
        return self.brands.keys()

    # occurrences
    def add_parsed_result(self, brand, last_node, next_token, level_gramm, pos_token_gramm, group_parent=None,
                          meta_info=None) -> ProductNode:

        if last_node is None:
            last_node = self.get_brand(brand)
        next_node = ProductNode(token=next_token, level=level_gramm,
                                brand_name=None, group_parent=group_parent)  # brand -> redundancy info

        if meta_info is not None:
            next_node.add_meta_info(meta_info=meta_info)
        last_node.add_child(next_node)
        return next_node

    def print_sub_tree(self, tokens, level=0, tree_obj=None):
        brand = tokens[0]
        last_token = len(tokens) - 1
        brand_dict = self.get_brand(brand)
        next_token = tokens[0:1]

        if level == 0:
            tree_obj = brand_dict[next_token]

        self.print_sub_tree(tokens[1:], level + 1, tree_obj)
