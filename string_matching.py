'''Matching functions for a CSAF document and an asset'''

import re
import pandas as pd
from fuzzywuzzy import fuzz # License?
from Levenshtein import distance as levenshtein_distance # TODO geht nicht
from Levenshtein import ratio as levenshtein_ratio # TODO geht nicht
from collections import Counter



def tokenize_string(text):
    return re.findall(r'\b\w+(?:-\w+)*\b', text.lower())

def is_alphabetic(token):
    return token.isalpha()

def token_weight(token):
    if token.isalpha():
        return 1  # alphabetic only
    elif re.match(r'^\d+$', token):
        return 1  # numbers only
    else:
        return 1  # alphanumeric or with special characters

def match_vendor(vendor1, vendor2):
    ratio = 0
    if pd.isna(vendor1) or pd.isna(vendor2):
        return None  # no match if one of the values is missing
    # fuzz partial ratio
    #ratio = fuzz.partial_ratio(vendor1.lower(), vendor2.lower())
    #ratio = fuzz.ratio(vendor1.lower(), vendor2.lower())
    ratio = fuzz.token_sort_ratio(vendor1.lower(), vendor2.lower())
    
    return int(ratio)  # Keine Übereinstimmung

def tokenize_and_group(text):
    # Tokenize the text
    #tokens = re.findall(r'\b\w+(?:-\w+)*\b', text.lower())
    tokens = text.lower().split()
    # Initialize lists for token groups
    group_1 = []  # Alphabetical tokens
    group_2 = []  # Numeric tokens
    group_3 = []  # Other tokens
    # Iterate through tokens and assign to groups
    for token in tokens:
        if token.isalpha():
            group_1.append(token)
        elif token.isdigit():
            group_2.append(token)
        else:
            group_3.append(token)
    # Join tokens in each group into strings
    group_1_text = ' '.join(group_1)
    group_2_text = ' '.join(group_2)
    group_3_text = ' '.join(group_3)
    
    return group_1_text, group_2_text, group_3_text

def scale_percentage(percent, factor=1):
    # Check if the value is within the valid range
    if percent == None:
        return None
    elif percent < 0 or percent > 100:
        raise ValueError("Percentage must be between 0 and 100.")
    
    # Calculate the scaled value
    scaled_percent = max(0, 100 - (100 - percent) * factor)
    return int(scaled_percent)

def analyze_structure(s):
    pattern = ''
    for char in s:
        if char.isalpha():
            pattern += 'L'  # L (Letter)
        elif char.isdigit():
            pattern += 'N'  # N (Number)
        else:
            pattern += 'O'  # O (Other)
    return pattern

# match product_name or product_family- weighted
def match_product(name1, name2, weight_group_1=1, weight_group_2=1, weight_group_3=1, percentage_factor_group_3=1):
    # Neutral if either of the values is missing
    if pd.isna(name1) or pd.isna(name2) or name1 == '' or name2 == '':
        return None  
        
    # Check if one of the names is fully contained in the other
    if name1.lower() in name2.lower() or name2.lower() in name1.lower():
        return 100
    #return fuzz.token_sort_ratio(name1,name2)
    # Tokenize and group the texts
    group1_1, group1_2, group1_3 = tokenize_and_group(name1)
    group2_1, group2_2, group2_3 = tokenize_and_group(name2)
    
    # Calculate similarity group3 - alphanumeric
    if (group1_3 and group2_3):
        max_score = 100
        compared = False
        for i in group1_3.split():
            for j in group2_3.split():
                if len(i) == len(j) > 4:
                    if analyze_structure(i) == analyze_structure(j):
                        compared = True
                        #score = fuzz.ratio(i, j)
                        score = 100 if i == j else 0
                        #print (i,j)
                        if score < max_score:
                            max_score = score
        if compared == True:
            similarity_group_3 = max_score
            #similarity_group_3 = scale_percentage(similarity_group_3, percentage_factor_group_3)
        else: 
            similarity_group_3 = None
            group1_1 += " " + group1_3
            group2_1 += " " + group2_3
            #print (group1_1)
    else:
        similarity_group_3 = None
    
    # Calculate similarity for other groups
    similarity_group_1 = fuzz.token_set_ratio(group1_1, group2_1) if (group1_1 and group2_1) else None
    similarity_group_2 = fuzz.token_set_ratio(group1_2, group2_2) if (group1_2 and group2_2) else None
   
    

    # Weight the similarities
    numerator = 0
    denominator = 0
    if similarity_group_1 is not None:
        numerator += weight_group_1 * similarity_group_1
        denominator += weight_group_1
    if similarity_group_2 is not None:
        numerator += weight_group_2 * similarity_group_2
        denominator += weight_group_2
    if similarity_group_3 is not None:
        numerator += weight_group_3 * similarity_group_3
        denominator += weight_group_3

    weighted_similarity = numerator / denominator if denominator > 0 else 0
    return int(weighted_similarity)

