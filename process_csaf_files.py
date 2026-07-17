"""Module provides functions to look at CSAf file for text miner."""

import json
import os
import cProfile
from timeit import timeit
from pathlib import Path
from tqdm import tqdm
import pandas as pd
from utils.log_class import get_logger

# Encoding
ENCODING = "utf-8"

# CSAF Keys
PRODUCT_TREE = "product_tree"
FULL_PRODUCT_NAMES = "full_product_names"
BRANCHES = "branches"


def get_json_list(root: Path = Path.cwd().joinpath("resources"),
                  folder_names: set[str] | None = None) -> list[Path]:
    """Get paths from json files from a directory -r

    Parameter:
        path_directory: Path of starting directory
                        for collecting paths to json files
        allowed_folders: set[str] sub folders where to look
        (used to make selection if needed e.g.for tests)
    
    Awareness:
        Be aware that the full path is stored and any json file within
        the root path will be processed but also deleted later on.

    Return:
        list[Path] of json files
    """
    if folder_names is None:
        return list(root.rglob("*.json"))

    json_files = []

    for dirpath, dirnames, _f in os.walk(root):
        if Path(dirpath).name in folder_names:
            for subdir, _dir, files in os.walk(dirpath):
                for file in files:
                    if file.endswith(".json"):
                        json_files.append(Path(subdir) / file)
            # Don't descend into this subtree again
            dirnames.clear()
    return json_files


def get_csaf_sources(filelist: list[Path]) -> pd.DataFrame:
    """Check if json files is a CSAF one.

    Parameter:
        list[Path] filelist: List of Path leading to
        potential CSAF files

    Return:
        list with all CSAF documents paths
    """
    log = get_logger(__name__, __file__)
    csaf_files = []
    
    required_entries = {"document", PRODUCT_TREE, "vulnerabilities"}
    
    for file_path in filelist:
        try:
            if file_path.stat().st_size == 0:
                log.debug(
                    "Filepath {} leads to an empty JSON file. \
                    File is excluded.",
                    file_path,
                )
                continue
                
            with open(file_path, "r", encoding=ENCODING) as filename:
                try:
                    data = json.load(filename)
                except json.decoder.JSONDecodeError as e:
                    log.opt(exception=True).warning(
                        "Loading {} lead to Error: {}. File is excluded. "
                        " Check it out.", file_path, e,
                    )
                    continue

            if not isinstance(data, dict):
                log.info(
                    "File {} does not contain a JSON object. \
                        File is excluded.",
                    file_path,
                )
                continue

            if not required_entries.issubset(data.keys()):
                missing = required_entries - data.keys()
                log.info(
                    "File {} is not a valid CSAF document. Missing keys: {}",
                    file_path,
                    ", ".join(sorted(missing)),
                )
                continue

            csaf_files.append(file_path)
        except OSError as e:
            log.error("Could not read {}: {]}", file_path, e)
    return csaf_files


def flatten_tree_data(json_data: dict, input_type: str = PRODUCT_TREE):
    """Separate in two different structures of CSAF files."""
    tree = json_data.get(input_type, {})
    # if full product names instead of branches
    if FULL_PRODUCT_NAMES in tree:
        df_json = pd.DataFrame(tree[FULL_PRODUCT_NAMES]).rename(
            columns={"name": FULL_PRODUCT_NAMES}
        )
        return df_json
    tree_data = tree.get(BRANCHES, [])
    flattened_data = []
    for item in tree_data:
        flattened_data.extend(flatten_branch(item, {}))
    return pd.DataFrame(flattened_data)


def flatten_branch(branch, parent_attributes):
    """Read in branches of json file."""
    attributes = parent_attributes.copy()
    attributes.update({branch.get("category", ""): branch.get("name", "")})
    if BRANCHES in branch:
        flat_branches = []
        for sub_branch in branch[BRANCHES]:
            flat_branches.extend(flatten_branch(sub_branch, attributes))
        return flat_branches
    else:
        # last leaf of branches
        if "product" in branch:
            attributes.update(
                {
                    "full_product_name_branch":
                        branch["product"].get("name", ""),
                    "product_id":
                        branch["product"].get("product_id", ""),
                }
            )
        return [attributes]


def nested_get(d, *keys, default=None):
    """Get dictionary function to reduce code replication."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key)
    return d if d is not None else default


def process_csaf_sources(csaf_sources: list[Path]) -> pd.DataFrame:
    """Process the csaf json list

    Parameter:
        csaf_sources with full path to file

    Limitations:
        it is assumed, that the files are accurate csaf files
        the previous functions in this module check only the
        top level structure
    """
    log = get_logger(__name__, __file__)

    dfs = []
    for file_path in tqdm(csaf_sources):
        with open(file_path, 'r', encoding=ENCODING) as file:
            json_data = json.load(file)
        references = nested_get(json_data,
                                "document", "references", default="")
        df_flattened = flatten_tree_data(json_data, PRODUCT_TREE)
        df_flattened = df_flattened.assign(
            path=file_path,
            data_source=next(ref["url"] for ref in references if
                             ref.get("url", "").endswith(".json")),
            csaf_document_id=nested_get(json_data,
                                        "document",
                                        "tracking",
                                        "id",
                                        default="")
        )

        dfs.append(df_flattened)
    if not dfs:
        log.error("All provided CSAF files are not applicable or empty")
        return pd.DataFrame()
    else:
        df = pd.concat(dfs, ignore_index=True)
        return csaf_checks(df.drop(columns=["path"]))


def csaf_checks(df: pd.DataFrame) -> pd.DataFrame:
    """"Check for missing columns that are required later on."""

    log = get_logger(__name__, __file__)
    
    path_csaf_columns = Path.cwd().joinpath("utils", "csaf_columns.json")
    with open(path_csaf_columns, 'r', encoding=ENCODING) as file:
        pre_col = json.load(file)["df_columns"]["predefined_columns"]
        
    # Set None for missing predefined columns
    missing = set(pre_col) - set(df.columns)
    for col in missing:
        df[col] = None
    # Check for unexpected columns
    unexpected = set(df.columns) - set(pre_col)
    if unexpected:
        log.error("Unexpected columns: {}", unexpected)
    return df

def check_resources(fkt: str = "find_json_files(Path(os.getcwd()))"):
    """To optimize the implementation: cProfile to identify bottlenecks."""
    cProfile.run(fkt)


if __name__ == "__main__":
    print("Call process_csaf_sources(get_csaf_sources(get_json_list(<root_path>)))")
    # Test
    
    process_csaf_sources(get_csaf_sources(
        get_json_list(Path.cwd().joinpath("tests",
                                          "test_files"))))
