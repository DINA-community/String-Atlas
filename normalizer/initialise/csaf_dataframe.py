import os
import pandas
import pandas as pd
import process_csaf_files

CSAF_FOLDERS: str = os.getenv('CSAF_FOLDERS', 'All')
CSAF_PATH = os.getenv('CSAF')
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

def find_by_tokens(df_all: pandas.DataFrame, vendor:str, words:list[str]) -> list[tuple[str, str]]:
    if vendor is None or len(words) == 0:
        return []
    mask = df_all["vendor"].str.lower().eq(vendor.strip().lower())
    text = df_all["product_name"].str.lower()
    for word in words:
        mask = mask & text.str.contains(word.strip().lower(), na=False)
    return list(df_all.loc[mask, ["product_id", "csaf_document_id"]].itertuples(index=False, name=None))