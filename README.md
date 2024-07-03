# String-Atlas

For normalisation of input data the following files are provided. They are used for the netbox plugin [DDDC](../../DDDC-Netbox-plugin) and for the intented CSAF Handler.

## Overview

At the moment, the repository consists of separated python modules. There is no modules yet, that uses the scripts together. This will take place in a new project while revising the modules step by step separately.

|module  | status |
|- |- |
|process_csaf_files     | need faster routines |
|string_checker         | #2 + major revision needed --> development in progress by another thesis |
|string_helperfunctions | stable |
|string_matching        | need major revision |
|string_miner           | major revision needed --> development in progress by another thesis|
|string_normalization   | need major revision #1 #3 #4 #5 -> branch: dev_normalization|
|string_synonym         | stable |

While the functions are explained in the code itself, some adjustments must be made when executing the code itself.

### process_csaf_files.py

In the last line the path to directory, where the CSAF file(s) are, have to be added.

 ```text
df = process_csaf_sources(get_csaf_sources(<path to directory>))
 ```

 **Note**: the function `find_file` of the helperfunctions.py will search at the folder and the upper folder *data* amd *String-Sysiphos*.

### string_checker.py

  no edition information provided at the moment

### string_helperfunctions.py
  
  The LogHandler class is used for all other functions where logging takes place.

  Chances in this file have impact on several other files. Be aware of the dependencies.

### string_matching.py

  string comparison (intented for CSAF matching).

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

The string_normalizaton.py and process_csaf_files.py and string_matching were set up by Benjamin Wensky.

## Dependencies

Some functions will need specific data for string processing. Those can be found in String-Sysiphos.

## License

The software was developed on behalf of the [BSI](https://www.bsi.bund.de) \(Federal Office for Information Security\)

Copyright &copy; 2024 by DINA-Community Apache 2.0 License. [See License](/LICENSE)
