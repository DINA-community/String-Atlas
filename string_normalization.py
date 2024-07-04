"""Module provides functions for normalization for matching CSAF and assets."""


import os
import re
import pandas as pd
from string_helperfunctions import read_json_file
from string_helperfunctions import find_file
from string_synonym import StringSynonym


#Encoding
ENCODING = "uft-8"
'''
#TODO Liste
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
    df["vendor_prep"] = df.vendor.copy()
    # catch empty/missing values
    df.vendor_prep.fillna('None', inplace=True)
    df.vendor_prep.loc[df.vendor_prep == ""] = 'None'
    # single the vendor
    df.vendor_prep = df.vendor_prep.str.split('and |, ')
    df = df.explode(column='vendor_prep')
    #####################
    #### precleaning ####
    #####################
    df["vendor_precl"] = df.vendor_prep.copy()
    # get rid of abbreviations in brackets
    pattern_brack = r'\(.*?\)'
    df.vendor_precl.replace(pattern_brack," ", regex=True, inplace=True)
    # replace doubles spaces
    df.vendor_precl.replace(r'\s+'," ", regex=True, inplace=True)
    df.vendor_precl = df.vendor_precl.str.strip()
    ########################################
    ### delete unneccsary name fragments ###
    ########################################
    df["vendor_del"] = df.vendor_precl.copy()
    pre_delete = read_json_file(find_file('normalisation.json')
                                )['cleaning']['pre_delete_vendor']
    df["vendor_del"] = df.vendor_del.replace(pre_delete, ' ', regex=True)
    ####################
    ### Postcleaning ###
    ####################
    df["vendor_poscl"] = df.vendor_del.copy()
    df.vendor_poscl.replace(" & ", " ", regex=True, inplace=True)
    df.vendor_poscl.replace(r'\s+'," ", regex=True, inplace=True)
    df.vendor_poscl.replace(r'(?i)\bKG$'," ", regex=True, inplace=True)
    #replace missing . and -
    df.vendor_poscl = df.vendor_poscl.str.strip()
    df.vendor_poscl.replace(r'\s?\.$|^\.\s?|\s\.\s', '', regex=True, inplace=True)
    # remove / and \ from strings and replace it with a space
    df.vendor_poscl.replace(r'[\/\\]', '', regex=True, inplace=True)
    # remove copyright
    df.vendor_poscl.replace(r'(?i)\(c\)|©', '', regex=True, inplace=True)
    ###############################
    ### use vendor Synonym list ###
    ###############################
    syn = StringSynonym()
    df["vendor_mod_Syn"] = df["vendor_poscl"].apply(lambda x: syn.normalize(x, 'vendor'))
    # no change necessary
    df.loc[df.vendor_mod_Syn.str.lower() == df.vendor.str.lower(), 'vendor_mod_Syn'] = ''
    # check the synonym with original entry
    df = df.assign(ind=range(len(df)))
    maker = 0
    df["vendor_syn"] = ''
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
                        df.loc[df['ind']==index, 'vendor_syn'] = word
                        checker = False
                        print(f'{word} and {index} with maker {maker}')
                        continue
                    elif index-maker > 1:
                        df.loc[df['ind']==index, 'vendor_syn'] = word
                        checker = False
                        print('Should not be possible yet')
                        continue
                else:
                    maker = 0
                    checker = True
                df.loc[df['ind']==index, 'vendor_syn'] = word
    #Check if fully completed?
    if (~(df.vendor_syn == '')).sum() < (~(df.vendor_mod_Syn == '')).sum():
        number = {(~(df.vendor_mod_Syn == '')).sum() - (~(df.vendor_syn == '')).sum()}
        print(f'There are {number} Synonyms where the check failed.')
    df.drop(['ind', 'vendor_mod_Syn'], axis=1, inplace=True)
    df = spellcheck(df)

    ###################
    ### consolidate ###
    ###################
    # log manipulations of the vendor string
    df[[col + '_fin' for col in df.columns[1:]]] = df[df.columns[1:]].copy()
    df.vendor_precl_fin.where(~(df.vendor_precl == df.vendor_prep) , '', inplace=True)
    df.vendor_del_fin.where(~(df.vendor_prep == df.vendor_del) , '', inplace=True)
    df.vendor_poscl_fin.where(~(df.vendor_del == df.vendor_poscl) , '', inplace=True)
    df.vendor_syn_fin.where(~(df.vendor_poscl == df.vendor_syn) , '', inplace=True)
    df_mod_col = [col for col in df.columns if '_fin' in col]
    df_mod_col.insert(0,'vendor')
    df[df_mod_col].to_parquet('log_vendor_<time>_<runID>.parquet')
    # generate final column modified
    df['vendor_modified'] = ''
    df.vendor_modified.where(~(df.vendor_modified == '') , df.vendor_syn_fin, inplace=True)
    df.vendor_modified.where(~(df.vendor_modified == '') , df.vendor_poscl, inplace=True)
    if len(df.groupby(df.index)['vendor_modified'].apply(list)
           .reset_index(drop=True))!= len(df_load.vendor.unique()):
        print('WARNING: colum modified as not as many entries as the original one! ')
    df_fin = pd.DataFrame()
    df_fin['vendor_modified'] = df.groupby(df.index)['vendor_modified'].apply(list).reset_index(
        drop=True)
    df_fin['vendor_modified'] = df_fin['vendor_modified'].str.join(', ')
    df_fin.vendor_modified.replace(r'(, ){2}', ', ', regex=True, inplace=True)
    df_fin.vendor_modified.replace(r'\b,\s?$', '', regex=True, inplace=True)
    df_fin.index = df_load.vendor.unique()
    # Update inital DataFrame
    df_load.vendor_modified = df_load['vendor'].map(df_fin['vendor_modified'])
    return df_load

def spellcheck(df :pd.DataFrame):
    '''Uses the spellchecker function'''
    print('add column df["vendor_mod_Spell"]: not implemented yet')
    return df

# helperfunctions
def remove_special_characters(text):
    '''The remove_special_characters function is used to clean up the product names. 
    As serial numbers are often separated by a hyphen (e.g. Simatic 7SR1205-2JA87-1CAO/EE), 
    the structure is retained in order to be able to make a better statement about the equality 
    of two product strings later during matching  with analyze_structure.'''
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

def clean_dataframe_product(df):
    '''
    filepath='./data/knownBranches.json'
    known_branches = ['ERROR: replace me since load_known_branches(filepath) is not working anymore!']
    regex_patterns = known_branches.get('product_regex', {})
    function_keywords = known_branches.get('function_keywords', [])
    '''
    regex_patterns = r''
    function_keywords = []

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

def remove_letters_from_string(text):
    '''The purpose is to extract only the numerical parts of the version number.
     As the matching later refers to the "dot" as a separator, care is taken 
     to ensure that, for example, "3.4.5.RevA" is converted to 
     "3.4.5" and not to "3.4.5."'''
    cleaned_text = re.sub(r'[^0-9.]', '', text)
    if cleaned_text and cleaned_text.endswith('.'):
        cleaned_text = cleaned_text[:-1]  # Remove "dot"
    return cleaned_text or None