# match product_version 
def match_version(version1, version2, version_range1):
    # score None represents neutral score.
    score=None
    # if version information indicates every version, set score to 100%, to indicate a match 
    if version1 == 'vers:all/*' or version2 == 'vers:all/*' or version_range1 == 'vers:all/*':
        score=100
        return score  # 'vers:all/*' represents wildcard for every version
    # if no version information is available, keep  score at 50%, to keep it neutral 
    elif pd.isna(version1) or pd.isna(version2) or version1 == '' or version2 == '':
        score=None
        return score  
    else:
        # Extract individual parts of the version numbers
        v1_list = list(version1.split('.'))
        v2_list = list(version2.split('.'))

        # Ensure both lists have the same length, append 'x' for missing values
        max_length = max(len(v1_list), len(v2_list))
        v1_list.extend(["x"] * (max_length - len(v1_list)))
        v2_list.extend(["x"] * (max_length - len(v2_list)))

        # Calculate the match for each segment
        similarity_scores = []
        for i in range(max_length):
            if (v1_list[i] == "x") or (v2_list[i] == "x"):
                similarity_scores.append(1) # 100% match for this segment, as no further version info is available
            elif v1_list[i] == v2_list[i]:
                similarity_scores.append(1)  # 100% match for this segment
            else:
                similarity_scores.append(0)
                break

        # Calculate a weighted average of the similarities
        # Earlier segments have more weight (e.g., Major version is more important than Minor)
        weights = [2**(max_length-i-1) for i in range(max_length)]
        weighted_similarity = sum(s*w for s, w in zip(similarity_scores, weights)) / sum(weights)

        return int(weighted_similarity * 100)  # Convert to percentage
        
# match keyword section
def match_keyword(keyword1, keyword2):
    if pd.isna(keyword1) or pd.isna(keyword2) or keyword1 == '' or keyword2 == '':
        return None  # Neutral if either of the values is missing
    elif keyword1.lower() in keyword2.lower() or keyword2.lower() in keyword1.lower():
        return 100 # Check if one of the names is fully contained in the other
    else:
        return 0 # no match, if values are available but do not match

def calculate_overall_score(vendor_score, product_name_score, product_family_score, version_score, keyword_score, vendor_threshold, product_family_threshold, product_name_threshold, keyword_threshold, version_threshold):
    # Check if vendor score is missing
    if vendor_score is None:
        return 0, "No Match vendor missing"
    # Check if vendor score meets threshold
    elif vendor_score >= vendor_threshold:
        # Check if product family score is missing
        if product_family_score is None:
            # Check if product name score is missing
            if product_name_score is None:
                return 0, "No Match Product Name and Family missing"
            # Check if product name score meets threshold
            if product_name_score >= product_name_threshold:
                # Check if version score exists and meets threshold
                if version_score is not None and version_score < version_threshold:
                    return 0, f"No Match - Version Score is below {version_threshold}% ({version_score}%)"
                return 1, "Match - Family Missing"
            # Check if product name score is within a certain range and version and keyword scores exist
            elif (product_name_threshold-20) <= product_name_score < product_name_threshold and version_score is not None and keyword_score is not None:
                # Perform version and keyword boost
                overall_score = (3*vendor_score + 2*product_name_score + version_score + keyword_score) / 7
                if overall_score >= keyword_threshold:
                    return 1, "Possible match - version and keyword boost"
            else:
                return 0, f"No match - Product name score is below {product_name_threshold}% ({product_name_score}%)"
        # Check if product family score meets threshold
        elif product_family_score >= product_family_threshold:
            # Check if product name score is missing
            if product_name_score is None:
                return 1, "Possible Match - Product Name missing"
            # Check if product name score meets threshold
            elif product_name_score >= product_name_threshold:
                # Check if version score exists and meets threshold
                if version_score is not None and version_score < version_threshold:
                    return 0, f"No Match - Version Score is below {version_threshold}% ({version_score}%)"
                else:
                    return 1, "Match - Product Name and Family is given"
            # Check if product name score is within a certain range and version and keyword scores exist
            elif (product_name_threshold-20) <= product_name_score < product_name_threshold and version_score is not None and keyword_score is not None:
                # Perform version and keyword boost
                overall_score = (3*vendor_score + 2*product_name_score + version_score + keyword_score) / 7
                if overall_score >= keyword_threshold:
                    return 1, "Possible match - version and keyword boost"
            else:
                return 0, f"No match: Product name score is below {product_name_threshold}% ({product_name_score}%)"
        else:
            return 0, f"No match: Product family score is below {product_family_threshold}% ({product_family_score}%)"
    # Check if vendor score is below threshold
    elif vendor_score <= vendor_threshold:
        return 0, f"No match: Vendor score is below {vendor_threshold}% ({vendor_score}%)"
    return 0, "Loop Error"



    # old version
    return int(overall_score)
    if vendor_score == 50:
        overall_score = 0
        return int(overall_score)

    # select higher or lower score if product_family or product_name is not available
    if product_name_score == 50 and product_family_score < 50:
        product_score = product_family_score
    elif product_family_score == 50 and product_name_score < 50:
        product_score = product_name_score
    elif product_family_score == 50 and product_name_score == 50:
        product_score = 0
    elif product_name_score == 50 or product_family_score == 50:
        product_score = max(product_name_score, product_family_score)
    else:
        product_score = (product_name_score + product_family_score) / 2   
    
    overall_score = (3*vendor_score + 2*product_score + version_score + keyword_score) / 7 
    
    return int(overall_score)
    
