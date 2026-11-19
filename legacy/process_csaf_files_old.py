"""Module provides functions to look at CSAf file for courpus and for matching."""

import json
import os
from pathlib import Path
from time import perf_counter
import cProfile
import pandas as pd
import numpy as np
from utils.string_helperfunctions import read_json_file, find_file
from utils.string_helperfunctions import LogHandler

# Encoding
ENCODING = "utf-8"

def create_folders_set(folders:str):
    allowed_folders = set()
    for folder in folders.split(','):
        if '-' in folder:
            start, end = folder.split('-')
            for folder_num in range(int(start), int(end) + 1):
                allowed_folders.add(str(folder_num))
            allowed_folders.update()
        else:
            allowed_folders.add(str(folder))
        allowed_folders.add("csaf_files")
        allowed_folders.add("OT")
        allowed_folders.add("white")
    return allowed_folders

def is_folder_allowed(file_path: Path, allowed_folders: set[str]) -> bool:
    """
    check if parent folder is allowed
    """
    last_folder = file_path.parent.name
    return last_folder in allowed_folders


# def process_json_files_in_directory(directory_path):
def get_csaf_sources(path_directory: str, allowed_folders: set[str] = None):
    '''Get paths to json source files from a directory and check if it is a CSAF one.

    Parameter:
        path_directory:str  path to the directory where the CSAf json files are.
    
    Return:
        pd.Dataframe with all CSAF documents found with columns path and file name
    '''
    formating = "[%(asctime)s - %(levelname)s - process_csaf_files  %(funcName)s] %(message)s"
    log = LogHandler(formating)
    file_list = []
    for source in [path_directory]:
        source = os.path.normpath(source)
        for root, _, files in os.walk(source):
            for file in files:
                if file.endswith(".json") is False:
                    log.logger.debug('Filepath %s is not a json file. File is excluded.', file)
                    continue

                file_path = os.path.join(root, file)
                if allowed_folders is not None and not is_folder_allowed(Path(file_path), allowed_folders):
                    continue

                try:
                    with open(file_path, 'r', encoding=ENCODING) as filename:
                        #os.path.getsize(fullpathhere) > 0
                        if os.stat(file_path).st_size == 0:
                            log.logger.debug('Filepath %s lead to a emtpy json file. '
                                             'File is excluded.', file_path)
                            continue
                        try:
                            dummy = json.load(filename)
                        except json.decoder.JSONDecodeError as e:
                            log.logger.error('Filepath %s lead to Error: %s. File is excluded. '
                                             ' Check it out.', file_path, e)
                        # Check if it is a CSAF file
                        try:
                            dummy1 = dummy.get('document')
                            dummy2 = dummy.get('product_tree')
                            dummy3 = dummy.get('vulnerabilities')
                            if None in (dummy1, dummy2, dummy3):
                                log.logger.info('File with path %s fits not the CSAF standard. '
                                                'File is excluded.', file_path)
                            else:
                                file_list.append([os.path.join(root, file), file])
                        except (KeyError, json.decoder.JSONDecodeError) as e:
                            log.logger.error('Filepath %s lead to a non CSAF file with Error: %s. '
                                             'File is excluded', file_path, e)
                except FileNotFoundError as e:
                    raise FileNotFoundError("Could not find the file at: " + file_path) from e
    return pd.DataFrame(file_list, columns=['path', 'file'])

def merge_dataframes(df1, df2):
    return pd.concat([df1, df2], axis=0, ignore_index=True, sort=False)

def read_csaf_file(file_path):
    '''Read json file of a CSAF document.'''
    formating = "[%(asctime)s - %(levelname)s - process_csaf_files  %(funcName)s] %(message)s"
    log = LogHandler(formating)
    try:
        with open(file_path, 'r', encoding=ENCODING) as filename:
            #os.path.getsize(fullpathhere) > 0
            if os.stat(file_path).st_size == 0:
                log.logger.warning('Filepath %s lead to a emtpy json file.'
                                   ' File isexcluded.', file_path)
            try:
                dummy = json.load(filename)
            except json.decoder.JSONDecodeError as e:
                log.logger.warning('Filepath %s lead to Error: %s. File is excluded. '
                                   'Check it out.', file_path, e)
            except FileNotFoundError:
                log.logger.warning('Could not find the file at: %s', file_path)
            # Check if it is a CSAF file
            try:
                dummy1 = dummy.get('document')
                dummy2 = dummy.get('product_tree')
                dummy3 = dummy.get('vulnerabilities')
                if None in (dummy1, dummy2, dummy3):
                    log.logger.info('File with path %s fits not the CSAF standard.'
                                    , file_path)
                    return True
                else:
                    return dummy
            except (KeyError, json.decoder.JSONDecodeError) as e:
                log.logger.info('Filepath %s lead to a non CSAF file with Error: %s.',
                                file_path, e)
    except FileNotFoundError as e:
        log.logger.warning("Could not find the file at: %s", file_path)


