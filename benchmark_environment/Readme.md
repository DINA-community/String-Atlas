# Installation

## Quick Start on the Same System

The demo is available for local use.

### Manual

```bash
cd resources
git clone https://github.com/cisagov/CSAF
# delete some years for faster processing
cd ..
cd docker-run-api
docker compose up
```

### Scripted Installation

```bash
bash demo.sh
```

The script only uses CSAF documents from 2024 onwards to allow faster processing.

## Usage

### API Ready

The text mining process takes several minutes up to 20 minutes for a PC without GPU. Wait until the process has completed and the output ends with:

```bash
api-1       |  * Serving Flask app 'app'
api-1       |  * Debug mode: on
```

### Jupyter Notebook

Open `csaf.ipynb` in your editor and run the test code.

### Python Scripts

```bash
cd cli_environment
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

use the `run_query.py` to test single strings:

```bash
python run_query.py "S7-1500, Siemens SIMATC S7-1500"
```

or `run_csv_benchmark.py` for a full benchmark test

```bash
python run_csv_benchmark.py ../<Filename>
```

At the moment, there are two files for testing: `test_strategy.csv` and `benchmark_selection.csv`

When running the scripts later, ensure that the .venv is active. Otherwise, the scripts might not work.

## Setup Benchmark Files

The benchmark takes each product and generates deviations from that string according to the test type. In the following table, this is illustrated for the string `SIMATIC S7-1500`

| Test Type               | Error Type                                               |  Example |  Short Description |
|-------------------------|----------------------------------------------------------|---------------------|----------------------|
| Test – Lexical errors   | Lexical errors – wrong letter typing                     | SIMATIC D7-1500                  |    Substitutes a character with wrong single keyboard neighbour character                |
| Test – Lexical errors   | Lexical errors – lower and uppercase                     | sIMATIC S7-1500                     |  lower uppercase characters or uppers lowercase character s                   |
| Test – Lexical errors   | Lexical errors – insertion redundant characters          |  SIMATICC S7-1500                  |  Insert a duplicate of a following random character               |
| Test – Lexical errors   | Lexical errors – insertion additional characters         | SIMATICA S7-1500                    | Insert a random character at random position                     |
| Test – Lexical errors   | Lexical errors – deletion characters                     |   SIMATC S7 1500                  |   deletes a random character                   |
| Test – Lexical errors   | Lexical errors – transposed letters                      | SIMATCI S7 1500                    | Transposing two consecutive random characters                |
| Test – Lexical errors   | Lexical errors – missing token                           |   SIMATIC S7                  |     removes a random token. tokenizing is by spliting the text by  whitespaces or special characters (nonalphanumeric)               |
| Test – Lexical errors   | Lexical errors – number alpha mix                        |  SIMATIC 7S-1500                   |   Transposing two consecutive random characters with different types (alpha and numeric)                 |
| Test – Different Spelling | different spelling – special chars – whitespace replacement | SIMATIC S7 1500  |  a random special char is replaced by whitespace                   |
| Test – Different Spelling | different spelling – special chars – removed            |    SIMATIC S71500                 |  a random special char is removed                     |
| Test – Different Spelling | different spelling – whitespaces – removed between token |   SIMATICS7-1500                  |                       two random tokens are concated by removing seperating whitespace|
| Test – Different Spelling | different spelling – whitespaces – replacement with special char |    SIMATIC-S7-1500                 |   a random whitespace is substituted by a special char                   |
| Test – Different Spelling | different spelling – vendor                             |   Siemens => Siemens AG                |    different spelling for vendor names. for example with legal forms or other type of additional tokens                  |
| Test – Different Spelling | different spelling – lower and uppercase                |   simatic s7-1500                  |   lowercase a whole random token with alpha characters                   |
| Test – Different Spelling | different spelling – synonyms                           |   CPU => Processor                |   for certain product tokens are synonym used. Mot yet automated                |
| Test – Different Spelling | different spelling – abbreviations                      |   Siemens => Siem.                   |  abbreviations used for vendor or product tokens. Not yet automated                   |
| Test – Different Spelling | different spelling – wrong semantic                     |    ET S7-1500            |  The text contains tokens that do not semantically fit the product type. not yet automated.             |
| Test – Format errors    | format errors – underscore                               |  SIMATIC_S7_1500                   |   replacing whitespaces and specialchars with underscores                   |
| Test – Format errors    | format errors – multiple products in row                 |  Siemens SIMATIC S7-1500;  Siemens ET-200                    |   text containing multiple vendors and/or products. not yet automated                   |
| Test - Format errors    | format error - transposed token                          |  S7-1500 SIMATIC   |  Two random consecutive tokens are transposed                     |
| Test - Format errors    | format error – whitespaces – special char mixed          |  SIMATIC-S7-1500                    |  replaces witespaces with special chars                     |
| Test – Different Spelling | different spelling - acronym                             |  Programable Logic Controller => PLC                   |                      instead of tokens are acronym token used. not yet autoamted. |
| Test – Different Spelling | different spelling - full form for acronym              |   PLC => Programable Logic Controller                    |  text contains full form for acronym token                    |
| Test - Placeholder       | placeholder - content word                               |    S7-1500 SIMATIC CPU|   oneunnecessary placeholder word is added in text. not yet automated                   |
| Test - Placeholder       | placeholder - functional                                 |  S7-1500 brand SIMATIC                   |  a functional placeholder word with describes for example the consecutive tokens                    |
| Test - Placeholder       | placeholder - two content words                          | S7-1500 SIMATIC CPU PLC  |  two unnecessary placeholder words are added in text. not yet automated                     |
| Test - Placeholder       | placeholder - long content with unique not yet automated                    |   SIMATIC S7-1500 CPU 1511TF-1 PN ( 6ES7511-1UK01-0AB0)                  |  text contains a unique token which describes the product type exactly not yet automated                     |
| Test - Placeholder       | placeholder - long content                               |   S7-1500 SIMATIC CPU Programmable Logic Controller                  |  plenty placeholder words are added in text.   not yet automated                   |

## Evaluation

Running the scripts or looking at the runs given in the jupyter file, the current success rate is rather low. A automated evaluation will be provided.