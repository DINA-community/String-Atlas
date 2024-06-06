# String-Sisyphos

For normalisation of input data the following files are provided. They are used for the netbox plugin [DDDC](../DDDC-Netbox-plugin) and for the intented CSAF Handler.

## Usage

While the functions are explained in the code itself, some adjustments must be made when executing the code itself.

### process_csaf_files.py

In the last line the path to directory, where the CSAF file(s) are, have to be added.

 ```text
df = process_csaf_sources(get_csaf_sources(<path to directory>))
 ```

 **Note**: the function `find_file` of the helperfunctions.py will search at the folder and the upper folder *data* amd *String-Sysiphos*.

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

### string_spellchecker.py

  no edition information provided at the moment

### string_synonym.py

  provides a class for synonym checks

## Dependencies

Some functions will need specific data for string processing. Those can be found in String-Sysiphos...
