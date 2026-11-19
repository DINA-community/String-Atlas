from matcher.lib.lookup_table import (
    create_product_lookup_tables,
    create_vendor_and_brand_lookup_tables,
    cleanup_brands_and_producttypes_in_lookup_tables, create_functional_words_and_placeholders_lookup_tables,
    cleanup_general_producttypes_in_lookup_tables
)
from normalizer.database.redis_client_helper import (get_all_keys,load_documents,extract_rows_product_type,
                                                     extract_rows_vendor_and_brand,group_and_count)

keys_product_type = list(dict.fromkeys(
    get_all_keys("*product__type*") +
    get_all_keys("*product_type*")
))

documents_product_type = load_documents(keys_product_type)
rows_product_type = extract_rows_product_type(documents_product_type)
grouped_product_type = group_and_count(rows_product_type)

keys_vendor_and_brand = get_all_keys("vendor__*")
documents_vendor_and_brand = load_documents(keys_vendor_and_brand)
rows_vendor_and_brand = extract_rows_vendor_and_brand(documents_vendor_and_brand)
grouped_vendor_and_brand = group_and_count(rows_vendor_and_brand)

print("Matcher - Lookup Tables - Redis - Placeholder - Start")
create_functional_words_and_placeholders_lookup_tables()
print("Matcher - Lookup Tables - Redis - Placeholder - Done")
print("Matcher - Lookup Tables - Redis - Vendor and Brands - Start")
create_vendor_and_brand_lookup_tables(grouped_vendor_and_brand)
print("Matcher - Lookup Tables - Redis - Vendor and Brands - Done")
print("Matcher - Lookup Tables - Redis - Product Types - Start")
create_product_lookup_tables(grouped_product_type)
print("Matcher - Lookup Tables - Redis - Product Types - Done")
print("Matcher - Lookup Tables - Redis - Cleaning Brands - Start")
cleanup_brands_and_producttypes_in_lookup_tables()
print("Matcher - Lookup Tables - Redis - Cleaning Brands - Done")
print("Matcher - Lookup Tables - Redis - Cleaning Products - Start")
cleanup_general_producttypes_in_lookup_tables()
print("Matcher - Lookup Tables - Redis - Cleaning Products - Done")
# TODO cleanup placesholders in product and vendors for space saving
