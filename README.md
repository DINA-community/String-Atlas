# String-Atlas

In general String-Atlas is a collection of modules used for matching CSAF documents with assets. This collection was designed for the DINA-community project, surrounding Malcolm, DDDC and CSAF-Handler.

> :exclamation: This is a developing state at the moment and not ready to use. 

## Development

At the moment, the whole framework is under reconstruction aiming to provide better methods to harmonized asset data. This allows a fast mapping with CSAF documents as well as ensure that the
asset data on an operator side is harmonized in that way that different data models and descriptions have no negativ effect on mapping assets with CSAF documents-

The development state can be tested under the benchmark_environment following the [Installation Guide](benchmark_environment/Readme.md).

The general idea is to extract information from any database and map it to a basic classification, as shown below. Based on this initial mapping, the matching routine of the matching agent can then be used to identify compatible assets using more specific attributes, such as the firmware version.  

![Manufacturer](https://img.shields.io/badge/Manufacturer-green?style=plastic)
![Device Family](https://img.shields.io/badge/Device_Family-darkgreen?style=plastic)
![Model](https://img.shields.io/badge/Model-green?style=plastic)
![Model Series](https://img.shields.io/badge/Model_Series-grey?style=plastic)
![Further Specifications](https://img.shields.io/badge/Model_Specification-red?style=plastic)

The color is intended to display the matching reason. To keep it simple, only a few
reasons are provided such as

| Confidence                                                                    | Description                                                       |
| ---                                                                           | ---                                                               |
| ![Exact](https://img.shields.io/badge/Exact-darkgreen?style=plastic)          | Exact match                                                       |
| ![Indirect](https://img.shields.io/badge/Indirect-green?style=plastic)        | Indirect match e.g. manufacturer is Siemens for model SCALANCE    |
| ![Inconclusive](https://img.shields.io/badge/Inconclusive-grey?style=plastic) | No match with sufficient confidence (e.g. Model Specifications)   |
| ![No Match](https://img.shields.io/badge/No_Match-red?style=plastic)          | Confidence is below a certain value                               |

Also, this approach can be used in the string_miner and string_checker. Please note, that the classification is not fixed. Especially, the sufficient confidence has to be determine.

## Status of Revision

The following scripts are used in other repositories and will be replaced when the revision takes place.

|Module                 | Status                                                                                | Action                                                                |
|---                    |---                                                                                    | ---                                                                   |
|process_csaf_files     | Deprecated                                                                            | Replace with a more reliable and higher-performance implementation.   |
|string_checker         | Major revision required [#2](https://github.com/DINA-community/String-Atlas/issues/)  | Await completion of the normalization module before refactoring.      |
|string_helperfunctions | Stable                                                                                | Refactor and align with the normalization framework.                  |
|string_miner           | Major revision required                                                               | Defer to the backlog for future revision.                             |
|string_normalization   | [issue #3 #4 #5](https://github.com/DINA-community/String-Atlas/issues/)              | In active development                                                 |
|string_synonym         | Stable                                                                                | Update to integrate the normalization framework.                      |

## Contribution

The initial version of the string_normalizaton.py, process_csaf_files.py and string_matching were set up by Benjamin Wensky.

## Dependencies

Some functions will need specific data for string processing. Those can be found in [String-Sysiphos](https://github.com/DINA-community/String-Sysiphos).

## License

The software was developed on behalf of the [BSI](https://www.bsi.bund.de) \(Federal Office for Information Security\)

Copyright &copy; 2024-2026 by DINA-Community Apache 2.0 License. [See License](/LICENSE)
