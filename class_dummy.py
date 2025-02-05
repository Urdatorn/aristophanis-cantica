from class_syllable import Syllable
from class_word import Word

text = '''[ἀ]{έ}{να}[οι] {Νε}{φέ}[λαι]'''
syllables = [Syllable(s) for s in text.split()]