def get_csaf_document_id(json_data):
    '''Extract CSAF document tracking id.'''
    return json_data.get('document', {}).get('tracking', {}).get('id', '')


def flatten_tree_data(json_data, input_type="product_tree"):
    '''Separate in two different structes of CSAF files.'''
    tree = json_data.get(input_type, {})
    # if full product names instead of branches
    if 'full_product_names' in tree:
        df_json = pd.DataFrame(tree['full_product_names']
                               ).rename(columns={'name': 'full_product_names'})
        return df_json
    tree_data = tree.get('branches', [])
    flattened_data = []
    for item in tree_data:
        flattened_data.extend(flatten_branch(item, {}))
    return pd.DataFrame(flattened_data)


def flatten_branch(branch, parent_attributes):
    '''Read in branches of json file.'''
    attributes = parent_attributes.copy()
    attributes.update({
        branch.get('category', ''): branch.get('name', '')
    })
    if 'branches' in branch:
        flat_branches = []
        for sub_branch in branch['branches']:
            flat_branches.extend(flatten_branch(sub_branch, attributes))
        return flat_branches
    else:
        # last leaf of branches
        if 'product' in branch:
            attributes.update({
                'full_product_name_branch': branch['product'].get('name', ''),
                'product_id': branch['product'].get('product_id', '')
            })
        return [attributes]


def process_csaf_sources(csaf_sources: pd.DataFrame):
    '''Process the csaf json list'''
    formating = "[%(asctime)s - %(levelname)s - process_csaf_files  %(funcName)s] %(message)s"
    log = LogHandler(formating)
    combined_df = pd.DataFrame()
    predefined_columns = read_json_file(find_file('csaf_columns.json')
                                        )['df_columns']['predefined_columns']
    fac = np.round(len(csaf_sources) / 30, 0) + 1
    for i in range(len(csaf_sources)):
        if i > 0:
            if i % fac == 0:
                print(f"{np.round(i / len(csaf_sources) * 100, 2)}% eingelesen")
        file_path = csaf_sources.path.loc[i]
        try:
            json_data = read_csaf_file(file_path)
            if json_data is None:
                log.logger.info("Filepath contain no CSAF data. %s", file_path)
                continue
            df_flattened = flatten_tree_data(json_data, 'product_tree')
            df_flattened['path'] = file_path
            # Lege fehlende Spalten an
            df_flattened['data_source'] = get_url_from_csaf(json_data, file_path)
            df_flattened['csaf_document_id'] = get_csaf_document_id(json_data)
            for fix_column in predefined_columns:
                if fix_column not in df_flattened.columns:
                    df_flattened[fix_column] = None
            if set(df_flattened.columns).issubset(set(predefined_columns)) is False:
                log.logger.error("There are undefined columns in %s", file_path)
            # df_flattened = df_flattened[predefined_columns]
            combined_df = pd.concat([combined_df, df_flattened], ignore_index=True)
        except json.JSONDecodeError as e:
            log.logger.warning("Fehler beim Parsen der Datei %s %s", file_path, e)
    return combined_df


def get_url_from_csaf(d, path):
    '''Extract url from CSAf file.'''
    formating = "[%(asctime)s - %(levelname)s - process_csaf_files  %(funcName)s] %(message)s"
    log = LogHandler(formating)
    try:
        for ref in d['document']['references']:
            if ref.get('url', '').endswith('.json'):
                return ref['url']
    except KeyError as e:
        log.logger.info("%s: No url for json document provided in %s", e, path)
        return 'missing'


if __name__ == "__main__":
    print('Call process_csaf_sources(get_csaf_sources(<PATH_directory>))')
    start = perf_counter()
    df = process_csaf_sources(get_csaf_sources(os.path.join(os.getcwd(), 'resources')))
    elapsed = perf_counter() - start
    print(f"Elapsed time: {elapsed:.6f} s")
