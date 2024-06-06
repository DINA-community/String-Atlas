""" A class for normalizing an input string by matching it against a dictionary of given synonyms.
        Requirements:

        Parameters:
            test_str (str): The test string to normalize.
            specific_dict (str): The specific attribute (e.g. device family) to use for 
                normalization. If not provided or not found, the whole dictionary (pd.DataFrame)
                is used.
            case_sensitive (bool): Not an option anymore. Serach is always case insensitve.

        Returns:
            str: The normalized string based on the specified dictionary.
            '' : if the test string is empty or no match is found in the dictionaries.
"""
from inspect import currentframe, getframeinfo
import re
import yaml
import pandas as pd
import numpy as np
from string_helperfunctions import LogHandler, find_file

# Default path to files for loading custom synonym words.
DEFAULT_SYNONYM_FILENAME = "synonym_list.yaml"

# ENCODING
ENCODING = 'utf-8'


class StringSynonym:
    """
    A class for normalizing an input string by matching it against a dictionary of given synonyms.
    """

    def __init__(self, synonyms_filename: str = DEFAULT_SYNONYM_FILENAME):
        """
        Initializes the class with the provided synonyms file name.
        Reads the synonyms from yaml file and assigns them to instance variables.

        Parameters:
            synonyms_filename (str): Name of the yaml file containing synonyms.
                Default: DEFAULT_SYNONYM_FILENAME.
        """

        formating = "[%(asctime)s - %(levelname)s - StringNormalizer  %(funcName)s] %(message)s"
        self.logger = LogHandler(formating)
        self.df_dict = self._read_synonyms(find_file(synonyms_filename))

    def _read_synonyms(self, synonyms_path :str):
        '''Reads synonyms from an yaml file and returns a DataFrame.

        Parameters:
            synonyms_path (str): Path to the yaml file containing synonyms.
        Returns:
            df: A df containing:
                - columns: in general attributes of the DataModel in Netbox plugin
                - index: 
                    - alias: for the attribute (column name)
                    - unknown: if a manufacturer is not known 
                    - manufacturer according to the attributes
        Raises:
            Exception: If there is an error reading the json file.'''
        try:
            with open(synonyms_path, 'r', encoding=ENCODING) as file:
                _data = yaml.safe_load(file)
                df = pd.DataFrame(_data)
                for col in df.columns:
                    df[col] = df[col].apply(lambda x: ' , '.join(x) if isinstance(x, list)
                                            else np.nan)
                    df.fillna('N/A', inplace=True)
                    df = df.astype(object)
                return df
        except FileNotFoundError:
            frame = getframeinfo(currentframe())  # type: ignore
            self.logger.error(f"Error by trying reading file with path {synonyms_path} "
                              f"in function {frame.function}")
            return pd.DataFrame()

    def _get_master_word_from_dictionary(self, test_str: str, dictionary: pd.DataFrame):
        """
        Finds the master word from the given dictionary based on a test string.

        Parameters:
            test_str (str): The test string to search for in the dictionary.
            dictionary (pd.DataFrame): The dictionary to search in.
            case_sensitive (bool): Not an option anymore. Serach is always case insensitve.

        Returns:
            str: The master word from the dictionary that matches the test string.
                    - In case of alias returns columns name
                    - Otherwise master word(s) separated by ","
            Returns an empty string if no match is found.
        """
        # remove special signs
        test_str = re.sub(r'[)(),-._/]', ' ', test_str)
        test_str = re.sub(r'\s+', ' ', test_str).strip()
        master_word = ""
        for col in dictionary.columns:
            for ind in dictionary.index:
                if dictionary.loc[ind, col] == "N/A":
                    continue
                if re.search(rf'\b{test_str}\b', str(self.df_dict.loc[ind, col]),
                             flags=re.IGNORECASE):
                #if test_str.lower() in str(self.df_dict.loc[ind, col]).lower():
                    if ind == 'alias':
                        match = dictionary.columns[dictionary.loc[ind].str.contains
                                                   (test_str,na=False, case=False)]
                        if len(match) == 1 :
                            return match[0]
                        elif len(match):
                            frame = getframeinfo(currentframe())  # type: ignore
                            self.logger.info(f"multiple hits in function {frame.function} "
                                             f"for string {test_str}")
                            for word in match:
                                master_word = master_word + ' , ' + word
                            return match[:]
                    else:
                        if master_word == "":
                            master_word = ind
                        else:
                            master_word = master_word + ', ' + ind
        return master_word


    def normalize(self, test_str: str, specific_dict_name: str = ""):
        """
        Normalizes a test string based on the specified dictionary of synonyms.

        Parameters:
            test_str (str): The test string to normalize.
            specific_dict (str): The specific dictionary (as pd.DataFrame) to use for normalization.
                If not provided or not found, the whole dictionary is used.
            case_sensitive (bool): Not an option anymore. Serach is always case insensitve.

        Returns:
            str: The normalized string based on the specified dictionary.
            '' : if the test string is empty or no match is found in the dictionaries.
        """
        frame = getframeinfo(currentframe())  # type: ignore
        if not test_str:
            self.logger.warning(f"WARNING: No input string to normalize. "
                                f"Call in line {frame.lineno} of function {frame.function}")
            return ""
        if specific_dict_name == "":
            return self._get_master_word_from_dictionary(test_str, self.df_dict)
        # Look for specified dictionary
        match = self.df_dict.columns[self.df_dict.loc['alias'].str.contains(specific_dict_name,
                                                                            na=False, case=False)]
        if len(match)> 1:
            self.logger.info(f"Inconclusive specified dictionary name {specific_dict_name}. "
                             f"Call in line {frame.lineno} of function {frame.function}")
            return self._get_master_word_from_dictionary(test_str, self.df_dict)
        elif len(match):
            self.logger.info(f"Use specific column {match[0]}. "
                             f"Call in line {frame.lineno} of function {frame.function}")
            return self._get_master_word_from_dictionary(test_str,
                                                         pd.DataFrame(self.df_dict[match[0]]))
        else:
            self.logger.info(f"no specified dictionary name for found {specific_dict_name}. "
                             f"Call in line {frame.lineno} of function {frame.function}")
            return self._get_master_word_from_dictionary(test_str, self.df_dict)



