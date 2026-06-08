import os
import pandas
import pandas as pd
import process_csaf_files
from normalizer.precleaner import PreCleaner

CSAF_FOLDERS: str = os.getenv('CSAF_FOLDERS', 'All')
CSAF_PATH = os.getenv('CSAF')
if CSAF_PATH is None or CSAF_PATH.strip() == '':
    raise ValueError('CSAF environment variable not set')

if CSAF_FOLDERS == 'All':
    allowed_folders = None
else:
    allowed_folders = process_csaf_files.create_folders_set(CSAF_FOLDERS)

df_all = process_csaf_files.get_csaf_sources(CSAF_PATH, allowed_folders=allowed_folders)

product_set = set()
manufacturer = set()
merged_df = pd.DataFrame({
    'vendor': [],
    'product_name': [],
    'product_id': [],
    'csaf_document_id': []
})

for row in df_all.itertuples(index=False):
    json_data = process_csaf_files.read_csaf_file(row.path)
    all_data = process_csaf_files.flatten_tree_data(json_data)

    if isinstance(all_data, pd.DataFrame) and (
            not "product_name" in all_data.columns or not "vendor" in all_data.columns or not "full_product_name_branch" in all_data):
        continue

    all_data['csaf_document_id'] = process_csaf_files.get_csaf_document_id(json_data)
    if "product_id" not in all_data.columns:
        all_data['product_id'] = None

    product_data = list(all_data["product_name"].tolist())
    if "product_version" in all_data.keys():
        product_version_data = list(all_data["product_version"].tolist())

    manufacturer_data = list(all_data["vendor"].tolist())
    full_product_name_data = list(all_data["full_product_name_branch"].tolist())
    product_set = set(product_data + list(product_set))
    manufacturer = set(manufacturer_data + list(manufacturer))
    merged_df = process_csaf_files.merge_dataframes(merged_df, all_data)
df_filtered = merged_df.loc[:, ['vendor', 'product_name', 'product_id', 'csaf_document_id']]

vendors = df_filtered["vendor"].dropna().unique()
#print(len(vendors), " vendors unfiltered found")

# Precleaning ------------------------

#
# Windscribe for Linux Desktop App
# Windows Server 2008 for x64-based Systems
# Wonderware InBatch Server and Runtime Clients

df_filtered['vendor'] = df_filtered['vendor'].apply(PreCleaner.pre_filter_csaf_vendors)
df_filtered['product_name'] = df_filtered['product_name'].apply(
    PreCleaner.remove_csaf_product_version_tokens
)
df_filtered['product_name'] = df_filtered['product_name'].apply(
    PreCleaner.pre_filter
)

df_filtered = df_filtered[
      df_filtered["product_name"].notna()
      & df_filtered["product_name"].str.strip().ne("")
]
vendors = df_filtered["vendor"].dropna().unique()

#print(len(df_filtered)," product-rows - filtered by precleaning")
#print(len(vendors), " vendors left - filtered by precleaning")

# ------------------------
"""
26101  product-rows unfiltered found
870  vendors unfiltered found
24981  product-rows - filtered by precleaning
812  vendors left - filtered by precleaning
"""
df_filtered_with_duplicates = df_filtered.copy()

df_filtered = df_filtered.drop_duplicates(
    subset=["vendor", "product_name"],
    keep="last"
)
vendors = df_filtered["vendor"].dropna().unique()
#print(len(df_filtered)," product-rows - filtered duplicates")
#print(len(vendors), " vendors left - filtered duplicates")



# Filter Option 1 - normalize own products for vendors stripping own vendor name

count_vendors_in_product_names = 0
count_vendors = 0
for vendor in vendors:

    vendor_df = df_filtered.copy()
    result = df_filtered[
      df_filtered["vendor"].str.contains(vendor, case=False, na=False, regex=False) &
      df_filtered["product_name"].str.contains(vendor, case=False, na=False, regex=False)
    ]

    if len(result) > 0:
        count_vendors += 1
        count_vendors_in_product_names += len(result)
#print(count_vendors, " different vendors are contained in ", count_vendors_in_product_names, " product name")


# see 15 start
def remove_vendor_prefix(row):
    vendor = row["vendor"]
    product = row["product_name"]
    if product.casefold().startswith(str(vendor).casefold() + " "):
        return product[len(vendor):].strip(" -_:")
    return product

df_filtered["product_name"] = df_filtered.apply(
    remove_vendor_prefix,
    axis=1
)

df_filtered = df_filtered[
      df_filtered["product_name"].notna()
      & df_filtered["product_name"].str.strip().ne("")
]
# see 15 end

vendors = df_filtered["vendor"].dropna().unique()

def find_by_tokens(df_all: pandas.DataFrame, vendor:str, words:list[str]) -> list[tuple[str, str]]:
    if vendor is None or len(words) == 0:
        return []
    mask = df_all["vendor"].str.lower().eq(vendor.strip().lower())
    text = df_all["product_name"].str.lower()
    for word in words:
        mask = mask & text.str.contains(word.strip().lower(), na=False)
    return list(df_all.loc[mask, ["product_id", "csaf_document_id"]].itertuples(index=False, name=None))
