import random
import re
from abc import abstractmethod
from typing import override
from surroundingkeys import get_next_letters
from string_miner.string_miner import StringMiner


class BenchmarkSubcategoryStrategie:
    def __init__(self):
        super().__init__()

    @abstractmethod
    def process(self, vendor: str, product: str) -> list[str]:
        pass


class KeyboardNeighbours:
    @staticmethod
    def get_neighbours(keyboard: str, letter: str):
        neighbours = []
        result = get_next_letters(letter=letter, keyboard=keyboard)
        if result is not None:
            if "side" in result[letter]:
                neighbours = neighbours + result[letter]["side"]
            if "top" in result[letter]:
                neighbours = neighbours + result[letter]["top"]
            if "bottom" in result[letter]:
                neighbours = neighbours + result[letter]["bottom"]
        return neighbours


    @staticmethod
    def get_neighbours_same_type(keyboard: str, letter: str):
        neighbours = []
        result = get_next_letters(letter=letter, keyboard=keyboard)
        if result is not None:
            if "side" in result[letter]:
                neighbours = neighbours + result[letter]["side"]
            if "top" in result[letter]:
                neighbours = neighbours + result[letter]["top"]
            if "bottom" in result[letter]:
                neighbours = neighbours + result[letter]["bottom"]

        if letter.isalpha():
            return [x for x in neighbours if str(x).isalpha()]
        else:
            return [x for x in neighbours if str(x).isnumeric()]



class LexWrongLetterTyping(BenchmarkSubcategoryStrategie):
    """
    generator for category "lexical errors"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes in alpha letters one mistake with a neighbouring letter. same for numbers.
        """
        pos = 0
        alphanum_pos = []
        for letter in product:
            if letter.isalnum():
                alphanum_pos.append(pos)
            pos = pos + 1

        if len(alphanum_pos) == 0:
            return ["SKIP"]

        queryset = []
        i = 0
        while i <= len(alphanum_pos) and i < 3:
            rnd_letter = random.choice(alphanum_pos)
            letter = product[rnd_letter]
            # TODO keyboard from config
            neighbours = KeyboardNeighbours.get_neighbours_same_type(letter=letter, keyboard="kbdgr")
            if len(neighbours) == 0:
                return ["SKIP"]
            rnd_neighbour = random.choice(neighbours)
            if letter.isupper():
                replace_letter = rnd_neighbour.upper()
            else:
                replace_letter = rnd_neighbour.lower()
            result = product[:rnd_letter] + replace_letter + product[rnd_letter + 1:]
            queryset.append(result)
            i = i + 1
            alphanum_pos.remove(rnd_letter)
        return queryset

class LexLowerAndUppercase(BenchmarkSubcategoryStrategie):
    """
    generator for category "lexical errors"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes lower und uppercase characters into opposite.
        """
        pos = 0
        alpha_pos = []
        for letter in product:
            if letter.isalpha():
                alpha_pos.append(pos)
            pos = pos + 1

        if len(alpha_pos) == 0:
            return ["SKIP"]

        queryset = []
        i = 0
        while i <= len(alpha_pos) and i < 3:
            rnd_letter_pos = random.choice(alpha_pos)
            letter = product[rnd_letter_pos]
            if letter.isupper():
                replace_letter = letter.lower()
            else:
                replace_letter = letter.upper()
            result = product[:rnd_letter_pos] + replace_letter + product[rnd_letter_pos + 1:]
            queryset.append(result)

            alpha_pos.remove(rnd_letter_pos)
            i = i + 1
        return queryset

class LexRedundantLetters(BenchmarkSubcategoryStrategie):
    """
    generator for category "lexical errors"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes redundant letters
        """
        pos = 0
        alpha_pos = []
        for letter in product:
            if letter.isalpha():
                alpha_pos.append(pos)
            pos = pos + 1

        if len(alpha_pos) == 0:
            return ["SKIP"]

        queryset = []
        i = 0
        while i <= len(alpha_pos) and i < 3:
            rnd_letter_pos = random.choice(alpha_pos)
            letter = product[rnd_letter_pos]
            replace_letter = 2 * letter
            result = product[:rnd_letter_pos] + replace_letter + product[rnd_letter_pos + 1:]
            queryset.append(result)
            alpha_pos.remove(rnd_letter_pos)
            i = i + 1
        return queryset


class LexInsertNeighboursLetters(BenchmarkSubcategoryStrategie):
    """
    generator for category "lexical errors"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes inserting neighbours letters.
        """
        pos = 0
        alphanum_pos = []
        for letter in product:
            if letter.isalnum():
                alphanum_pos.append(pos)
            pos = pos + 1

        if len(alphanum_pos) == 0:
            return ["SKIP"]

        queryset = []
        i = 0
        while i <= len(alphanum_pos) and i < 3:
            rnd_letter = random.choice(alphanum_pos)
            letter = product[rnd_letter]
            # TODO keyboard from config
            neighbours = KeyboardNeighbours.get_neighbours_same_type(letter=letter, keyboard="kbdgr")
            if len(neighbours) == 0:
                return ["SKIP"]
            rnd_neighbour = random.choice(neighbours)
            if letter.isupper():
                replace_letter = rnd_neighbour.upper()
            else:
                replace_letter = rnd_neighbour.lower()
            result = product[:rnd_letter] + letter+replace_letter + product[rnd_letter + 1:]
            queryset.append(result)
            i = i + 1
            alphanum_pos.remove(rnd_letter)
        return queryset

