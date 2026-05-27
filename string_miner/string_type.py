class StringType:
    TYPE_NUMBER = 'number'
    TYPE_ALPHA = 'alpha'
    TYPE_SPECIAL = 'special'


    SEARCH_SPECIAL_CHARS = r'[^A-Za-z\d]'
    SEARCH_DIGIT = "\\d"
    SEARCH_ALPHA = r'^[A-Za-z]+$'

    SPECIAL_CHARS_STRIP = [',', ':', '.']

    PATTERN_ALPHA = r'^[A-Za-z]+$'
    PATTERN_ALPHA_PREFIX = '^{}[A-Za-z]+$'
    PATTERN_PURE = r'^[A-Za-z]+$|^\d+$'
    PATTERN_NO_SPECIAL_CHARS = r'^[A-Za-z\d]+$'
    PATTERN_DIGITS = r'^\d+$'