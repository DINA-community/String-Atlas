import re
from string_miner.strategies.string_miner_strategy import StringMinerStrategy
from string_miner.string_miner_helper import StringMinerHelper
from string_miner.string_type import StringType


class StringMiner:

    strategies = None
    config:dict = None

    def __init__(self, config={}):
        self.strategies = []
        self.config = config
        # TODO default config erstellen, wenn keine übergeben wird

    def add_annotate_strategy(self, strategy: StringMinerStrategy):
        self.strategies.append(strategy)

    # TODO token_next wäre gut in der Corpus Logik, wenn statisch, oder 2. durchlauf -> rückwirkend wenn man als 3. tupel element level mitliefert
    def annotate_token(self, token, token_before=None, next_meta_info=None, level=0) -> ():
        highest = 0
        highest_match_types = None
        highest_match_annotations = None
        for strategy in self.strategies:
            match_score, types, annotations = strategy.annotate_token(token=token, token_before=token_before, next_meta_info=next_meta_info, level=level)
            if match_score > highest:
                highest = match_score
                highest_match_types = types
                highest_match_annotations = annotations
        return highest_match_types, highest_match_annotations

    def characterize(self, token: str):

        token = str(token)

        # TODO check if only character or digit
        # TODO sonderzeichen wie & etc.
        # TODO nach StringType auslagern
        SPECIAL_CHARS_SEMANTIC = [':']
        suffix_semantic = False
        suffix_sementic_special = None
        suffix_sementic_special_len = None

        special_chars = []
        current_type = None
        if re.match(StringType.PATTERN_PURE, token):
            if re.match(StringType.PATTERN_DIGITS, token):
                current_type = StringType.TYPE_NUMBER
                full_regex = StringType.PATTERN_DIGITS
                segment_regex = [StringType.PATTERN_DIGITS]
                segment_types = [StringType.TYPE_NUMBER]
            else:
                current_type = StringType.TYPE_ALPHA
                segment_types = [StringType.TYPE_ALPHA]
                segment_regex = [StringType.TYPE_ALPHA]
                full_regex = StringType.TYPE_ALPHA
            segments = [token]

        else:
            segments, segment_regex = self.create_pattern(token)
            segment_types = []
            for segment in segments:
                if segment.isalpha():
                    segment_types.append(StringType.TYPE_ALPHA)
                elif segment.isdigit():
                    segment_types.append(StringType.TYPE_NUMBER)
                else:
                    segment_types.append(StringType.TYPE_SPECIAL)
                    special_chars.append(segment)
            i = 0

            # TODO text cleaner auslagern -> hier die frage stellen ob es nicht sinn macht später erst danach zu suchen für bestimmte character
            reverse_segments_types = list(reversed(segment_types))
            reverse_segments = list(reversed(segments))
            while len(reverse_segments_types) > i and reverse_segments_types[i] == StringType.TYPE_SPECIAL:
                if reverse_segments[i] in StringType.SPECIAL_CHARS_STRIP:
                    i = i + 1
                else:
                    break
            if i > 0:
                segment_types = StringMinerHelper.remove_last_elements(segment_types, i)
                segments = StringMinerHelper.remove_last_elements(segments, i)
                segment_regex = StringMinerHelper.remove_last_elements(segment_regex, i)
                token = token.rstrip(''.join(StringType.SPECIAL_CHARS_STRIP))
            full_regex = ''.join(segment_regex)

        return {'nlp_type': 'ADJ', 'ern': '', 'type': current_type, 'value': token, 'special_chars': special_chars,
                'segments': segments, 'segment_types': segment_types, 'segment_regex': segment_regex,
                'full_regex': full_regex}

    # TODO Optimierung bei verschiedenen Längen und bei Alpha-Semgent Länge selbst, mehrere Regex anbieten
    def characteristic_group(self, token_group: []) -> []:
        """
        delivers not only diff between two token but common regex pattern for whole group

        common_characteristic
        [                   'V13.1'[feature_group - 2]
        ,                   'V13.0'[feature_group - 2]
        ]
        => ['V', '13', '.', '\\d\\{{1}}']

        token_group item is type ProductNode
        """
        common_segment_characters = []

        segment_index = 0
        segments_found = True
        while segments_found:
            segments_found = False
            segment_compare_to = None
            segment_compare_to_type = None
            # direct alpha chars match
            for token in token_group:
                if len(token['segment_types']) <= segment_index:
                    break
                if segment_compare_to is None:
                    if segments_found is False:
                        segments_found = True
                    segment_compare_to = token['segments'][segment_index]
                    segment_compare_to_type = token['segment_types'][segment_index]
                elif segment_compare_to is not False and segment_compare_to != token['segments'][segment_index]:
                    segment_compare_to = False
                if segments_found is False:
                    break

            # chars found AND direct char matches. Numbers should in groups as integer regex
            if segment_compare_to is not False and segments_found and segment_compare_to_type == StringType.TYPE_ALPHA:
                common_segment_characters.append(segment_compare_to)
            elif segment_compare_to is not False and segments_found and segment_compare_to_type == StringType.TYPE_SPECIAL:
                common_segment_characters.append(segment_compare_to)

            # not direct chars matches or digit chars
            elif segments_found:
                segment_compare_to = None
                segment_type = None
                segment_regex = None
                for token in token_group:
                    if len(token['segment_types']) <= segment_index:
                        break
                    if segment_compare_to is None:
                        segment_compare_to = token['segment_types'][segment_index]
                        segment_regex = token['segment_regex'][segment_index]
                        segment_type = segment_compare_to
                    elif segment_compare_to is not False and segment_compare_to_type != token['segment_types'][segment_index]:
                        segment_compare_to = False

                if segment_compare_to is not False:
                    if segment_type == StringType.TYPE_NUMBER:
                        common_segment_characters.append(segment_regex)
                    elif segment_type == StringType.TYPE_ALPHA:
                        words = set()
                        for token in token_group:
                            if len(token['segments']) <= segment_index:
                                break
                            words.add(token['segments'][segment_index])
                        prefix = self.get_common_prefix(words)
                        if len(prefix) > 1:
                            common_segment_characters.append(StringType.PATTERN_ALPHA_PREFIX.format(prefix))
                        else:
                            common_segment_characters.append(StringType.PATTERN_ALPHA)
            segment_index = segment_index + 1
        return common_segment_characters

    # UNUSED - wird performanter über index gelöst
    # TODO kann schon anders aufbereitet werden damit nur string vergleich über index
    def compare_regex_with_character(self, segment_regex, character:dict) -> float:
        # ['\\d\\{{4}}', '^[A-Za-z]+$', '-', '\\d\\{{1}}']
        search_alpha = StringType.PATTERN_ALPHA
        # TODO genau zählen wieviel prozentual passt -> threshold wird angewendet
        output = []
        segment_index = 0
        for group_segment in segment_regex:
            if StringType.SEARCH_DIGIT in group_segment:
                if character['segment_types'][segment_index] != StringType.TYPE_NUMBER:
                    return 0.00
                output.append('Digit')
            elif search_alpha == group_segment:
                if character['segment_types'][segment_index] != StringType.TYPE_ALPHA:
                    return 0.00
                output.append('Alpha')
            # TODO regel kann vereinfacht werden aus beiden -> else, aber noch warten ob weitere regeln
            elif re.search(StringType.SEARCH_SPECIAL_CHARS, group_segment):
                if character['segments'][segment_index] != group_segment:
                    return 0.00
                output.append('Special')
            elif group_segment != character['segments'][segment_index]:
                return 0.00

            segment_index += 1
        return 100.0

    def create_pattern(self, token):
        pattern = []
        current_segment_type = None
        current_segment = ''
        segments = []

        # Iteriere über jedes Zeichen des Tokens
        for char in token:
            if char.isalpha():
                if current_segment_type == 'number':
                    pattern.append(r'\d\{{' + str(len(current_segment)) + '}}')
                    segments.append(current_segment)
                    current_segment = ''

                current_segment_type = 'alpha'
                current_segment += char

            elif char.isdigit():
                if current_segment_type == 'alpha':
                    pattern.append(r'[A-Za-z]\{{' + str(len(current_segment)) + '}}')
                    segments.append(current_segment)
                    current_segment = ''

                current_segment_type = 'number'
                current_segment += char

            else:
                if current_segment_type == 'alpha':
                    pattern.append(r'[A-Za-z]\{{' + str(len(current_segment)) + '}}')
                    segments.append(current_segment)
                    current_segment = ''
                if current_segment_type == 'number':
                    pattern.append(r'\d\{{' + str(len(current_segment)) + '}}')
                    segments.append(current_segment)
                    current_segment = ''
                # Wenn Sonderzeichen, direkt hinzufügen und Segment abschließen
                pattern.append(re.escape(char))
                segments.append(char)
                current_segment_type = None
        if current_segment_type is not None:
            if current_segment_type == 'alpha':
                pattern.append(r'[A-Za-z]\{{' + str(len(current_segment)) + '}}')

            elif current_segment_type == 'number':
                pattern.append(r'\d\{{' + str(len(current_segment)) + '}}')
            segments.append(current_segment)
        return segments, pattern

    def get_common_prefix(self, words):
        words = list(words)
        prefix = words[0]
        for s in words[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    return ""
        return prefix

    def group_token(self, tokens: list, case=True) -> ():
        """
        return groups and no matches as tuple
        """
        characters = []
        for token in tokens:
            if isinstance(token, dict):
                character = token
            elif token is not None:
                character = self.characterize(token)
            else:
                continue
            characters.append(character)

        # todo vendor parameter, bei 2. Hersteller testen ob es anders angepasst werden muss
        threshold = 0.6
        # als vektor darstellen und sklearn clustering? gewichtung der vektoren
        checked_list = []
        groups = []
        no_matches = {}
        for character in characters:
            token = character['value']
            group = {}
            for character_compare in characters:
                token_compare = character_compare['value']
                if token_compare in checked_list or token_compare == token:
                    continue
                compare_result = self._compare_token(character, character_compare, case)
                if compare_result >= threshold:
                    group[token_compare] = character_compare

            if len(group) > 0:
                group[token] = character
                checked_list.extend(group)
                groups.append(group)
            elif token not in checked_list:
                no_matches[token] = character
                checked_list.append(token)
        return groups, no_matches

    # Noch keine Wortnachbarnanalyse -> es kan n sein das bei Text1  ein Wort ausgelassen wird und Text 2 länger hat, es aber ein Wort später kommt
    # feauture
    def _compare_token(self, character, character2, case):
        # phase 1 vergleich -> kann auch vektorisiert werden
        # is segment position
        prefix_equal = 0
        total_equal = 0
        total_segment_types_equal = 0
        prefix_segment_types_equal = 0
        # collect positions
        special_equal = []

        index = 0
        prefix = True
        prefix_type = True
        for segment in character2['segments']:
            if len(character['segments']) > index:
                if segment == character['segments'][index] or (
                        case is False and segment.lower() == character['segments'][index].lower()) \
                        or (character2['segment_types'][index] == character['segment_types'][index] and
                            character['segment_types'][index] == StringType.TYPE_NUMBER):
                    special_char = False
                    number_char = False
                    alpha_char = False
                    if 'd' in character['segment_regex'][index]:
                        number_char = True
                    elif 'A' in character['segment_regex'][index]:
                        alpha_char = True
                    else:
                        special_char = True

                    total_equal += 1

                    if prefix:
                        prefix_equal += 1
                    if special_char:
                        special_equal.append(index)
                else:
                    prefix = False

                if character2['segment_types'][index] == character['segment_types'][index]:
                    total_segment_types_equal += 1
                    if prefix_type:
                        prefix_segment_types_equal += 1
                else:
                    prefix_type = False

            index = index + 1

        value1 = character['value']
        value2 = character2['value']
        # same characters have more weight
        # semantisch zuerst ->

        # TODO gewichtung der Marke, Reihe etc. welche Wortposition es sein könnte. Z.b. SIMATIC hat nur 1 Wort, aber PC Reader -> vergleiche somit 2. Word einer Marke mit Reihe von SIMATIC -> verhindern.
        # todo könnte auch vektoren erstellen und in knn reinschicken
        # phase 2 resulting-algorithmus
        # beginning of
        # special character counts more weight when in middle, has semantic
        total_segments_len1 = len(character['segments'])  # TODO muss minimum sein
        total_segments_len2 = len(character2['segments'])
        total_segment_min = min(total_segments_len1, total_segments_len2)
        total_segment_max = max(total_segments_len1, total_segments_len2)

        total_len_c1 = len(character['value'])
        total_len_c2 = len(character2['value'])
        total_len_c = min(total_len_c1, total_len_c2)

        # TODO länger der segmente auch entscheident, suffixe, 1 Länge weißt auf merkmal hin,  hier varianz feststellen
        if value1.startswith('ET') and value2.startswith('ET'):
            test = '1'

        # TODO suffix wird nicht entdeckt ET200 -> ET

        # not at beginning, unprobability
        if prefix_equal == 0:  # TODO zwischen charactern überprüfen prefixe innerhalb des segments
            if total_segment_types_equal == 0:  # totally different types
                return 0
            elif prefix_segment_types_equal > 0:  # same beginning but different Charaters AC-200 - BC-200
                # not same start, but some same segments
                return 0.1
            else:
                return 0
        # beginning, very probability
        elif prefix_equal > 0:
            check_pos = prefix_equal
            # Segmentierung von Groß und Kleinschreibung ? oder vergleich ?

            # TODO Gesamtlänge

            #semantic special chars
            if character2['segment_types'][
                prefix_equal - 1] == StringType.TYPE_SPECIAL:  #S7-XXX macht all underseries -> next step extreact prefix # annoation bei group kategorie
                # segment type kann danach gleich unterscheiden 'S7-200', 'S7-PLCSIM'
                if prefix_equal < total_segment_min and character2['segment_types'][prefix_equal] == \
                        character['segment_types'][prefix_equal]:
                    return 1.0
                else:
                    if total_segment_max - prefix_equal == 1:
                        return 0.3
                    # TODO folgecheck, kann auch keins mehr danach folgen
                    return 0.6  # todo z.b. nach gesamt varrianz bewerten, in mitte kann auch was auftreten. was dann am 3. Wort wieder gleich ist.
            elif check_pos < total_segment_min and character2['segment_types'][check_pos] == character['segment_types'][
                check_pos]:  #ET200 -> ET400

                # TODO hier kann es auch number sein, wichtig sementaisch wenn es folgesegment ist (SP400N, SP400)
                measure1 = total_equal / total_segment_max
                measure2 = prefix_equal / total_segment_max * 1.1
                # todo hier noch formel nachbessern -> es ist hier viel wahrscheinlicher, außer  z.b. S7proEN S7proPN -> gehört nicht zu S7-400
                return max(measure1, measure2)

            #elif total_segment_min < total_segment_max:
            elif prefix_segment_types_equal == total_segment_max:
                return 1.0
            else:  #gleiche segment anzahl oder weniger, hier unterscheiden ?
                minus = 0.0
                # TODO parametrisieren für tokenvergleich
                if (check_pos < len(character['segments']) and character['segment_types'][
                    check_pos] == StringType.TYPE_NUMBER) \
                        or (check_pos < len(character2['segments']) and character2['segment_types'][
                    check_pos] == StringType.TYPE_NUMBER):
                    minus = 0.2

                # TODO noch hier reinmachen wenn nur ein segment ist bei einen und der andere die zahl, dann - 0.2
                measure1 = total_equal / total_segment_max
                measure2 = prefix_equal / total_segment_max * 1.1
                measure1 = measure1 - minus
                measure2 = measure2 - minus
                return max(measure1, measure2)


