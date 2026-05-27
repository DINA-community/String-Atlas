# String-Atlas

In general String-Atlas is a collection of modules used for matching CSAF documents with assets. This collection was designed for the DINA-community project, surrounding Malcolm, DDDC and CSAF-Handler.

## New Release - Matcher 2026

At the moment, the whole framework is under reconstruction aiming to provide better methods to harmonized asset data. This allows a fast mapping with CSAF. Additionally everyone understands the asset description hopefully despite different data models.

The development state can be tested under the benchmark_environment following the [Installation Guide](benchmark_environment/Readme.md).

Furthermore, you can find information about the benchmark environment you can run in a Jupyter Notebook in the folder there.

## Contribution

The string_normalizaton.py and process_csaf_files.py and string_matching were set up by Benjamin Wensky.

## Dependencies

Some functions will need specific data for string processing. Those can be found in [String-Sysiphos](https://github.com/DINA-community/String-Sysiphos).

## License

The software was developed on behalf of the [BSI](https://www.bsi.bund.de) \(Federal Office for Information Security\)

Copyright &copy; 2024-2026 by DINA-Community Apache 2.0 License. [See License](/LICENSE)

[fig_flow_new]: ./images/Cleansing.svg
