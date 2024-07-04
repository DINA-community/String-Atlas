'''function for common tasks'''
import logging
import json
import os
from inspect import currentframe, getframeinfo

ENCODING = "utf-8"

class LogHandler:
    """Logger for the String-Atlas repository"""
    def __init__(self, formating:str=''):
        if formating == '':
            formating = "[%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)20s()]\
                  %(message)s"
        logging.basicConfig(filename='code_process.log',encoding=ENCODING,
                            level=logging.DEBUG, format=formating)
        self.logger = logging.getLogger(__name__)


    def _info(self, text):
        self.logger.info(text)

    def _debug(self, text):
        self.logger.debug(text)

    def _warning(self, text):
        self.logger.warning(text)

    def _error(self, text):
        self.logger.error(text)

    def info(self, text):
        '''Call protected function _info'''
        self._info(text)

    def debug(self, text):
        '''Call protected function _debug'''
        self._debug(text)

    def warning(self, text):
        '''Call protected function warning'''
        self._warning(text)

    def error(self, text):
        '''Call protected function _error'''
        self._error(text)


def find_file_in_folder(search_path, file_name):
    '''Look if the file_name is given in the folder "search path".'''
    for root, __, files in os.walk(search_path):
        if file_name in files:
            return os.path.join(root, file_name)
    return 'False'


def find_file(file_name):
    """Search the file_name at three different places: 
            current folder,
            folder ../data/ 
            and 
            ../String-Sysiphos/.
    
    Parameter:
        File_name of the yaml file.
    
    Return:
        Filepath:str to the parameter file_name
        '' if no path was found
    """
    log = LogHandler()
    init_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    if find_file_in_folder(init_path, file_name) == 'False':
        # print('Look at ../data directory')
        search_path = os.path.join(init_path, os.path.pardir, 'data')
        if find_file_in_folder(search_path, file_name) == 'False':
            # print('Look at ../String-Sysiphos/')
            search_path = os.path.join(init_path, os.path.pardir, 'String-Sysiphos')
            if find_file_in_folder(os.path.join(search_path, os.path.pardir),
                                            file_name) == 'False':
                frame = getframeinfo(currentframe())  # type: ignore
                log.error(f"File {file_name} not found. Function: "
                          f"{frame.function}, Line {frame.lineno}")
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
