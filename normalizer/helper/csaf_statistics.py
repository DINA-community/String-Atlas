import argparse
import csv
import os

CSAF_PATH = os.getenv('CSAF')

from normalizer.initialise.csaf_dataframe import df_filtered_with_duplicates
from matcher.initialise.clients import redis_client
from matcher.lib.lookup_table import redis_get_json


class CSFAStatistic:

    def __init__(self):
        self.vendors = []
        self.features = []
        self.features_dict = {}
        self.vendor_series_token = {}
        self.vendor_subseries_token = {}

        self.series_entity_index = {}
        self.vendor_others_token_series = dict()
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
                if this_brand:
                    if subseries not in self.vendor_others_token_series[vendor]:
                        self.vendor_others_token_series[vendor][subseries] = {}
                    if brand not in self.vendor_others_token_series[vendor][subseries]:
                        self.vendor_others_token_series[vendor][subseries][brand] = 1
                    else:
                        self.vendor_others_token_series[vendor][subseries][brand] = self.vendor_others_token_series[vendor][subseries][brand] + 1



    def create_statistic(self, df_filtered, output_path="csaf_statistics.csv"):
        for vendor in self.vendors:
            vendor_filtered_df = df_filtered.loc[
                df_filtered["vendor"].str.casefold() == vendor.casefold()
                ].copy()
            vendor_filtered_df.loc[:, 'product_name'].apply(lambda x: self.extract_features_from_text(x, vendor))

        rows = []
        for vendor in self.vendors:

            if vendor not in self.vendor_others_token_series:
                continue
            for subseries, brands in self.vendor_others_token_series[vendor].items():
                for brand, count in brands.items():
                    rows.append({
                        "vendor": vendor,
                        "brand": brand,
                        "subseries": subseries,
                        "count": count,
                    })

        rows.sort(key=lambda row: (row["vendor"], row["brand"], row["subseries"]))
        self.export_csv(rows, output_path)
        return rows

    @staticmethod
    def export_csv(rows, output_path):
        output_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["vendor", "brand", "subseries", "count"])
            writer.writeheader()
            writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(description="Export CSAF producttypes counts as CSV.")
    parser.add_argument(
        "-f",
        "--file",
        default="csaf_product_statistics.csv",
        help="Path to the CSV output file. Defaults to csaf_statistics.csv.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    statistic = CSFAStatistic()
    rows = statistic.create_statistic(df_filtered_with_duplicates, args.file)
    print(f"{len(rows)} product types and count exported to {args.file}")
