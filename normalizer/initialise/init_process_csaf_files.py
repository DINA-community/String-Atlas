import pandas
import redis
import os
import time
from normalizer.corpus_manager import CorpusManager
from normalizer.database.csaf_database_helper import CSAFDataBaseHelper
from normalizer.database.redis_csaf_database_helper import RedisCSAFDatabaseHelper
from normalizer.helper.feature_extractor import FeatureExtractor
from normalizer.initialise.csaf_dataframe import df_filtered
from string_miner.strategies.physical_unit_string_miner import PhysicalUnitStringMinerStrategy
from string_miner.string_miner import StringMiner

print("Initialising ========", flush=True)

# CSAF path environment variable. folder that contains csaf_files from CISA
CSAF_PATH = os.getenv('CSAF')
CSAF_REGEX: bool = os.getenv("CSAF_REGEX_MODE", "false").lower() in ("1", "true", "yes", "on")
CSAF_FOLDERS: str = os.getenv('CSAF_FOLDERS', 'All')
CSAF_VENDORS: str = str(os.getenv('CSAF_VENDORS', 'All'))
OUI_FILE = os.getenv('OUI_FILE')
LEGAL_FILE = os.getenv('LEGAL_FILE')

KEY_CSAF = 'csaf_initial_timestamp'
docker_redis_hostname = str(os.getenv('DOCKER_REDIS_HOSTNAME', 'localhost'))
docker_redis_port = int(os.getenv('DOCKER_REDIS_PORT', 6379))
docker_redis_database = int(os.getenv('DOCKER_REDIS_DATABASE', 0))


def set_initial_csaf_files(database_helper: CSAFDataBaseHelper, key):
    database_helper.set_value(key, int(time.time()))

def is_csaf_initialised(database_helper: CSAFDataBaseHelper, key):
    current_time = int(time.time())
    last_initialised = database_helper.get_value(key)
    if last_initialised is None:
        return False
    #last_initialised = int(last_initialised)
    #one_month_ago = current_time - 3600 * 24 * 30
    #return last_initialised >= one_month_ago
    return True

def create_database(database_helper: CSAFDataBaseHelper, corpus_config:{}, df_corpus: pandas.DataFrame, regex:bool=False):
    string_miner = StringMiner()

    corp_manager = CorpusManager(config=corpus_config, corpus_data=df_corpus, string_miner=string_miner)
    corp_manager.bl_extract()
    corp_manager.save_vendors_and_brands(database_helper=database_helper)
    corp_manager.save_oui(database_helper=database_helper)
    corp_manager.save_product_type_and_regex(database_helper=database_helper, regex=regex)

    try:
        import matcher.initialise.qadrant_collections
    except ImportError:
        print("Skipping qdrant vector initialization because optional vector dependencies are not installed.", flush=True)
    import matcher.initialise.create_lookup_tables

    physical_strategy = PhysicalUnitStringMinerStrategy()
    string_miner.add_annotate_strategy(physical_strategy)

    feature_extractor = FeatureExtractor(string_miner=string_miner)
    feature_extractor.extract_features(df_filtered)


r_db = redis.Redis(host=docker_redis_hostname, port=docker_redis_port, db=docker_redis_database)
database_helper = RedisCSAFDatabaseHelper(database=r_db)

csaf_force_reinit = str(os.getenv('CSAF_FORCE_REINIT', 'False'))
if is_csaf_initialised(database_helper=database_helper, key=KEY_CSAF) and (csaf_force_reinit != 'True'):
    print("CSAF corpus is initialized")
    exit(0)

if CSAF_PATH is None or CSAF_PATH.strip() == '':
    raise Exception('CSAF environment variable not set')



start_time = time.time()

corpus_c = {'legal_entities_file_name': LEGAL_FILE, 'oui_lookup_file_name': OUI_FILE, 'vendors_used': CSAF_VENDORS}
# reset database content
r_db.flushall()
create_database(database_helper=database_helper, corpus_config=corpus_c, df_corpus=df_filtered, regex=CSAF_REGEX)

set_initial_csaf_files(database_helper=database_helper,key=KEY_CSAF)

end_time = time.time()
elapsed_time = end_time - start_time

#delete_key_fixes(r_db)
print(f"CSAF INITIALISED - Laufzeit: {elapsed_time:.1f} Sekunden")
