# String-Atlas

> For normalisation of input data the following files are provided. They are used for the netbox plugin [DDDC](https://github.com/DINA-community/DDDC-Netbox-plugin) and for the intended CSAF Handler.
>
> :exclamation: This is a developing state at the moment and not ready to use.

## Overview

In general String-Atlas is a collection of modules used for matching CSAF documents with assets of a asset data base. This collection was designed for the DINA-community project, surrounding Malcolm, DDDC and CSAF-Handler.

![Flowchart_CSAFMatcher][fig_flow_new]

At the beginning, both datasets have to be adjusted for comparison. Therefore, the matching information (attributes) have to be mapped to the attributes used for the Netbox plugin [DDDC](https://github.com/DINA-community/DDDC-Netbox-plugin). This mapping is done in `process_csaf_files.py` as module *Flatten CSAF Data into Pandas DataFrame* and in the module `Database Mapping` \(not implemented yet\)

The module *DataCleaning/Standardisation* adjust the input data of both datasets for comparison. It shall be used in the Netbox plugin DDDC as well.

The matching process shall satisfy the CSAF Standard. Therefore, the functions in string_matching.py must be extended with regard to matching priorities \(Modi\) 1 and 3 in [Issue 593](https://github.com/oasis-tcs/csaf/issues/593) and matching priority 2 \(Modi-2\) must be adapted with regard to the data fields to be compared.

The *DataCleaning/Standardisation* adjust the input data of both datasets for comparison.

There is no modules yet, that uses the scripts together. This will take place in a new project while revising the modules step by step separately.

|module  | status |
|- |- |
|process_csaf_files     | deprecated |
|string_checker         | major revision needed [#2](https://github.com/DINA-community/String-Atlas/issues/)|
|string_helperfunctions | stable |
|string_miner           | major revision needed |
|string_normalization   | [issue #3 #4 #5](https://github.com/DINA-community/String-Atlas/issues/) |
|string_synonym         | stable |

### process_csaf_files.py

In the last line the path to directory, where the CSAF file(s) are, have to be added.

 ```text
df = process_csaf_sources(get_csaf_sources(<path to directory>))
 ```

 **Note**: the function `find_file` of the helperfunctions.py will search at the folder and the upper folder *data* amd *String-Sysiphos*.

### string_checker.py

  no edition information provided at the moment

### string_helperfunctions.py
  
  The LogStyle class is used for all other functions where logging takes place.

  Chances in this file have impact on several other files. Be aware of the dependencies.

### string_miner.py

  Extract attribute information out of a string.

### string_normalization.py

- delete prefix and suffix
- use synonyms and spellchecker

### string_synonym.py

  provides a class for synonym checks

## Setup

The modules have been tested with Ubuntu 22.04.

### Prerequisites

There are some packages that have to be installed by the user, in order to use some features in the mapping process.

 ```bash
  pip install levenshtein fuzzywuzzy collections inspect pprint
 ```

## Contribution

The `string_normalization.py` and `process_csaf_files.py` were set up by Benjamin Wensky.

## Dependencies

Some functions will need specific data for string processing. Those can be found in [String-Sysiphos](https://github.com/DINA-community/String-Sysiphos).

## License

The software was developed on behalf of the [BSI](https://www.bsi.bund.de) \(Federal Office for Information Security\)

Copyright &copy; 2024-2025 by DINA-Community Apache 2.0 License. [See License](/LICENSE)

[fig_flow_new]: ./images/Cleansing.svg
