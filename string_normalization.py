"""Module provides functions for normalization for matching CSAF and assets."""


import json
import os
import re
import pandas as pd
from string_helperfunctions import read_json_file
from string_helperfunctions import find_file
from string_synonym import StringSynonym


#Encoding
ENCODING = "uft-8"
'''
Vendor fertig stellen (known branches anlegen)
Produktname (überarbeiten)
Version (sehr mager)
'''

def clean_vendor(df: pd.DataFrame):
    """Clean manufacturer string with know pre_delete dictonary.
        ...
        
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
    df_load= pd.read_parquet(os.path.join(os.path.dirname(__file__), "test", "df_CSAF"))
    df = pd.DataFrame(df_load.vendor.unique(), columns=["vendor"])
    df["vendor_modified"] = df.vendor.copy()
    # catch empty/missing values
    df.vendor_modified.fillna('None', inplace=True)
    df.vendor_modified.loc[df.vendor_modified == ""] = 'None'
    # single the vendor
    df.vendor_modified = df.vendor_modified.str.split('and |, ')
    df = df.explode(column='vendor_modified')
    # get rid of abbreviations in brackets
    pattern_brack = r'\(.*?\)'
    df.vendor_modified.replace(pattern_brack," ", regex=True, inplace=True)
    # replace doubles spaces
    df.vendor_modified.replace(r'\s+'," ", regex=True, inplace=True)
    # delete unneccsary name fragments
    pre_delete = read_json_file(find_file('normalisation.json')
                                )['cleaning']['pre_delete_vendor']
    df["vendor_modified"] = df.vendor_modified.str.strip()
    df["vendor_mod_clean"] = df.vendor_modified.replace(pre_delete, ' ', regex=True)
    df["vendor_mod_pcl"] = df.vendor_mod_clean.copy()
    # TODO missing entries?
    # Postcleaning
    df.vendor_mod_pcl.replace(" & ", " ", regex=True, inplace=True)
    df.vendor_mod_pcl.replace(r'\s+'," ", regex=True, inplace=True)
    df.vendor_mod_pcl.replace(r'(?i)\bKG$'," ", regex=True, inplace=True)
    #replace missing . and -
    df["vendor_mod_pcl"] = df.vendor_mod_pcl.str.strip()
    df.vendor_mod_pcl.replace(r'\s?\.$|^\.\s?|\s\.\s', '', regex=True, inplace=True)
    df.vendor_mod_pcl.replace(r'\s?-$|^-\s?|\s-\s', '', regex=True, inplace=True)

    ###############################
    ### use vendor Synonym list ###
    ###############################
    syn = StringSynonym()
    df["vendor_mod_Syn"] = df["vendor_mod_pcl"].apply(lambda x: syn.normalize(x, 'vendor'))
    # no change necessary
    df.loc[df.vendor_mod_Syn.str.lower() == df.vendor.str.lower(), 'vendor_mod_Syn'] = ''

    # check the synonym with original entry
    df = df.assign(ind=range(len(df)))
    maker = 0
    df["Check"] = ''
    for index in df['ind'].loc[df['vendor_mod_Syn']!='']:
        a = df.loc[df['ind']==index]['vendor']
        b = df.loc[df['ind']==index]['vendor_mod_Syn'].to_list()
        checker = False
        if len(b)> 1:
            print("error")
        for word in [entry.strip() for entry in b[0].lower().split(',')]:
            if (a.str.lower().str.contains(word.strip()).any() or
                a.str.lower().str.contains(word.strip().rstrip('s')).any()):
                if checker:
                    maker = index
                    print(f'{index} and {word} with maker {maker}')
                    checker = False # sollte egal sein
                    continue
                elif str(df.loc[df['ind']==index]['vendor']
                         .to_list()[0]) == str(df.loc[df['ind']==maker]['vendor'].to_list()[0]):
                    if index > 2 and index-maker == 1:
                        df.loc[df['ind']==index, 'Check'] = word
                        checker = False
                        print(f'{word} and {index} with maker {maker}')
                        continue
                    elif index-maker > 1:
                        df.loc[df['ind']==index, 'Check'] = word
                        checker = False
                        print('Should not be possible yet')
                        continue
                else:
                    maker = 0
                    checker = True
                df.loc[df['ind']==index, 'Check'] = word

    #Check full completed?
    if (~(df.Check == '')).sum() < (~(df.vendor_mod_Syn == '')).sum():
        number = {(~(df.vendor_mod_Syn == '')).sum() - (~(df.Check == '')).sum()}
        print(f'There are {number} Synonyms where the check failed.')

    # TODO spellchecker
    df["vendor_mod_Spell"] = spellcheck(df)

    # TODO zurückabwickeln
    # delete ind
    # zeige nur änderung wo was geändert wurde (geiler Satz)
    # schreibe datei weg

    # del emtpy entries
    df_dummy = df[df.vendor_modified.str.strip() != '']
    df_dummy.groupby(df_dummy.index)['vendor_modified'].apply(list).reset_index()

    # TODO use stocklist as testbed
    # TODO use more CASF data

    # Part für Produktname sinnvoll
    text = 'some cracy string-that Siemens-AG is not right'
    tokens = text.split()
    cleaned_tokens = []
    for token in tokens:
        if '-' in token:
            parts = token.split('-')
            if all(part.isalpha() for part in parts):
                cleaned_tokens.extend(parts)
            elif token == "-":
                continue
            else:
                cleaned_tokens.append(token)
        else:
            cleaned_tokens.append(token)
    cleaned_text = ' '.join(cleaned_tokens)
    if not cleaned_text:
        return None
    else:
        return cleaned_text

def spellcheck(df :pd.DataFrame):
    '''Uses the spellchecker function'''
    print('not implemented yet')
    return df

# helperfunctions
def load_known_branches(filepath='./data/knownBranches.json'):
    try:
        with open(filepath, 'r', encoding="utf-16") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError("Could not find the file at: " + filepath)

def remove_special_characters(text):
    # remove / and \ from strings and replace it with a space
    text = re.sub(r'[\/\\]', ' ', text)
    # remove copyright
    text = re.sub(r'\(c\)|©', ' ', text, flags=re.IGNORECASE)
    # replace commas with space
    text = re.sub(r',', ' ', text)
    # Remove round brackets
    text = re.sub(r'\(|\)', '', text)
    tokens = text.split()
    cleaned_tokens = []
    for token in tokens:
        if '-' in token:
            parts = token.split('-')
            if all(part.isalpha() for part in parts):
                cleaned_tokens.extend(parts)
            elif token == "-":
                continue
            else:
                cleaned_tokens.append(token)
        else:
            cleaned_tokens.append(token)
    cleaned_text = ' '.join(cleaned_tokens)
    if not cleaned_text:
        return None
    else:
        return cleaned_text

def remove_letters_from_string(text):
    # TODO Wensky: Zweck/Grund für dieser Funktion?
    cleaned_text = re.sub(r'[^0-9.]', '', text)
    if cleaned_text and cleaned_text.endswith('.'):
        cleaned_text = cleaned_text[:-1]  # Remove "dot"
    return cleaned_text or None




# function to clean vendor and check for matches in known_branches.json


# function to clean product_name and product_family, check for matches in known_branches.json
def clean_product_column_and_extract_information(df, column_name, regex_dict):
    # Convert all strings to lowercase
    cleaned_column = df[column_name].str.lower().str.strip()
    # Remove all special characters of a string that are separated by space
    cleaned_column = cleaned_column.apply(lambda x: remove_special_characters(x) if isinstance(x, str) else None)
    # Advanced cleaning and data extraction
    for index, value in cleaned_column.items():
        # If product_name is empty but product_family is given, copy product_family to product_name_modified
        if column_name == 'product_name':
            if (not isinstance(value, str) or value == "" or pd.isna(value)) and isinstance(df.at[index, "product_family_modified"], str):
                cleaned_column.at[index] = df.at[index, "product_family_modified"]
                continue
        # Skip if value is not of type string
        if not isinstance(value, str) or value == "" or pd.isna(value):
            cleaned_column.at[index] = df.at[index, column_name+"_modified"]
            continue

        # Try to find information (recognize vendor and product version) and more cleaning
        for vendor, regex_patterns in regex_dict.items():
            for regex_pattern in regex_patterns:
                if re.search('(?i)' + regex_pattern, value):
                    # Recognize vendor and move product family
                    cleaned_vendor = df.at[index, 'vendor_modified']
                    if vendor not in cleaned_vendor.split(', '):
                        df.at[index, 'vendor_modified'] = cleaned_vendor + f", {vendor}" if cleaned_vendor else vendor

                    # Move matched portion of the string to 'product_family_modified'
                    matched_string = re.search('(?i)' + regex_pattern, value).group(0)
                    if 'product_family_modified' in df.columns:
                        if df.at[index, 'product_family_modified'] is None:
                            df.at[index, 'product_family_modified'] = matched_string
                        else:
                            df.at[index, 'product_family_modified'] += ', ' + matched_string
                    else:
                        df.at[index, 'product_family_modified'] = matched_string
                    # Remove matched_string from product_name
                    if matched_string in value:
                        value = value.replace(matched_string, "").strip()
        # Remove recognized vendor from product_name or product_family
        if isinstance(df.at[index, 'vendor_modified'],str):
            vendors = df.at[index, 'vendor_modified'].split(', ')
            for vendor in vendors:
                if vendor in value:
                    value = value.replace(vendor, "").strip()
            cleaned_column.at[index] = value

        # Try to recognize version information from product_names and add it
        if not isinstance(df.at[index, 'product_version'], str):
            version_matches = re.findall(r'v\d+$', value)
            for product_version in version_matches:
                df.at[index, 'product_version_modified'] = product_version
        elif isinstance(df.at[index, 'product_version'], str):
            df.at[index, 'product_version_modified'] = df.at[index, 'product_version']
    return cleaned_column

def find_function_keywords(column, function_keywords):
    function_keywords_found = []

    for value in column.str.lower().str.strip():
        if not isinstance(value, str):
            function_keywords_found.append('')
            continue

        # 100% (direct) Match
        found_keywords = [keyword for keyword in function_keywords if keyword in value]
        function_keywords_found.append(', '.join(found_keywords) if found_keywords else '')

    return function_keywords_found

def clean_dataframe_product(df, filepath='./data/knownBranches.json'):
    known_branches = load_known_branches(filepath)
    regex_patterns = known_branches.get('product_regex', {})
    function_keywords = known_branches.get('function_keywords', [])

    # Cleaning the 'product_name' and 'product_family' columns
    df['product_family_modified'] = clean_product_column_and_extract_information(df, 'product_family', regex_patterns)
    df['product_name_modified'] = clean_product_column_and_extract_information(df,'product_name', regex_patterns)
    #df['product_family_modified'] = clean_product_column_and_extract_information(df, 'product_family', regex_patterns)
    # Finding function keywords
    function_keywords_name = find_function_keywords(df['product_name'], function_keywords)
    function_keywords_family = find_function_keywords(df['product_family'], function_keywords)

    # Combining the keywords
    df['function_keywords_found'] = [', '.join(filter(None, fk)) for fk in zip(function_keywords_name, function_keywords_family)]

    # Removing duplicate entries in keywords and vendor
    df['function_keywords_found'] = df['function_keywords_found'].apply(lambda x: ', '.join(set(x.split(', '))))
    df['vendor_modified'] = df['vendor_modified'].apply(lambda x: ', '.join(set(x.split(', '))) if isinstance(x, str) else None)

    # Removing the found keywords from the modified columns
    for index, row in df.iterrows():
        # Ensure function_keywords_found is a string
        keywords_found = str(row['function_keywords_found']).split(', ') if pd.notna(row['function_keywords_found']) else []
        for keyword in keywords_found:
            # remove from product_name_modified
            try:
                # Ensure product_name_modified is a string
                if pd.notna(row['product_name_modified']):
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    df.at[index, 'product_name_modified'] = re.sub(pattern, '', df.at[index, 'product_name_modified'])
            except KeyError:
                continue
            # remove from product_family_modified
            try:
                # Ensure product_family_modified is a string
                if pd.notna(row['product_family_modified']):
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    df.at[index, 'product_family_modified'] = re.sub(pattern, '', df.at[index, 'product_family_modified'])
            except KeyError:
                continue
    return df

def clean_dataframe_version(df):
    df['product_version_modified'] = df['product_version_modified'].apply(lambda x: remove_letters_from_string(str(x)))
    return df

def clean_dataframe_version_range(df):
    df['product_version_range_modified'] = df['product_version_range'].copy()
    # more cleaning here
    return df
