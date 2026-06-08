from normalizer.semantics.semantics import Annotation
from normalizer.tree.product_node import ProductNode
from string_miner.string_miner import StringMinerStrategy
from string_miner.string_miner_helper import StringMinerHelper
from string_miner.string_type import StringType


class PhysicalUnitStringMinerStrategy(StringMinerStrategy):

    NAME = 'Physical Unit String Miner'
    oui_lookup_without_legal_forms = None

    def __init__(self, legal_entities_file_name='legal_entities.json', oui_lookup_file_name='latest_oui_lookup.json'):
        super().__init__(name=self.NAME)

    def annotate_token(self, token, token_before:ProductNode=None, token_after=None, next_meta_info=None, level=0) -> ():
        """
        first tuple element is match score
        second tuple element is type of token
        third tuple element is annotation
        """
        if len(token['segment_types']) > 1:
            if token['segment_types'][0] == StringType.TYPE_NUMBER and token['segments'][1] == 'V':
                return 70, None, [Annotation.ANNOTATION_PHYSICAL_UNIT_VOLT_AND_AMOUNT]
        elif token['value'] == 'V': # TODO and not group
            last_segments = token_before.get_token()['segment_types'] # TODO number annotieren
            if last_segments is not None and len(last_segments) == 1 and last_segments[0] == StringType.TYPE_NUMBER:
                return 70, None,[Annotation.ANNOTATION_PHYSICAL_UNIT_VOLT]
            # TODO nachträglich letzten Token annotieren, 2 mal durchlaufen lassen, bzw. mit visitor anstatt recursiv
        if token['value'].lower() in ['v', 'version', 'ver']:
            return 70, None,[Annotation.ANNOTATION_VERSION_IDENTIFIER]
        elif token_before is not None and token_before.has_annotation(Annotation.ANNOTATION_VERSION_IDENTIFIER) and (str(token['value']).isdigit() or StringMinerHelper.has_float_sequence(token['value'])):
            return 70, None,[Annotation.ANNOTATION_VERSION]
        elif StringMinerHelper.has_float_sequence(token['value']) and str(token['value']).lower().startswith('v'):
            return 70, None,[Annotation.ANNOTATION_VERSION_IDENTIFIER_AND_VERSION]
        elif StringMinerHelper.is_unique(token) and (next_meta_info is None or ('group' in next_meta_info and next_meta_info['group'] is True)):
            return 70, None,[Annotation.ANNOTATION_UNIQUE]
        return 0, None, []
