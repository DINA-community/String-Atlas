from benchmark.strategies.subcategory_strategy import *

class BenchmarkSubcategoryFactoryStrategie:
    @abstractmethod
    def create(self, name) -> "BenchmarkSubcategoryStrategie":
        raise NotImplementedError()

class BenchmarkSubcategoryFactory(BenchmarkSubcategoryFactoryStrategie):
    _strategies = {
        "Lexical errors - wrong letter typing": LexWrongLetterTyping,
        "Lexical errors - lower and uppercase": LexLowerAndUppercase,
        "Lexical errors - insertion redundant characters": LexRedundantLetters,
        "Lexical errors - insertion additional characters": LexInsertNeighboursLetters,
        "Lexical errors - deletion characters": LexDeletionLetters,
        "Lexical errors - transposed letters": LexTranspositionLetters,
        "Lexical errors - missing token": LexMissingToken,
        "Lexical errors - number alpha mix": LexNumberAlphaMix,
        # TODO insert special chars at random positions

        "different spelling - whitespaces - removed between token": DiffSpellRemovedWhitespaces,
        "different spelling - special chars - removed": DiffSpellRemovedSpecialChars,
        "different spelling - whitespaces - replacement with special char": DiffSpellWhitespaceReplace,
        "different spelling - special chars - whitespace replacement": DiffSpellSpecialCharsReplace,
        "different spelling - vendor": DiffSpellVendor,
        "different spelling - lower and uppercase": DiffSpellLowerAndUppercase,

        "format errors - underscore": FEundersorces,
        "format error - transposed token": FEtransposedToken,
        "format error - whitespaces - special char mixed": FEmixedReplaceWhitespaces,
    }
    """
    _strategies = {
        
        
        "different spelling - synonyms": SubcatB,
        "different spelling - abbreviations": SubcatB,
        "different spelling - wrong semantic": SubcatB,
        "format errors - multiple products in row": SubcatB,
    }
    """

    @classmethod
    def create(cls, name) -> None|BenchmarkSubcategoryStrategie:
        if name not in cls._strategies:
            #raise ValueError(f"Unknown subcategory: {name}")
            return None
        return cls._strategies[name]()