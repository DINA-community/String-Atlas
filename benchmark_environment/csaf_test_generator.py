import argparse
from pathlib import Path

import pandas as pd


def generate_columns(df_source, df_output):
    for _, row in df_source.iterrows():
        vendor = row["vendor"]
        brand = row["brand"]
        subseries = row["subseries"]

        col = brand + " " + subseries
        col = col.strip()
        df_output.loc[0, col] = col
        df_output.loc[1, col] = vendor
        df_output.loc[2, col] = "Product"
        df_output.loc[3, col] = "contains(\"" + col + "\"));"


def generate_test_file(args):

    with open(file="test_strategy_template.csv", encoding="utf-8") as benchmark_template_file:

        df_output = pd.read_csv(benchmark_template_file)

        with open(file=args.csaffile, encoding="utf-8") as csaf_file:
            df_source = pd.read_csv(csaf_file)
            df_source = df_source.sort_values(
                by=df_source.columns[3],
                ascending=False
            )

            generate_columns(df_source.iloc[0:args.top_number,:], df_output)

            middle_n = min(args.middle_number, len(df_source) - args.last_number - args.top_number)
            start_middle = (len(df_source) - middle_n) // 2
            generate_columns(df_source.iloc[start_middle:start_middle + middle_n, :], df_output)

            generate_columns(df_source.iloc[-args.last_number:, :], df_output)

            df_output.to_csv("test_strategy_generated.csv", index=False, header=True)

if __name__ == "__main__":
    argparse = argparse.ArgumentParser()
    argparse.add_argument("--last_number", type=int, required=False, default=25)
    argparse.add_argument("--top_number", type=int, required=False, default=25)
    argparse.add_argument("--middle_number", type=int, required=False, default=100)
    argparse.add_argument("--csaffile", type=Path, required=True, default="csaf_product_statistics.csv")
    args = argparse.parse_args()
    generate_test_file(args)
