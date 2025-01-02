from lxml import etree

from grc_utils import normalize_word

from vowels import UPPER_SMOOTH_ACUTE, UPPER_ROUGH_ACUTE, LOWER_ACUTE, LOWER_SMOOTH_ACUTE, LOWER_ROUGH_ACUTE, LOWER_DIAERESIS_ACUTE
from vowels import UPPER_SMOOTH_GRAVE, UPPER_ROUGH_GRAVE, LOWER_GRAVE, LOWER_SMOOTH_GRAVE, LOWER_ROUGH_GRAVE, LOWER_DIAERESIS_GRAVE
from vowels import UPPER_SMOOTH_CIRCUMFLEX, UPPER_ROUGH_CIRCUMFLEX, LOWER_CIRCUMFLEX, LOWER_SMOOTH_CIRCUMFLEX, LOWER_ROUGH_CIRCUMFLEX, LOWER_DIAERESIS_CIRCUMFLEX

accents = {
    'acute': set(UPPER_SMOOTH_ACUTE + UPPER_ROUGH_ACUTE + LOWER_ACUTE 
                 + LOWER_SMOOTH_ACUTE + LOWER_ROUGH_ACUTE + LOWER_DIAERESIS_ACUTE),
    'grave': set(UPPER_SMOOTH_GRAVE + UPPER_ROUGH_GRAVE + LOWER_GRAVE
                 + LOWER_SMOOTH_GRAVE + LOWER_ROUGH_GRAVE + LOWER_DIAERESIS_GRAVE),
    'circumflex': set(UPPER_SMOOTH_CIRCUMFLEX + UPPER_ROUGH_CIRCUMFLEX + LOWER_CIRCUMFLEX
                      + LOWER_SMOOTH_CIRCUMFLEX + LOWER_ROUGH_CIRCUMFLEX + LOWER_DIAERESIS_CIRCUMFLEX)
}

def metrically_responding_lines(strophe_line, antistrophe_line):
    """
    Takes two <l>:s and returns True if they contain the exact same sequence of <syll> weight attributes.
    E.g.:
            <l n="208-209" metre="2 cr"><syll weight="heavy">Ἐκ</syll><syll weight="light">πέ</syll><syll weight="heavy">φευγ</syll>',<syll weight="heavy">οἴ</syll><syll weight="light">χε</syll><syll weight="heavy">ται</syll></l>
            <l n="223-224" metre="2 cr"><syll weight="heavy">ὅσ</syll><syll weight="light">τι</syll><syll weight="heavy">ς, ὦ Ζ</syll><syll weight="heavy">εῦ</syll><syll weight="light">πά</syll><syll weight="heavy">τερ</syll></l>
    """
    syllables1 = strophe_line.findall('syll')
    syllables2 = antistrophe_line.findall('syll')
    
    if len(syllables1) != len(syllables2):
        return False
    
    for syll1, syll2 in zip(syllables1, syllables2):
        if syll1.get('weight') != syll2.get('weight'):
            return False
    
    return True

line1 = etree.fromstring('<l n="208-209" metre="2 cr"><syll weight="heavy">Ἐκ</syll><syll weight="light">πέ</syll><syll weight="heavy">φευγ</syll><syll weight="heavy">οἴ</syll><syll weight="light">χε</syll><syll weight="heavy">ται</syll></l>')
line2 = etree.fromstring('<l n="223-224" metre="2 cr"><syll weight="heavy">ὅσ</syll><syll weight="light">τι</syll><syll weight="heavy">ς, ὦ Ζ</syll><syll weight="heavy">εῦ</syll><syll weight="light">πά</syll><syll weight="heavy">τερ</syll></l>')
print(metrically_responding_lines(line1, line2))

def accentually_responding_lines(strophe_line, antistrophe_line):
    """
    For two <l>:s which are metrically_responding_lines, return a list of maps of pairs of syllables with the both same ordinal and accent (acute, grave or circumflex).
    For example, in the below lines (last lines from the first two strophes of Pind. Ol. 2), the first and fifth syllables have acutes:
        <syll weight="light">ἄ</syll><syll weight="heavy">ω</syll><syll weight="light">το</syll><syll weight="heavy">ν ὀρ</syll><syll weight="light">θό</syll><syll weight="light">πο</syll><syll weight="heavy">λιν</syll>
        <syll weight="light">τρί</syll><syll weight="heavy">αν</syll> <syll weight="light">σφί</syll><syll weight="heavy">σιν</syll> <syll weight="light">κό</syll><syll weight="light">μι</syll><syll weight="heavy">σον</syll>
    In that case, the function should return 
        [{'ἄ': 'τρί', 'θό': 'κό'}, {}, {}]
    """
    if not metrically_responding_lines(strophe_line, antistrophe_line):
        return False
    
    syllables1 = strophe_line.findall('syll')
    syllables2 = antistrophe_line.findall('syll')
    
    accent_maps = [dict(), dict(), dict()]  # [acute_map, grave_map, circumflex_map]
    
    for syll1, syll2 in zip(syllables1, syllables2):
        norm_syll1 = normalize_word(syll1.text)
        norm_syll2 = normalize_word(syll2.text)
        for i, (accent, chars) in enumerate(accents.items()):
            if any(ch in chars for ch in norm_syll1) and any(ch in chars for ch in norm_syll2):
                # Store the entire text of the syllable
                accent_maps[i][syll1.text] = syll2.text
    return accent_maps

def responding_acutes(strophe_line, antistrophe_line):
    """
    For two <l>:s which are metrically_responding_lines, return how many syllables with the same ordinal have the same acute accent.
    """
    accent_maps = accentually_responding_lines(strophe_line, antistrophe_line)
    if not accent_maps:
        return False
    
    return len(accent_maps[0])

strophe_line = etree.fromstring('<l n="" metre=""><syll weight="light">ἄ</syll><syll weight="heavy">ῶ</syll><syll weight="light">το</syll><syll weight="heavy">ν ὀρ</syll><syll weight="light">θό</syll><syll weight="light">πο</syll><syll weight="heavy">λὶν</syll></l>')
antistrophe_line = etree.fromstring('<l n="" metre=""><syll weight="light">τρί</syll><syll weight="heavy">ὦν</syll> <syll weight="light">σφί</syll><syll weight="heavy">σιν</syll> <syll weight="light">κό</syll><syll weight="light">μι</syll><syll weight="heavy">σὸν</syll></l>')
print(accentually_responding_lines(strophe_line, antistrophe_line))

strophe_line = etree.fromstring('<l n="" metre=""><syll weight="light">ἄ</syll><syll weight="heavy">ω</syll><syll weight="light">το</syll><syll weight="heavy">ν ὀρ</syll><syll weight="light">θό</syll><syll weight="light">πο</syll><syll weight="heavy">λιν</syll></l>')
antistrophe_line = etree.fromstring('<l n="" metre=""><syll weight="light">τρί</syll><syll weight="heavy">αν</syll> <syll weight="light">σφί</syll><syll weight="heavy">σιν</syll> <syll weight="light">κό</syll><syll weight="light">μι</syll><syll weight="heavy">σον</syll></l>')
print(accentually_responding_lines(strophe_line, antistrophe_line))

def responds(strophe, antistrophe):
    """
    Takes a pair of 
    <strophe type="strophe" responsion="XXXX"> and 
    <strophe type="antistrophe" responsion="XXXX"> XML elements containing <l>'s with nested <syll> elements.
    """