
import pandas as pd
from pathlib import Path
from process_csaf_files import process_csaf_sources
from process_csaf_files import get_csaf_sources, get_json_list
from time import perf_counter


if __name__ == "__main__":
    """ Start from root folder with 
    # python3 -m tests.test_files.test_process_csaf_file
    """
    start = perf_counter()
    df_csaf = process_csaf_sources(get_csaf_sources(
        get_json_list(Path.cwd().joinpath("tests", "test_files"))))
    elapsed = perf_counter() - start
    print(f"Elapsed time: {elapsed:.6f} s")

    # checks offline
    df_csaf.to_csv("new.csv")
    df_old = pd.read_csv(Path(__file__).resolve().parent / "old.csv")
    df_new = pd.read_csv(Path(__file__).resolve().parent / "new.csv")
    common_cols = df_old.columns.intersection(df_new.columns)
    result = pd.concat(
        [df_old[common_cols], df_new[common_cols]],
        ignore_index=True
    )
    print(len(result.drop_duplicates(keep=False)))
    print(df_old.columns.difference(df_new.columns))
    