class LexDeletionLetters(BenchmarkSubcategoryStrategie):
    """
    generator for category "lexical errors"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes inserting neighbours letters.
        """
        pos = 0
        alphanum_pos = []
        for letter in product:
            if letter.isalnum():
                alphanum_pos.append(pos)
            pos = pos + 1

        if len(alphanum_pos) == 0:
            return ["SKIP"]

        queryset = []
        i = 0
        while i <= len(alphanum_pos) and i < 3:
            rnd_letter = random.choice(alphanum_pos)
            result = product[:rnd_letter] + product[rnd_letter + 1:]
            queryset.append(result)
            i = i + 1
            alphanum_pos.remove(rnd_letter)
        return queryset

class LexTranspositionLetters(BenchmarkSubcategoryStrategie):
    """
    generator for category "lexical errors"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes transposition letters.
        """
        queryset = []
        alphanum_pos = list(range(len(product)))

        transposition_tuples = []
        i = 0
        while i < len(alphanum_pos) - 1 and i < 3:
            random_choice = random.choice(alphanum_pos)
            right = True
            left = True
            for transposition in transposition_tuples:
                if transposition[0] == random_choice:
                    right = False
                elif transposition[1] == random_choice:
                    left = False
            if random_choice == 0 or product[random_choice] == product[random_choice - 1]:
                left = False
            if random_choice == len(product) - 1 or product[random_choice] == product[random_choice + 1]:
                right = False
            if left is False and right is False:
                alphanum_pos.remove(random_choice)
                continue
            elif left and right:
                random_choice_neighbour = random.choice([random_choice - 1, random_choice + 1])
            elif right:
                random_choice_neighbour = random_choice + 1
            else:
                random_choice_neighbour = random_choice - 1

            if random_choice > random_choice_neighbour:
                random_choice_neighbour = random_choice_neighbour + 1
                random_choice = random_choice - 1
            transposition_tuples.append((random_choice, random_choice_neighbour))

            result = product[:random_choice]
            result = result + product[random_choice_neighbour] + product[random_choice]
            if random_choice_neighbour < len(product) -1:
                result = result + product[random_choice_neighbour +1:]
            queryset.append(result)

            i = i + 1
        return queryset

class LexMissingToken(BenchmarkSubcategoryStrategie):
    """
    generator for category "lexical errors"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes missing tokens.
        """
        tokens = product.split()
        choices = list(range(len(tokens)))
        if len(choices) < 2:
            return ["SKIP"]

        queryset = []
        i = 0
        while len(choices)  > 0 and i < 3:
            random_choice = random.choice(choices)
            result = []
            pos = 0
            for token in tokens:
                if pos != random_choice:
                    result.append(token)
                pos = pos + 1
            queryset.append(" ".join(result))
            choices.remove(random_choice)
            i = i + 1
        return queryset

class LexNumberAlphaMix:
    """
    generator for category "lexical errors"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes Alpha Number Mix.
        """
        string_miner = StringMiner()
        character = string_miner.characterize(product)
        if 'alpha' not in character['segment_types'] or 'number' not in character['segment_types']:
            return ["SKIP"]
        transposition_pos = []
        for i in range(len(character['segment_types']) - 1):
            type = character['segment_types'][i]
            type_compare = character['segment_types'][i + 1]
            if type !="special" and type_compare != "special" and type != type_compare:
                transposition_pos.append(i)
        queryset = []
        for i in range(min(len(transposition_pos), 3)):
            pos = transposition_pos[i]
            result = character['segments'][:pos] + [character['segments'][pos + 1]] + [character['segments'][pos]] + character['segments'][pos + 2:]
            queryset.append("".join(result))

        if len(queryset) == 0:
            return ["SKIP"]

        return queryset


class FEtransposedToken(BenchmarkSubcategoryStrategie):
    """
    generator for category "format error"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes transposed tokens.
        """
        tokens = product.split()
        choices = list(range(len(tokens)))

        transposition_tuples = []

        if len(choices) < 2:
            return ["SKIP"]

        queryset = []
        i = 0
        while i <= len(choices) - 1 and i < 3:
            random_choice = random.choice(choices)
            left = True
            right = True
            if random_choice == 0 or tokens[random_choice] == tokens[random_choice - 1]:
                left = False
            if (random_choice == len(tokens) - 1 or
                    tokens[random_choice] == tokens[random_choice + 1]):
                right = False

            for transposition in transposition_tuples:
                if transposition[0] == random_choice:
                    right = False
                elif transposition[1] == random_choice:
                    left = False

            if left is False and right is False:
                choices.remove(random_choice)
                continue
            elif left and right:
                random_choice_neighbour = random.choice([random_choice - 1, random_choice + 1])
            elif right:
                random_choice_neighbour = random_choice + 1
            else:
                random_choice_neighbour = random_choice - 1

            if random_choice > random_choice_neighbour:
                random_choice_neighbour = random_choice_neighbour + 1
                random_choice = random_choice - 1
            transposition_tuples.append((random_choice, random_choice_neighbour))

            result = []
            for token_nr in choices:
                if token_nr == random_choice:
                    result.append(tokens[random_choice_neighbour])
                elif token_nr == random_choice_neighbour:
                    result.append(tokens[random_choice])
                else:
                    result.append(tokens[token_nr])
            queryset.append(" ".join(result))
            i = i + 1
            choices.remove(random_choice)
        return queryset


