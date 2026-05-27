# Füge das Parent Directory zu sys.path hinzu
import sys, os
import unittest
import json

import pandas as pd
from header_field_mapper.field_mapper import FieldMapper

current_dir = os.path.dirname(os.path.abspath(__file__))
config_mapping_file = os.path.join(current_dir, 'config_data_mapping.json')
with open(config_mapping_file, 'r') as file:
    # Lade den Inhalt der Datei in ein Python-Objekt
    config = json.load(file)


class TestHeaderFieldMapper(unittest.TestCase):
    records = [
        {'description': '', 'device_family': 'RSPE30', 'device_name3': 'sw-process', 'device_role': 'Switch',
         'ip_address': '192.168.10.1', 'oui': 'EC:74:BA', 'mac_address': 'EC:74:BA:52:A2:C4',
         'manufacturer': 'Hirschmann',
         'source': 'testinput'},
        {'description': '', 'device_family': 'RSPE30', 'device_name3': 'sw-process', 'device_role': 'Switch',
         'ip_address': '192.168.10.1', 'oui': 'EC:74:BA', 'mac_address': 'EC:74:BA:52:A2:C4',
         'manufacturer': 'Hirschmann',
         'source': 'testinput'},
        {'description': '', 'device_family': 'ET200-1515SP', 'device_name3': 'sps-1', 'device_role': '',
         'ip_address': '192.168.10.3', 'oui': 'EC:74:BA', 'mac_address': 'AC:64:17:48:AC:0A', 'manufacturer': 'Siemens',
         'source': 'testinput'},
        {'description': '', 'device_family': 'S7-1200', 'device_name3': 'sps-2', 'device_role': '',
         'ip_address': '192.168.10.12', 'oui': 'EC:74:BA', 'mac_address': 'E0:DC:A0:4A:C0:94',
         'manufacturer': 'Siemens',
         'source': 'testinput'},
        {'description': '', 'device_family': 'ET200-1512SP', 'device_name3': 'sps-3', 'device_role': '',
         'ip_address': '192.168.10.13', 'oui': 'EC:74:BA', 'mac_address': 'AC:64:17:48:AC:AD',
         'manufacturer': 'Siemens',
         'source': 'testinput'},
        {'description': '', 'device_family': 'S7-314', 'device_name3': 'sps-safety', 'device_role': 'Safety SPS',
         'ip_address': '192.168.10.14', 'oui': 'EC:74:BA', 'mac_address': 'AC:64:17:48:3A:89',
         'manufacturer': 'Siemens',
         'source': 'testinput'},
        {'description': 'PHOENIX_a8:26:a7', 'device_family': 'AXL F BK PN', 'device_name3': 'bk-1',
         'device_role': 'media gateway', 'ip_address': '192.168.10.7', 'oui': 'EC:74:BA',
         'mac_address': '00:a0:45:a8:26:a8',
         'manufacturer': 'Phoenix Contact', 'source': 'testinput'},
        {'description': 'WAGOKont_43:b5:c0', 'device_family': '750-375', 'device_name3': 'bk-2',
         'device_role': 'media gateway', 'ip_address': '192.168.10.22', 'oui': 'EC:74:BA',
         'mac_address': '00:30:DE:43:B5:C6',
         'manufacturer': 'Wago', 'source': 'testinput'},
        {'description': 'RobertBo_1e:e8:af', 'device_family': 'R-IL PN BK', 'device_name3': 'bk-3',
         'device_role': 'media gateway', 'ip_address': '192.168.10.23', 'oui': 'EC:74:BA',
         'mac_address': '00:60:34:1E:EC:A5',
         'manufacturer': 'Bosch-Rexroth', 'source': 'testinput'},
        {'description': 'Softing_33:09:78', 'device_family': 'uaGate', 'device_name3': 'opcua-gw',
         'device_role': 'media gateway', 'ip_address': '192.168.10.10', 'oui': 'EC:74:BA',
         'mac_address': '00:06:71:33:09:78',
         'manufacturer': 'Sotfing', 'source': 'testinput'},
        {'description': 'KUNBUS_01:16:d5', 'device_family': 'RevPi Core3', 'device_name3': 'opcua-io-env',
         'device_role': 'OPC UA Server', 'ip_address': '192.168.10.26', 'oui': 'EC:74:BA',
         'mac_address': 'B8:27:EB:E1:5E:47',
         'manufacturer': 'Kunbus', 'source': 'testinput'},
        {'description': '', 'device_family': 'MIS340', 'device_name3': 'motor-scheibe', 'device_role': 'actuator',
         'ip_address': '192.168.10.24', 'oui': 'EC:74:BA', 'mac_address': '54:E3:B0:00:D1:E3', 'manufacturer': 'JVL',
         'source': 'testinput'},
        {'description': '', 'device_family': 'MIS340', 'device_name3': 'motor-aufzug', 'device_role': 'actuator',
         'ip_address': '192.168.10.25', 'oui': 'EC:74:BA', 'mac_address': '54:E3:B0:00:D1:E0', 'manufacturer': 'JVL',
         'source': 'testinput'},
        {'description': '', 'device_family': 'Simatic TP700 Comfort', 'device_name3': 'hmi', 'device_role': 'HMI',
         'ip_address': '192.168.10.31', 'oui': 'EC:74:BA', 'mac_address': 'AC:64:17:4B:4B:E6',
         'manufacturer': 'Siemens',
         'source': 'testinput'},
        {'description': '', 'device_family': '', 'device_name3': 'Io-device', 'device_role': '',
         'ip_address': '192.168.10.27', 'oui': 'EC:74:BA', 'mac_address': '00:07:46:80:EF:F2', 'manufacturer': 'Turck',
         'source': 'testinput'},
        {'description': '', 'device_family': 'ET200-1515SP', 'device_name3': 'sps-1-host', 'device_role': '',
         'ip_address': '192.168.10.11', 'oui': 'EC:74:BA', 'mac_address': 'AC:64:17:46:C6:CA',
         'manufacturer': 'Siemens',
         'source': 'testinput'}]

    records_standard_heterogen = [
        {'description': '', 'device_family': 'RSPE30', 'device_name3': 'sw-process', 'device_role': 'Switch',
         'ip_address': '192.168.10.1', 'oui': 'EC-74-BA', 'mac_address': 'EC:74:BA:52:A2:C4',
         'manufacturer': 'Hirschmann',
         'source': 'testinput'},
        {'description': '', 'device_family': 'RSPE30', 'device_name3': 'sw-process', 'device_role': 'Switch',
         'ip_address': '192.168.10.1', 'oui': 'EC-74-BA', 'mac_address': 'EC:74:BA:52:A2:C4',
         'manufacturer': 'Hirschmann',
         'source': 'testinput'},
        {'description': '', 'device_family': 'ET200-1515SP', 'device_name3': 'sps-1', 'device_role': '',
         'ip_address': '192.168.10.3', 'oui': 'EC-74-BA', 'mac_address': 'AC:64:17:48:AC:0A', 'manufacturer': 'Siemens',
         'source': 'testinput'}
    ]

    records_test_vendor = [
        {'description': '', 'device_family': 'RSPE30', 'device_name3': 'sw-process', 'device_role': 'Switch',
         'ip_address': '192.168.10.1', 'oui': 'EC-74-BA', 'mac_address': 'EC:74:BA:52:A2:C4',
         'manufacturer': 'Datalogic',
         'source': 'testinput'},
        {'description': '', 'device_family': 'RSPE30', 'device_name3': 'sw-process', 'device_role': 'Switch',
         'ip_address': '192.168.10.1', 'oui': 'EC-74-BA', 'mac_address': 'EC:74:BA:52:A2:C4',
         'manufacturer': 'Datalogic',
         'source': 'testinput'},
        {'description': '', 'device_family': 'ET200-1515SP', 'device_name3': 'sps-1', 'device_role': '',
         'ip_address': '192.168.10.3', 'oui': 'EC-74-BA', 'mac_address': 'AC:64:17:48:AC:0A', 'manufacturer': 'Siemens',
         'source': 'testinput'}
    ]

    records_test_vendor_product = [
        {'description': '', 'device_family': 'RSPE30', 'device_name3': 'sw-process', 'device_role': 'Switch',
         'ip_address': '192.168.10.1', 'oui': 'EC-74-BA', 'mac_address': 'EC:74:BA:52:A2:C4',
         'manufacturer': 'Datalogic', 'product_name': 'S7-1212C', 'product_family': 'SIMATIC',
         'source': 'testinput'},
        {'description': '', 'device_family': 'RSPE30', 'device_name3': 'sw-process', 'device_role': 'Switch',
         'ip_address': '192.168.10.1', 'oui': 'EC-74-BA', 'mac_address': 'EC:74:BA:52:A2:C4',
         'manufacturer': 'Datalogic', 'product_name': 'S7-1200', 'product_family': 'SIMATIC',
         'source': 'testinput'},
        {'description': '', 'device_family': 'ET200-1515SP', 'device_name3': 'sps-1', 'device_role': '',
         'ip_address': '192.168.10.3', 'oui': 'EC-74-BA', 'mac_address': 'AC:64:17:48:AC:0A', 'manufacturer': 'Siemens',
         'source': 'testinput', 'product_name': 'S7-700', 'product_family': 'SIMATIC'
         }
    ]

    def test_dict_matcher_product_name(self):
        field_mapper = FieldMapper(config)
        df = pd.DataFrame(self.records_test_vendor_product)
        field_mapper.mapping_conventional(records=df)

    def test_mapping(self):
        field_mapper = FieldMapper(config)
        df = pd.DataFrame(self.records)
        field_mapper.mapping_conventional(records=df)

    def test_mapping2(self):
        field_mapper = FieldMapper(config)
        df = pd.DataFrame(self.records_standard_heterogen)
        field_mapper.mapping_conventional(records=df)

    def test_dict_matcher(self):
        field_mapper = FieldMapper(config)
        df = pd.DataFrame(self.records_test_vendor)
        field_mapper.mapping_conventional(records=df)




if __name__ == '__main__':
    unittest.main()
