class Semantics:
    TOKEN_VENDOR = 'vendor'
    TOKEN_VENDOR_LEGAL = 'vendor_legal'
    TOKEN_BRAND = 'brand'
    TOKEN_SERIES = 'series'
    TOKEN_SUB_SERIES = 'sub_series'
    TOKEN_SERIES_AND_SUB_SERIES_MIX = 'series_and_sub_series'
    TOKEN_FEATURE_GROUP = 'feature_group'  # ending values, but have common regex
    TOKEN_FEATURE_SERIE = 'feature_series'
    TOKEN_FEATURE = 'static_feature'  # after a group, maybe too less values, can be how cpu is build
    TOKEN_OUTLIER_SUSPECTED = 'outlier_suspected'

    TOKEN_PARENTHESES_START = 'parentheses_start'
    TOKEN_PARENTHESES_END = 'parentheses_end'
    TOKEN_PARENTHESES_FEATURE_STATIC = 'parentheses_feature_static'
    TOKEN_PARENTHESES_FEATURE_GROUP = 'parentheses_feature_group'


    TOKEN_SERIES_ONLY_LIST = [TOKEN_SERIES]
    PARENTHESIS_LIST = [TOKEN_PARENTHESES_START, TOKEN_PARENTHESES_END, TOKEN_PARENTHESES_FEATURE_STATIC, TOKEN_PARENTHESES_FEATURE_GROUP]
    PARENTHESIS_LIST_OPEN = [TOKEN_PARENTHESES_START, TOKEN_PARENTHESES_FEATURE_STATIC, TOKEN_PARENTHESES_FEATURE_GROUP]
    TOKEN_SERIES_LIST2 = [TOKEN_SERIES_AND_SUB_SERIES_MIX, TOKEN_SERIES, TOKEN_SERIES, TOKEN_SUB_SERIES, TOKEN_FEATURE_SERIE,TOKEN_FEATURE_GROUP, TOKEN_PARENTHESES_FEATURE_GROUP]
    TOKEN_SERIES_LIST = [TOKEN_SERIES_AND_SUB_SERIES_MIX, TOKEN_SERIES, TOKEN_SUB_SERIES, TOKEN_FEATURE_SERIE,TOKEN_FEATURE_GROUP, TOKEN_PARENTHESES_FEATURE_GROUP]
    TOKEN_BRAND_TILL_SERIES = [TOKEN_BRAND, TOKEN_SERIES, TOKEN_SUB_SERIES, TOKEN_SERIES_AND_SUB_SERIES_MIX]

    TOKEN_FEATURES = [TOKEN_FEATURE_GROUP, TOKEN_FEATURE, TOKEN_FEATURE_SERIE]

    COLUMN_PRODUCT_TYPE = 'product_type'
    COLUMN_FAMILY = 'product_family'
    COLUMN_VENDOR = 'vendor'
    COLUMN_MAC = 'mac'
    COLUMN_OUI = 'oui'
    COLUMN_MODELL = 'modell_nr'
    COLUMN_SERIES = 'series'
    COLUMN_IP = 'ip_address'
    COLUMN_PRODUCT_NAME = 'product_name'

    COLUMNS_TO_FIND = [COLUMN_MODELL, COLUMN_VENDOR, COLUMN_SERIES, COLUMN_FAMILY, COLUMN_MAC, COLUMN_OUI, COLUMN_SERIES, COLUMN_IP, COLUMN_PRODUCT_TYPE, COLUMN_PRODUCT_NAME]

# TODO das über die json config machen, regeln mit vorherigen und folgetoken macheen oder matching über gesamten satz
class Annotation:
    # like a model number
    ANNOTATION_UNIQUE = 'unique'
    ANNOTATION_VERSION_IDENTIFIER = 'version_identifier'
    ANNOTATION_VERSION_IDENTIFIER_AND_VERSION = 'version_identifier_and_version'
    ANNOTATION_VERSION = 'version'

    ANNOTATION_PHYSICAL_UNIT = 'physical_unit'
    ANNOTATION_PHYSICAL_UNIT_VOLT = 'physical_unit_volt'
    ANNOTATION_PHYSICAL_UNIT_VOLT_AND_AMOUNT = 'physical_unit_volt_and_amount'
    ANNOTATION_PHYSICAL_UNIT_VOLT_AMOUNT = 'physical_unit_volt_amount'