if __name__ == "__main__":
    # NOTE: The following code provides examples using the class and testing it's functionality.

    def test(test_str, specific_dict: str = ""):
        """
        Tests the normalization of a test string and prints the result.

        Parameters:
            test_str (str): The test string to normalize.
            specific_dict (str): The specific dictionary to use for normalization.
                Defaults to an empty string, which indicates using the default dictionary.
            case_sensitive (bool): Determines whether the normalization is case sensitive or not.
                Defaults to False.
        """
        with open('test_synonym.txt', 'a', encoding='utf-8') as file:
            file.write(f"'{test_str}' -> '{sn.normalize(test_str, specific_dict)}'\n")

        print(f"'{test_str}' -> '{sn.normalize(test_str, specific_dict)}'")

    # initialize the StringNormalizer class with default parameters
    sn = StringSynonym()

    # Test self synonyms
    test("Hersteller")
    test("device role")
    test("device-role")

    #Test multiple hits
    test("LS")
    test("ge")

    # Test "Manufacturer"
    test("io device")
    test("SIEMENS")
    test("Phoenix Contact GmbH")
    test("PxC")
    test("Asea Brown Boveri")
    test('Dräger')

    # Test "Manufacturer" synonyms under restriction of the search space
    test("SIEMENS", "Device Role")  # returns '' because of lookup in wrong search space
    test("SIEMENS", "Manufacturer")
    test("siemens.com", "Manufacturer")
    test("Phoenix Contact GmbH", "Manufacturer")
    test("PxC", "Manufacturer")
    test("Asea Brown Boveri", "Manufacturer")

    # Test "Device Role" synonyms
    test("PLC")
    test("SPS")
    test("io device")
    test("Firewall")
    test("switch")
    test("bus coupler")
    test("BK")
    test("Human Machine Interface")
    test("Domain-Controller")

    # Test "Device Role" synonyms under restriction of the search space
    test("SPS", "Device Role")
    test("io device", "Device Role")
    test("Firewall", "Device Role")
    test("switch", "Device Role")
    test("bus coupler", "Device Role")
