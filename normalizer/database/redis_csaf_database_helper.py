import re
import redis
import json
from pandas.core.dtypes.inference import is_float
from redis.commands.search.field import TextField, TagField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from matcher.lib.common import is_number
from .csaf_database_helper import CSAFDataBaseHelper


class RedisCSAFDatabaseHelper(CSAFDataBaseHelper):
    redis_database = None

    REGEX_PRODUCT_TYPE_IDX = 'regex_product_type_token_idx'
    VENDOR_IDX = 'vendor_token_idx'
    BRAND_IDX = 'brand_token_idx'
    PRODUCT_TYPE_IDX = 'product_type_token_idx'
    OUI_IDX = 'oui_token_idx'

    LEARNED_VENDOR_IDX = 'learned_vendor_token_idx'
    LEARNED_BRAND_IDX = 'learned_brand_token_idx'
    LEARNED_PRODUCT_TYPE_IDX = 'learned_brand_token_idx'
    LEARNED_REGEX_PRODUCT_TYPE_IDX = 'regex_product_type_token_idx'

    regex_product_type_idx = None
    client_product_type = None
    client_regex_product_type = None
    client_brand = None
    client_vendor = None
    client_oui = None

    # learn layer
    client_brand_learned = None
    client_vendor_learned = None
    client_product_type_learned = None

    # TODO request manager
    # type wenn man nicht weiß welche felder -> mapping der Spalten
    # type wenn man nach token sucht und schon das feld weiß -> FullSpellchecker mappt
    # Confirmation
    sessions_mapping = None
    sessions_token_rows = None

    def __init__(self, database: redis.Redis):
        super().__init__()
        self.redis_database = database
        self.client_regex_product_type = self.redis_database.ft(self.REGEX_PRODUCT_TYPE_IDX)
        self.client_product_type = self.redis_database.ft(self.PRODUCT_TYPE_IDX)
        self.client_brand = self.redis_database.ft(self.BRAND_IDX)
        self.client_vendor = self.redis_database.ft(self.VENDOR_IDX)
        self.client_oui = self.redis_database.ft(self.OUI_IDX)

        # learning layer
        self.client_brand_learned = self.redis_database.ft(self.LEARNED_BRAND_IDX)
        self.client_vendor_learned = self.redis_database.ft(self.LEARNED_VENDOR_IDX)
        self.client_product_type_learned = self.redis_database.ft(self.LEARNED_PRODUCT_TYPE_IDX)
        self.client_regex_product_type_learned = self.redis_database.ft(self.LEARNED_REGEX_PRODUCT_TYPE_IDX)

    def get_redis_db(self):
        return self.redis_database

    def set_value(self, key, value):
        self.redis_database.set(key, value)

    def get_value(self, key):
        return self.redis_database.get(key)

    def save_json_data(self, key, json_value):
        try:
            self.redis_database.execute_command('JSON.SET', key, '$', json_value)
            # print('saved: ' + key)
        except Exception as e:
            raise ValueError(f"{key} could not be saved")

    def create_regex_product_type_index(self):
        try:
            self.client_regex_product_type.info()
        except redis.exceptions.ResponseError:
            schema = (
                TextField("$.vendor", as_name="vendor"),
                TextField("$.product_type", as_name="product_type"),
                TextField("$.short_type_index", as_name="short_type_index"),
                # str list segments seperated with ",,"
                TagField( "$.group_regex", as_name="group_regex"),
                TagField( "$.token_regex", as_name="token_regex"),
                TextField("$.token_segment_types", as_name="token_segment_types"),
                TagField("$.regex_uuid", as_name="regex_uuid"),
                TextField("$.types", as_name="types"),
                TextField("$.annotations", as_name="annotations"),
                TextField("$.token_pos", as_name="token_pos"),
                TextField("$.whole_tokens", as_name="whole_tokens"),
            )
            self.client_regex_product_type.create_index(schema, definition=IndexDefinition(index_type=IndexType.JSON))

    def create_product_type_index(self):
        try:
            self.client_product_type.info()
        except redis.exceptions.ResponseError:
            schema = (
                TextField("$.vendor", as_name="vendor"),
                TextField("$.product_type", as_name="product_type"),
                TextField("$.annotations", as_name="annotations")
            )
            self.client_product_type.create_index(schema, definition=IndexDefinition(index_type=IndexType.JSON))

    def create_oui_index(self):
        try:
            self.client_oui.info()
        except redis.exceptions.ResponseError:
            schema = (
                # scheme XX-XX-XX
                TextField("$.oui", as_name="oui"),
                TextField("$.oui_search", as_name="oui_search"),
                TextField("$.vendor_oui", as_name="vendor_oui"),
                TextField("$.vendor_csaf_normalized", as_name="vendor_csaf_normalized"),
                TextField("$.vendor_without_legal_oui", as_name="vendor_without_legal_oui")
            )
            self.client_oui.create_index(schema, definition=IndexDefinition(index_type=IndexType.JSON))

    def create_vendor_index(self):
        try:
            self.client_vendor.info()
        except redis.exceptions.ResponseError:
            schema = (
                TextField("$.vendors_similar_oui", as_name="vendors_similar_oui"),
                # CSAF writing, it is also defines the key. JOIN OUI Index
                TextField("$.vendor_csaf_normalized", as_name="vendor_csaf_normalized"),
                TextField("$.vendors_similar_csaf", as_name="vendors_similar_csaf"),
                TextField("$.vendors_similar_all", as_name="vendors_similar_all"),
                TextField("$.brands", as_name="brands"),
            )
            self.client_vendor.create_index(schema, definition=IndexDefinition(index_type=IndexType.JSON))

    def create_learn_vendor_index(self):
        try:
            self.client_vendor_learned.info()
        except redis.exceptions.ResponseError:
            schema = (
                TextField("$.vendor_csaf_normalized", as_name="vendor"),
                TextField("$.vendors_similar_learned", as_name="vendor"),
            )
            self.client_vendor_learned.create_index(schema, definition=IndexDefinition(index_type=IndexType.JSON))

    def create_learn_brand_index(self):
        try:
            self.client_brand_learned.info()
        except redis.exceptions.ResponseError:
            schema = (
                TextField("$.vendor_csaf_normalized", as_name="vendor"),
                TextField("$.brand_csaf_normalized", as_name="vendor"),
                TextField("$.brands_similar_learned", as_name="vendor"),
            )
            self.client_brand_learned.create_index(schema, definition=IndexDefinition(index_type=IndexType.JSON))

    # TODO sollte vom format gleich sein wie andere
    def create_learn_product_type_index(self):
        try:
            self.client_product_type_learned.info()
        except redis.exceptions.ResponseError:
            schema = (
                TextField("$.vendor_csaf_normalized", as_name="vendor_csaf_normalized"),
                TextField("$.brand_csaf_normalized", as_name="brand_csaf_normalized"),
                # From Brand Token till Subseries
                # TODO Thesis festlegung für Normalizisierung
                TextField("$.product_type_normalized", as_name="product_type_normalized"),
                TextField("$.product_type_similar_learned", as_name="product_type_similar_learned"),
            )
            self.client_product_type_learned.create_index(schema, definition=IndexDefinition(index_type=IndexType.JSON))

    # TODO sollte vom format gleich sein wie andere
    def create_learn_regex_product_type_index(self):
        try:
            self.client_product_type_learned.info()
        except redis.exceptions.ResponseError:
            schema = (
                TextField("$.vendor_csaf_normalized", as_name="vendor"),
                TextField("$.brand_csaf_normalized", as_name="vendor"),
                # From Brand Token till Subseries
                # TODO Thesis festlegung für Normalizisierung
                TextField("$.product_type_normalized", as_name="vendor"),
                TextField("$.product_type_similar_learned", as_name="vendor"),
            )
            self.client_product_type_learned.create_index(schema, definition=IndexDefinition(index_type=IndexType.JSON))

    def create_brand_index(self):
        try:
            self.client_brand.info()
        except redis.exceptions.ResponseError:
            schema = (
                TextField("$.brand_csaf_normalized", as_name="brand_csaf_normalized"),
                TextField("$.vendor_csaf_normalized", as_name="vendor_csaf_normalized"),
                TextField("$.brands_similar_learned", as_name="brands_similar_learned")
            )
            self.client_brand.create_index(schema, definition=IndexDefinition(index_type=IndexType.JSON))

    def clean_tokens(self, df, vendor=None, brand=None):
        not_found = 0
        found_ids = set()
        offset = 0
        all_results = []
        batch_size = 100
        while True:
            search_query = Query('*').paging(offset, batch_size)
            results = self.client_product_type.search(search_query)
            all_results.extend(results.docs)
            if len(results.docs) == 0:
                break
            offset += batch_size

        for doc in all_results:
            if doc.id in found_ids:
                continue
            found_ids.add(doc.id)
            json_data = doc.json
            json_obj = json.loads(json_data)
            product_type = json_obj.get('product_type', None)
            meta = json_obj.get('meta_info', [])
            key = doc.id
            if 'whole_tokens' in meta:
                whole_tokens = [meta_token for meta_token in meta['whole_tokens'] if meta_token not in ['(', ')']]
                search_compare = ' '.join(whole_tokens)
                result = df.loc[df['product_name'] == search_compare]
                if result.shape[0] == 0:
                    not_found = not_found + 1
                    test = self.redis_database.delete(key)
        print(f'{not_found} deleted')
        print(f"Anzahl der abgerufenen Dokumente: {len(all_results)}")

    def short_type_index(self, token_segment_types:[]):
        return ''.join(token_segment_types).lower()

    # TOOD more possiblities
    def sanitize_input(self, user_input):
        sanitized = re.sub(r'[@{}|*-]', '', user_input)
        return sanitized

    # key hat noch vendor und producttyp und ist unique
    def fetch_regexes(self, vendor:str, short_type_index:str):
        query = Query(f"@short_type_index:{short_type_index}").paging(0, 100000)
        result = self.client_regex_product_type.search(query)

        results = []
        for doc in result.docs:
            # TODO liefert auch "score" field
            key = doc.id
            vendor = self.redis_database.execute_command('JSON.GET', key, '$.vendor').decode('utf-8')
            group_regexes = self.redis_database.execute_command('JSON.GET', key, '$.group_regex')
            product_type = self.redis_database.execute_command('JSON.GET', key, '$.product_type')
            short_type_index = self.redis_database.execute_command('JSON.GET', key, '$.short_type_index').decode('utf-8')
            results.append((key, vendor, json.loads(product_type), json.loads(group_regexes), json.loads(short_type_index)))
        return results

    def get_value_by_uuid(self, uuid):
        return self.client_regex_product_type.search(uuid)

    def fetch_regexes_by_group(self, vendor:str, group_regex:str, short_type_index:str, brand:str=None) -> list:
        # KEYS "*___regex_detail_type:W*,,*4*,,-,,*1*___vendor*""
        # TODO brand einschränkung + synonyme

        # TODO suche nach Produkttyp regex oder nach der Gruppe selbst. Ersteres ist gezielter
        matching_keys = self.redis_database.keys("*___regex_type:"+short_type_index+"___regex_detail_type:"+group_regex+'___*')
        print("*___regex_type:"+short_type_index+"___regex_detail_type:"+group_regex+'___*')
        found_list = []
        for key in matching_keys:
            regex_uuid_part = key.decode('utf-8').split("___")[0]
            product_type = self.redis_database.execute_command('JSON.GET', key, '$.product_type').decode('utf-8')
            types = self.redis_database.execute_command('JSON.GET', key, '$.types')
            annotations = self.redis_database.execute_command('JSON.GET', key, '$.annotations')
            token_pos = int(self.redis_database.execute_command('JSON.GET', key, '$.token_pos').decode('utf-8').strip('[]'))
            whole_tokens = self.redis_database.execute_command('JSON.GET', key, '$.whole_tokens')
            vendor = self.redis_database.execute_command('JSON.GET', key, '$.vendor')

            meta_info = {'vendor': json.loads(vendor)[0], 'types': json.loads(types)[0], 'annotations': json.loads(annotations)[0],
                         'token_pos': token_pos, 'whole_tokens': json.loads(whole_tokens)[0], 'group_uuid': regex_uuid_part}
            found_list.append((key.decode('utf-8'), json.loads(product_type)[0], meta_info))
        return found_list

    # TODO index aufbauen für sofort suche ohne -
    def search_oui(self, oui:str, count_matches=1):
        oui_search = oui.replace(':', '').replace('-', '')
        query = Query(f"@oui_search:{oui_search}")
        result = self.client_oui.search(query)
        for doc in result.docs:
            key = doc.id
            vendor_info = self.redis_database.execute_command('JSON.GET', key, '$.vendor_csaf_normalized')
            return json.loads(vendor_info)[0], {}
        return None, {}

    def search_vendor(self, token, count_matches=1):
        unique_csaf_vendor = set()
        query = Query(f"@vendor_csaf_normalized:{token}")
        additional_info = {}
        result = self.client_vendor.search(query)
        for doc in result.docs:
            vendor_info = self.redis_database.execute_command('JSON.GET', doc.id, '$.vendor_csaf_normalized')
            if vendor_info not in unique_csaf_vendor:
                return json.loads(vendor_info)[0], additional_info

        query_similar = Query(f"@vendors_similar_all:{token}")
        additional_info = {}
        result = self.client_vendor.search(query_similar)
        for doc in result.docs:
            vendor_info = self.redis_database.execute_command('JSON.GET', doc.id, '$.vendor_csaf_normalized')
            if vendor_info not in unique_csaf_vendor:
                return json.loads(vendor_info)[0], additional_info
        return None, {}

    def search_brand(self, search_token, vendor=None, count_matches=1):
        if vendor is not None:
            query = Query(f"@vendor:{vendor} @brand_csaf_normalized:{search_token}")
        else:
            query = Query(f"@brand_csaf_normalized:{search_token}")
        result = self.client_brand.search(query)
        for doc in result.docs:
            brand_info = self.redis_database.execute_command('JSON.GET', doc.id, '$.brand_csaf_normalized')
            vendor_found = self.redis_database.execute_command('JSON.GET', doc.id, '$.vendor_csaf_normalized')
            additional_info = {'vendor': json.loads(vendor_found)[0] }
            return json.loads(brand_info)[0], additional_info
        return None, {}

    def search_token(self, token, offset, batch_size, vendor=None, brand=None) -> ():
        if token == '*':
            search_query = Query('*').paging(offset, batch_size)
        else:
            # TODO replace special chars with ~
            if is_number(token):
                token_escaped = str(token)
            else:
                token_escaped = re.sub('[^a-zA-Z0-9*]+', '~', token)

            token_escaped = token_escaped.strip('~')
            search_query = '@product_type:*'+token_escaped
            if len(token_escaped) > 0:
                search_query = search_query + '*'

        results = self.client_product_type.search(search_query)
        found_ids = set()
        found_list = []
        for doc in results.docs:
            json_data = doc.json
            json_obj = json.loads(json_data)
            product_type = json_obj.get('product_type', None)
            meta_info = json_obj.get('meta_info', [])
            if doc.id not in found_ids:
                # TODO annotations hinzufügen
                found_list.append((doc.id, product_type, meta_info))
                found_ids.add(doc.id)
        return found_list

    def search_prefix_token(self, token, vendor=None, brand=None):
        if vendor:
            if brand:
                token_key = 'vendor:' + vendor + ',brand:' + brand
            else:
                token_key = 'vendor:' + vendor + ',brand:' + brand
        else:
            token_key = ''

        current_token_key = token_key + ',token:' + token +'*'

        keys = self.redis_database.keys(current_token_key)
        return self._get_values(keys)

    def search_suffix_token(self, token, vendor=None, brand=None):
        if vendor:
            if brand:
                token_key = 'vendor:' + vendor + ',brand:' + brand
            else:
                token_key = 'vendor:' + vendor + ',brand:' + brand
        else:
            token_key = ''
        current_token_key = token_key + ',token:*' + token
        keys = self.redis_database.keys(current_token_key)
        return self._get_values(keys)

    def search_infix_token(self, token, vendor=None, brand=None):
        if vendor:
            if brand:
                token_key = 'vendor:' + vendor + ',brand:' + brand
            else:
                token_key = 'vendor:' + vendor + ',brand:' + brand
        else:
            token_key = ''
        current_token_key = token_key + ',token:*' + token+'*'
        keys = self.redis_database.keys(current_token_key)
        return self._get_values(keys)

    def _get_values(self, keys:[]):
        results = []
        for key in keys:
            results.append(self.redis_database.get(key))
        return results

    def delete_key(self, key):
        self.redis_database.delete(key)