def filter_matching_vendors(df1, df2, vendor_threshold):
    vendors_in_df1 = set(df1['vendor_modified'])
    vendors_in_df2 = set(df2['vendor_modified'])
    
    common_vendors = set()
    for vendor1 in vendors_in_df1:
        for vendor2 in vendors_in_df2:
            if match_vendor(vendor1, vendor2) is None:
                continue            
            elif match_vendor(vendor1, vendor2) >= vendor_threshold:
                common_vendors.add(vendor1)
                common_vendors.add(vendor2)
    
    df1_filtered = df1[df1['vendor_modified'].isin(common_vendors)]
    df2_filtered = df2[df2['vendor_modified'].isin(common_vendors)]
    
    return df1_filtered, df2_filtered

def calculate_similarities(df1, df2, vendor_threshold, product_family_threshold, product_name_threshold, keyword_threshold, version_threshold):
    # vendor filtering for performance boost
    df1, df2 = filter_matching_vendors(df1, df2, vendor_threshold)
    
    similarities = []
    for index1, row1 in df1.iterrows():
        for index2, row2 in df2.iterrows():
            # Berechnung der individuellen Scores
            vendor_score = match_vendor(row1['vendor_modified'], row2['vendor_modified'])
            # Skipped if manufacturer does not match
            if vendor_score is None:
                product_name_score = product_family_score = version_score = keyword_score = 0
                continue
            elif vendor_score < vendor_threshold:
                product_name_score = product_family_score = version_score = keyword_score = 0
                continue
            #debugging zeile um alle vendor scores 100 zu entfernen
            #elif vendor_score == 100:
                product_name_score = product_family_score = version_score = keyword_score = 0
                continue
            elif vendor_score >= vendor_threshold: 
                product_name_score = match_product(row1['product_name_modified'], row2['product_name_modified'],1,1,2,1)
                product_family_score = match_product(row1['product_family_modified'], row2['product_family_modified'])
                version_score = match_version(row1['product_version_modified'], row2['product_version_modified'], row1['product_version_range_modified'])
                keyword_score = match_keyword(row1['function_keywords_found'], row2['function_keywords_found']) 

            # Calculcate Overall Score
            match, reason = calculate_overall_score(vendor_score, product_name_score, product_family_score, version_score, keyword_score, vendor_threshold, product_family_threshold, product_name_threshold, keyword_threshold, version_threshold)
                       
            similarities.append({
                'Vendor 1': row1['vendor'],
                'Vendor 2': row2['vendor'],
                'Vendor 1 modified': row1['vendor_modified'],
                'Vendor 2 modified': row2['vendor_modified'],
                'Vendor Score': vendor_score,
                'Product Name 1_orig': row1['product_name'],
                'Product Name 2_orig': row2['product_name'],
                'Product Name 1': row1['product_name_modified'],
                'Product Name 2': row2['product_name_modified'],
                'Product Name Score': product_name_score,
                #'Product family 1_orig': row1['product_family'],
                #'Product family 2_orig': row2['product_family'],
                #'Product family 1': row1['product_family_modified'],
                #'Product family 2': row2['product_family_modified'],
                'Product family Score': product_family_score,
                'function keywords 1': row1['function_keywords_found'],
                'function keywords 2': row2['function_keywords_found'],
                'keyword score': keyword_score,
                'Version 1 modified': row1['product_version_modified'],
                'Version 2 modified': row2['product_version_modified'],
                'Range 1 modified' : row1['product_version_range_modified'],
                'Version Score': version_score,
                'Filename 1': row1['filename'],
                'Filename 2': row2['filename'],
                'Overall Score': match,
                'Reason' : reason
            })
    return pd.DataFrame(similarities)