class DiffSpellRemovedWhitespaces(BenchmarkSubcategoryStrategie):
    """
    generator for category "Different Spelling"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes removing whitespaces.
        """
        tokens = product.split()
        if len(tokens) < 2:
            return ["SKIP"]
        queryset = []
        for i in range(len(tokens) - 1):
            merged = tokens.copy()
            merged[i] = merged[i] + merged[i + 1]
            del merged[i + 1]
            queryset.append(" ".join(merged))
        return queryset

class DiffSpellWhitespaceReplace(BenchmarkSubcategoryStrategie):
    """
    generator for category "Different Spelling"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes replacing whitespaces with specialchar minus or underscores.
        """
        tokens = product.split()
        if len(tokens) < 2:
            return ["SKIP"]
        queryset = []
        sign = "-"
        for s in range(0,2):
            for i in range(len(tokens) - 1):
                merged = tokens.copy()
                merged[i] = merged[i] + sign + merged[i + 1]
                del(merged[i + 1])
                queryset.append(" ".join(merged))
            sign = "_"
        return queryset

class DiffSpellRemovedSpecialChars(BenchmarkSubcategoryStrategie):
    """
    generator for category "Different Spelling"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes removing special chars.
        """
        pos = 0
        special_chars_positions = []
        for char in product:
            if not char.isalnum() and not char.isspace():
                special_chars_positions.append(pos)
            pos = pos + 1

        if len(special_chars_positions) == 0:
            return ["SKIP"]

        queryset = []
        for i in range(min(3, len(special_chars_positions))):
            replace_position = special_chars_positions[i]
            queryset.append(product[:replace_position] + product[replace_position + 1:])
        return queryset

class DiffSpellSpecialCharsReplace(BenchmarkSubcategoryStrategie):
    """
        generator for category "Different Spelling"
        """

    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes replacing special chars.
        """
        pos = 0
        special_chars_positions = []
        for char in product:
            if not char.isalnum() and not char.isspace():
                special_chars_positions.append(pos)
            pos = pos + 1

        if len(special_chars_positions) == 0:
            return ["SKIP"]

        queryset = []
        for i in range(min(3, len(special_chars_positions))):
            replace_position = special_chars_positions[i]
            queryset.append(product[:replace_position] + " " + product[replace_position + 1:])
        return queryset

class DiffSpellVendor(BenchmarkSubcategoryStrategie):
    """
           generator for category "Different Spelling"
           """

    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes adding vendor as prefix and suffix with comma
        """
        return [vendor + " " + product, product+ ", " + vendor]

class DiffSpellLowerAndUppercase(BenchmarkSubcategoryStrategie):
    """
    generator for category "Different Spelling"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes lower and uppercase
        """
        return [product.lower(), product.upper()]

class FEundersorces(BenchmarkSubcategoryStrategie):
    """
    generator for category "Different Spelling"
    """
    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes underscores
        """
        return [str(re.sub(r'\W', '_', product))]

class FEmixedReplaceWhitespaces(BenchmarkSubcategoryStrategie):
    """
    generator for category "format error"
    """

    @override
    def process(self, vendor: str, product: str) -> list[str]:
        """
        processes replacing whitespaces with mixed special chars
        """
        special_chars = ["-", ",", ";"]

        pos = 0
        special_chars_positions = []
        for char in product:
            if char.isspace():
                special_chars_positions.append(pos)
            pos = pos + 1

        if len(special_chars_positions) == 0:
            return ["SKIP"]

        special_char = random.choice(special_chars)
        pos = random.choice(special_chars_positions)
        return [product[0:pos] + special_char + product[pos + 1:]]


        # TODO delete
        """

        if len(special_chars_positions) == 1:
            return queryset

        for a in range(len(special_chars_positions)):
            special_char = product[special_chars_positions[i]]
            if a == len(special_chars_positions) - 1:
                b = 0
            else:
                b = a + 1
            special_char2 = special_chars[b]
            replace_chars = [special_char, special_char2]

            result = ""
            i = 0
            for char in product:
                if char.isspace():
                    result += replace_chars[i % 2]
                    i += 1
                else:
                    result += char
            queryset.append(result)
        
        return list(set(queryset))
        
        """
