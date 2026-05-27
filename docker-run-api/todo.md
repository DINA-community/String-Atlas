- [x] Bei Neustart Memory setzen in redis -> thesis relevant zusammen mit Updatemechanismus
- [x] Warnungen für df raus -> nicht thesis relevant
  - gruppieren nach Regex
    "1511TF-1" gibt es
    "1511TF-2"  -> finden 
  ACHTUNG: Gruppierung läuft erst ab bestimmten Semantics Token -> nochmal anpassen 

Gruppierung der Token im CorpusManager nochmal anpassen

TOOD Optimierung was noch ausgeführt werden muss überhaupt in csaf init

Custom Json Strategie die aus dem Sysiphos kommt
- Annotation kann itereieren über last_node -> d.h. wenn level > 3. Ebene ist kann man noch auf -3 Ebene zugreifen um rückwärtsvergliche zu machen
- und man kann mit zurückgegebenen level nachträglich annotieren
- am besten über json syntax



Danach def visit nochmal durhcgehen mit for schleife und items
siehe:
````
    def visit(self, node):
        self.structure['product_types'] = []
        self._visit_children(node)

        # save group regex
        for full_regex, product_types in self.product_type_list.items():
            for product_type, item in product_types.items():
                print(product_types)
                print(full_regex, product_type, item)

                # product_type: "SENTRON 3 KC ATC6 Expansion Module Ethernet"
                """
                {'annotations': [[], None, None, None, None, None, None],
                 'group': [False, True, False, False, False, False, False],
````
- sysiphos -> rechtsformen unternehmen.
- annotationen und types aus sysiphos einpflegen lassen, antatt physical nur. CPU, entity, beschreibung. JSON Format überlegen
- annoation aus nltk usw.

- outlier wird erkannt wenn string miner anderer type ermittelt als als nächstes vorgeschlagen -> State maschine
  - annotation -> outlier, token prefix rausschmeissen wenn prefix
- TODO right strip "("

**Matcher Komponente**
- brand und series werden nicht gematcht -> mehrere Ergebnisse liefern
  - mehrfachvorschläge
- Kombinierte Eingrenzung
  - PN -> eingrenzung auf vendor, brand, series möglich, in kombination mit andern
- Vendor Funktion
- Producttype Funktion
  - Vendor mitschicken 

# Nächstes Ziel
- Samstag: andere hersteller auch initialisieren
  - ZUERST HIER weiter python /app/normalizer/background_service/init_process_csaf_files.py
  - Durchlauf aktuell Dauerschleife mit Siemens und Mxq... recursive schleife -> vendor ermitteln wo es hakt
- Herstellerbezeichnung und Produktnamen mit Hersteller inbegriffen
  - OUI Lookup in Redis und über API anfragen mit Synonyme  
    - vendor suche bei matcher
  - Funktionen die überprüfen ob 1. bis n wort zu hersteller gehört oder zu synoynmen, von links nach rechts pflicht 
  - vendor werden nicht erkannt!! sondern als brand
  - Synonme z.B Großschreibung mit OUI abgleichen
- Sementicas _ Vednor  und VendorSynoynym(Part)
  - Hersteller Synonymdatenbank, bei gleichen Zeichen aber case sensitive -> übernahme von OUI Tabelle des jeweiligen Tokens
  - z.b. mit , 'Siemens Healthineers, Siemens' wie finde ich Tochterunternehmen ?
  - hier nochmal ansetzen bei produktnamen erkennen ob hersteller, following word usw.
    - outlier wird erkannt wenn string miner anderer type ermittelt als als nächstes vorgeschlagen -> State maschine
  - annotation -> outlier, token prefix rausschmeissen wenn prefix
  - 'PEPPERL+FUCHS' und 'Pepperl+Fuchs' -> Groß klein -> ist beides in CSAF
    - Durch Benutzereingabe verknüpfung -> Lerneffekt -> bezogen auf alle ermittelten Synonyme -> über OUI als ID matchen
 ````
  - 'Siemens'[b] -> wird als Brand angezeigt
                'SIMATIC'[series - [[]]]
                'OA'[series - [[]]]
                                                                'V3.14'[sub_series - 6 - [['version_identifier_and_version']]]
                                                                'V3.17'[sub_series - 6 - [['version_identifier_and_version']]]
    - Version wird nicht sofort korrigiert                                                                
````
  
# Letztes Ziel

- Plugin mit Spellchecker -> Lerneffekt Rückwärts
- Lerneffekt exportierbar machen
- OUI Daten automatisiert anbinden

- Doku

## Clean Code
- TODO Kommentare in python richtig verwenden für parameters, es ist character type


- matches zählen und counten
muss -> "000D81","Pepperl+Fuchs GmbH","Lilienthalstraße 200","Mannheim    68307","DE" ,matchen

- 
- 
  - Synonyme dazu lernen durch Benutzereingabe -> mit MAC von OUI matchen
      - Bugs:
      
        - save funktioniert noch nicht da tree objekt immer überschrieben wird in member variable
- es ist dasselbe Wort zu Begin als Brand:
````
1. Beispiel vendor "ABUS"
- 'PowerAgent'[b]
'PowerAgent'[b]
'DCMTK'[b]
'PowerAgent'[b]

2. Beispiel: vendor "ABUS"
"name": "ABUS TVIP: 20000-21150",
"name": "ABUS TVIP",

3. Beispiel mit Version
'911'[b]
                'Emergency'[series - [[]]]
                                'Gateway'[series - [[]]]
                                                '('[parentheses_start - [[]]]
                                                                'EGW'[parentheses_feature_static - [[]]]
                                                                                ')'[parentheses_end - [[]]]
                                                                                                'V4.X'[sub_series - 2 - [[]]]
                                                                                                'V5.X'[sub_series - 2 - [[]]]
                                                                                                'NAM'[series - [[]]]
````


- über vendor optional das matching einschränken


- Update Mechanismus für CSAF Corpus - Lerneffekt separate speichern und jedes mal einfließen lassen
- Lerneffekt über Plugin mitteilen
- DB-Adapter für Plugin
- Print nicht mehr anzeigen, nur Meldung das fertig
- außer man hat evironment verbose_casf
- vendor key values erstellen
- synonyme erstellen
- Lerneffekt exportieren können für Übertrag
- Verbose Debug für Print Tree only
- SSH Debug entfernen
- In Redis Group Pattern erzeugen mit Key und Verweis auf Producttype Index
- Weitere csaf quellen
- TODO für Thesis nach verschiedene Autoren berücksichtigen


A value is trying to be set on a copy of a slice from a DataFrame.
Try using .loc[row_indexer,col_indexer] = value instead

- Skript background_services wird nicht gefunden?
- Words:
    - Equipment
    - Maintanance
- final auf schwachstellen untersuchen

# TODO
self.product_tree = vendor_tree