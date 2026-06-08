# String-Atlas

In general String-Atlas is a collection of modules used for matching CSAF documents with assets. This collection was designed for the DINA-community project, surrounding Malcolm, DDDC and CSAF-Handler.

## New Release - Matcher 2026

At the moment, the whole framework is under reconstruction aiming to provide better methods to harmonized asset data. This allows a fast mapping with CSAF documents. Additionally, the data models is reviewed. In that way, hopefully everyone will understand the asset description despite using another data model.

The development state can be tested under the benchmark_environment following the [Installation Guide](benchmark_environment/Readme.md).

Furthermore, you can find information about a benchmark environment run in a Jupyter Notebook `csaf.ipynb`.

## Contribution

The initial version of the string_normalizaton.py, process_csaf_files.py and string_matching were set up by Benjamin Wensky.

## Dependencies

Some functions will need specific data for string processing. Those can be found in [String-Sysiphos](https://github.com/DINA-community/String-Sysiphos).

## License

The software was developed on behalf of the [BSI](https://www.bsi.bund.de) \(Federal Office for Information Security\)

Copyright &copy; 2024-2026 by DINA-Community Apache 2.0 License. [See License](/LICENSE)