class FeatureSemantics:
    # TODO aufzeigen warum man hier manuell pflegen muss und in welchen Aufwand, aus sysiphos laden, die hardcoded bleiben aber hier als Konstante zur Zuordnung in NetBox
    TYPE_CPU = 'cpu'
    TYPE_RAM = 'ram'
    TYPE_NET = 'NET'
    TYPE_FIRMWARE = 'FIRMWARE'


    # TODO später aus json configuration laden
    # Herstellerspezifisch
    # enumy types erstellen

    # TODO für series spezifiisch machen ? odewr optional, service hat vorrang
    def annotate_feature_semantics(self, vendor, token):
        config = [{
            'vendor': 'Siemens',
            'ern': {
                self.TYPE_NET: 'NET'
            }
         }]
        for config_item in config:
            ern = config_item['ern']
            for key, value in ern.items():
                if value == token:
                    return key

class SemanticsState:
    @staticmethod
    def get_last_series_pos(token_types: []):
        pos = 0
        for token_type in token_types:
            if token_type not in Semantics.TOKEN_BRAND_TILL_SERIES:
                return pos
            pos = pos + 1

    @staticmethod
    def get_last_normal_state(states_before):
        states_before = [x for x in states_before if x not in Semantics.PARENTHESIS_LIST]
        last_state = states_before[-1]
        return last_state

    @staticmethod
    def get_last_series_kind_state(states_before, state_searched:[]) -> tuple():
        state_before_reverse = states_before[::-1]
        start = None
        start_type = None
        end = None
        for i, state in enumerate(state_before_reverse):
            if state in state_searched:
                if start is None:
                    end = start = i
                    start_type = state
                elif state == start_type:
                    end = i
        return start, end

    def add_special_char(self, special_char=None):
        pass

    # TODO level müsste hochgezählt werden bei mehreen feautres
    @staticmethod
    def predict_new_state(states_before, is_group_member, special_char=None):

        if len(states_before) == 0:
            raise ValueError('every item type have to be iniated')
        last_state = states_before[-1]

        if special_char is not None and special_char == '(':
                return [Semantics.TOKEN_PARENTHESES_START]
        elif special_char is not None and special_char == ')':
            return [Semantics.TOKEN_PARENTHESES_END]
        elif last_state in Semantics.PARENTHESIS_LIST_OPEN:
            if is_group_member:
                return [Semantics.TOKEN_PARENTHESES_FEATURE_GROUP]
            else:
                return [Semantics.TOKEN_PARENTHESES_FEATURE_STATIC]
        else:
            # TODO innerhalb klammer kann ja auch subserie oder serie befinden bei csaf dokumenten
            if last_state == Semantics.TOKEN_PARENTHESES_END:
                last_state = SemanticsState.get_last_normal_state(states_before)

            if last_state == Semantics.TOKEN_BRAND:
                if is_group_member:
                    return [Semantics.TOKEN_SERIES_AND_SUB_SERIES_MIX]
                else:
                    return [Semantics.TOKEN_SERIES]
            elif last_state == Semantics.TOKEN_SERIES:
                if is_group_member:
                    return [Semantics.TOKEN_SUB_SERIES]
                else:
                    return [Semantics.TOKEN_SERIES]
            elif last_state == Semantics.TOKEN_SERIES_AND_SUB_SERIES_MIX or last_state == Semantics.TOKEN_SUB_SERIES:
                if is_group_member:
                    return [Semantics.TOKEN_FEATURE_GROUP]
                else:
                    return [Semantics.TOKEN_FEATURE_SERIE]
            elif last_state == Semantics.TOKEN_FEATURE_SERIE:
                if is_group_member:
                    return [Semantics.TOKEN_FEATURE_GROUP]
                else:
                    return [Semantics.TOKEN_FEATURE_SERIE]
            elif last_state == Semantics.TOKEN_FEATURE_GROUP:
                if is_group_member:
                    return [Semantics.TOKEN_FEATURE_GROUP]
                else:
                    return [Semantics.TOKEN_FEATURE]
            elif last_state == Semantics.TOKEN_FEATURE:
                if is_group_member:
                    return [Semantics.TOKEN_FEATURE_GROUP]
                else:
                    return [Semantics.TOKEN_FEATURE]
            else:
                print(states_before)
                raise ValueError('No Info about Semantics before')
