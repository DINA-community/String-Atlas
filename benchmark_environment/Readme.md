# Installation

## Quick-Start auf selben System

Die Demo ist für den lokalen Betrieb verfügbar

### Manuell

```text
cd resources
git clone https://github.com/cisagov/CSAF
# delete some years for faster processing
cd ..
cd docker-run-api
docker-compose up
```

### Scripted installation

```
bash demo.sh
```

Im Script werden nur CSAF Dokumente von 2024+ verwendet, um eine schnellere Bearbeitung zu ermöglichen.

## Nutzung

### API ready

Die Ausführung des Text Mining dauert ca. 30 Minuten. Warten Sie bis der Prozess durchgelaufen ist und mit

```text
api-1       |  * Serving Flask app 'app'
```

endet.

### Jypiter Notebook

csaf.ipynb öffnen im Editor und Testcode ausführen.

### Python scripte

Im Unterordner `cli_environment` die requirements installieren

```
python -m pip install -r requirements.txt
```

#### Examples

**Produkttypen als Listenargumente abfragen**

run_query.py testet die Matcher-Götterdämmerung-API über mehrere Texte die Kommagetrennt und in Anführungszeichen als Argument mitgeliefert werden.

```bash
python run_query.py "S7-1500, Siemens SIMATC S7-1500"
```

Als Ergebnis wird für jeden Text (Query) ein Vorschlag für den normalisierten Produkttyp in der darunterliegenden Zeile zurück gegeben.

```
--------
Query: S7-1500
SIMATIC S7-1500
--------
Query: Siemens SIMATC S7-1500
SIMATIC S7-1500
```

**Produkttypen als Listenargumente abfragen**

Für das Skript run_csv_benchmark.py wird ein CSV-Dateiname als Argument mitgeliefert, die in einem vorgegebenen Format Produkttypen für das Benchmarking vorgibt (siehe test_strategy.csv).
Die leeren Spalten in den Test-Zeilen werden automatisiert befüllt, soweit möglich und diese Texte als Query an die Matcher-API gesendet.

```bash
python run_csv_benchmark.py ../test_strategy.csv
```

Beispiel-Terminalausgabe:
```
Total number of test cases: 54
Test - Lexical errors - 17 from 23 cases succeeded
Test - Different Spelling - 15 from 19 cases succeeded
Test - Format errors - 6 from 7 cases succeeded
Test - Placeholder - 3 from 5 cases succeeded
following suggestions are not matched:
{'SIMATIC S7-200', 'SIMATIC S7 F Systems V6.3'}
```
Die erzeugte Datei results_<datum und uhrzeit>.csv beinhaltet die Statistik der Ergebnisse der Benchmark-Tests mit den Zeitangaben in Millisekunden (ms).

Die erzeugte Datei details_<datum und uhrzeit>.csv beinhaltet die Details der Ergebnisse und den dazugehörigen abgefragten Werten der Benchmark-Tests.

