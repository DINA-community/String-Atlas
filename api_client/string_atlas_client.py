import json
import requests

class StringAtlasAPIClient:
    config = None
    API_KEY = None
    API_PORT = None
    API_HOST = None
    API_HOST_URL_SCHEME = None

    ENDPOINT_PRODUCT_TYPE = '/api/product_type'
    ENDPOINT_MAPPING_CONVENTIONAL = '/api/mapping_columns_conventional'
    ENDPOINT_MAPPING_WITH_MINER = '/api/mapping_columns_with_miner'
    ENDPOINT_MAPPING_WITH_MINER_NORMALIZE = '/api/mapping_columns_with_miner_normalize'
    ENDPOINT_MATCH_PRODUCT_ROW = '/api/match_product_row'
    ENDPOINT_MATCH_VENDOR = '/api/match_vendor'

    def __init__(self, config):
        self.API_KEY = config['API']['API_KEY']
        self.API_PORT = config['API']['API_PORT']
        self.API_HOST = config['API']['API_HOST']
        self.API_HOST_URL_SCHEME = config['API']['API_HOST_URL_SCHEME']

    def request_product_type(self, token):
        # TODO injection schutz
        response = requests.post(url=self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_PRODUCT_TYPE,
                                 headers={'Content-Type': 'application/json',
                                          'X-API-KEY' : self.API_KEY},
                                 data=json.dumps({"token": token}))
        return response

    def request_product_type_row(self, row_data:dict):
        print('request: '+self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MATCH_PRODUCT_ROW)
        response = requests.post(url=self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MATCH_PRODUCT_ROW,
                                 headers={'Content-Type': 'application/json',
                                          'X-API-KEY' : self.API_KEY},
                                 data=json.dumps(row_data))
        return response

    def match_vendor_by_row(self, searched_tokens:dict):
        """
        searched_tokens[column] = search_text
        """
        print('request: '+self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MATCH_VENDOR)
        response = requests.post(url=self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MATCH_VENDOR,
                                 headers={'Content-Type': 'application/json',
                                          'X-API-KEY' : self.API_KEY},
                                 data=json.dumps(searched_tokens))
        return response

    def request_brands(self, row_data:dict):
        print('request: '+self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MATCH_PRODUCT_ROW)
        response = requests.post(url=self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MATCH_PRODUCT_ROW,
                                 headers={'Content-Type': 'application/json',
                                          'X-API-KEY' : self.API_KEY},
                                 data=json.dumps(row_data))
        return response

    def request_oui_mac(self, row_data:dict):
        print('request: '+self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MATCH_PRODUCT_ROW)
        response = requests.post(url=self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MATCH_PRODUCT_ROW,
                                 headers={'Content-Type': 'application/json',
                                          'X-API-KEY' : self.API_KEY},
                                 data=json.dumps(row_data))
        return response

    def mapping_conventional(self, columns:[], values:[]):
        print('request: ' + self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MAPPING_CONVENTIONAL)
        document_data = {'columns': columns, 'values': values}
        response = requests.post(url=self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MAPPING_CONVENTIONAL,
                                 headers={'Content-Type': 'application/json',
                                          'X-API-KEY': self.API_KEY},
                                 data=json.dumps(document_data))
        return response

    def mapping_with_miner(self, columns:[], values:[]):
        document_data = {'columns': columns, 'values': values}
        print('request: ' + self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MAPPING_WITH_MINER)
        response = requests.post(url=self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MAPPING_WITH_MINER,
                                 headers={'Content-Type': 'application/json',
                                          'X-API-KEY': self.API_KEY},
                                 data=json.dumps(document_data))
        return response

    def mapping_with_miner_normalize(self, columns:[], values:[]):
        document_data = {'columns': columns, 'values': values}
        print('request: ' + self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MAPPING_WITH_MINER_NORMALIZE)
        response = requests.post(url=self.API_HOST_URL_SCHEME + ':' + self.API_PORT + self.ENDPOINT_MAPPING_WITH_MINER_NORMALIZE,
                                 headers={'Content-Type': 'application/json',
                                          'X-API-KEY': self.API_KEY},
                                 data=json.dumps(document_data))
        return response


