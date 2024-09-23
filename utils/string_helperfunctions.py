'''function for common tasks'''
import json
import os
from pathlib import Path
from utils.log_class import LogStyle

ENCODING = "utf-8"


def find_file_in_folder(search_path, file_name):
    '''Look if the file_name is given in the folder "search path".'''
    for root, __, files in os.walk(search_path):
        if file_name in files:
            return os.path.join(root, file_name)
    return 'False'


def find_file(file_name):
    """Search the file_name at three different places: 
            current folder,
            folder ../../data/ 
            and 
            ../../String-Sysiphos/.
    
    Parameter:
        File_name of the yaml file.
    
    Return:
        Filepath:str to the parameter file_name
        '' if no path was found
    """
    log = LogStyle()
    search_path = Path(__file__).resolve()
    if find_file_in_folder(search_path, file_name) == 'False':
        # print('Look at ../../data directory')
        search_path = Path(__file__).resolve().parents[2]/'data'
        if find_file_in_folder(search_path, file_name) == 'False':
            # print('Look at ../../String-Sysiphos/')
            search_path = Path(__file__).resolve().parents[2]/'String-Sysiphos'
            if find_file_in_folder(search_path, file_name) == 'False':
                log.logger.error(f"File {file_name} not found.")
                return ''
    return find_file_in_folder(search_path, file_name)

def read_json_file(file_path):
    '''Read json file of a CSAF document.'''
    try:
        with open(file_path, 'r', encoding=ENCODING) as file:
            return json.load(file)
    except FileNotFoundError as e:
        raise FileNotFoundError("Could not find the file at: " + file_path) from e
    except TypeError as e:
        raise TypeError("Do not get a path to file: " + file_path) from e
