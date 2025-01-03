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

### METRICAL RESPONSION ###

def canonical_sylls(xml_line):
    """
    Returns a list of 'weights' for the line, with special rules:
      - Two consecutive syllables both with resolution="True" count as one 'heavy'.
      - A syll with anceps="True" becomes 'anceps', ignoring weight.
      - Otherwise, use 'heavy' or 'light' as in the <syll weight="..."> attribute.
    """
    syllables = xml_line.findall('.//syll')
    result = []
    i = 0

    while i < len(syllables):
        current = syllables[i]
        is_anceps = current.get('anceps') == 'True'
        is_resolution = current.get('resolution') == 'True'
        current_weight = current.get('weight', '')  # e.g. 'heavy' or 'light'

        # (1) If consecutive resolution => treat them as one heavy
        if (
            is_resolution and 
            i + 1 < len(syllables) and 
            syllables[i + 1].get('resolution') == 'True'
        ):
            # Combine next two "u" (light) with resolution => 'heavy'
            result.append('heavy')
            i += 2  # Skip the next syllable
            continue

        # (2) If anceps => treat as 'anceps', ignoring weight
        if is_anceps:
            result.append('anceps')
            i += 1
            continue

        # (3) Otherwise => just use the given weight
        if current_weight in ('heavy', 'light'):
            result.append(current_weight)
        else:
            # Fallback if something unexpected
            result.append('light')  # or 'heavy'—whatever default you want
        i += 1

    return result

def metrically_responding_lines(strophe_line, antistrophe_line):
    """
    Takes two <l> elements and returns True if they have the same 'canonical' sequence
    of syllables, where:
      - Two consecutive resolution='True' lights count as one heavy.
      - Any syllable with anceps='True' matches anything.
      - Else: heavy must match heavy, light must match light.
    """
    c1 = canonical_sylls(strophe_line)
    c2 = canonical_sylls(antistrophe_line)

    # If they collapse to different lengths => mismatch
    if len(c1) != len(c2):
        return False

    # Compare each slot
    for s1, s2 in zip(c1, c2):
        # (4) If either is 'anceps', no mismatch
        if s1 == 'anceps' or s2 == 'anceps':
            continue

        # (5) Otherwise the weights must match
        if s1 != s2:
            return False

    return True

#line1 = etree.fromstring('<l n="208-209" metre="2 cr"><syll weight="heavy">Ἐκ</syll><syll weight="light">πέ</syll><syll weight="heavy">φευγ</syll><syll weight="heavy">οἴ</syll><syll weight="light">χε</syll><syll weight="heavy">ται</syll></l>')
#line2 = etree.fromstring('<l n="223-224" metre="2 cr"><syll weight="heavy">ὅσ</syll><syll weight="light">τι</syll><syll weight="heavy">ς, ὦ Ζ</syll><syll weight="heavy">εῦ</syll><syll weight="light">πά</syll><syll weight="heavy">τερ</syll></l>')
#print(metrically_responding_lines(line1, line2))

############################
### ACCENTUAL RESPONSION ###
############################

def build_units_for_accent(line):
    """
    Convert a <l> element into a list of 'units' for accent comparison:
      - single -> {'type': 'single', 'syll': syllElem}
      - double -> {'type': 'double', 'syll1': s1, 'syll2': s2}
    Two consecutive resolution="True" lights become one 'double' unit.
    Everything else remains a single.
    """
    sylls = line.findall('.//syll')
    units = []
    i = 0

    while i < len(sylls):
        s = sylls[i]
        if (s.get('resolution') == 'True'
            and i + 1 < len(sylls)
            and sylls[i + 1].get('resolution') == 'True'):
            # Merge two consecutive resolved syllables into one "double" unit
            units.append({
                'type': 'double',
                'syll1': s,
                'syll2': sylls[i + 1]
            })
            i += 2
        else:
            # Single unit
            units.append({'type': 'single', 'syll': s})
            i += 1

    return units


def do_accent_match(syll1, syll2, accent_maps):
    """
    Checks if two single syllables share an accent (acute/grave/circumflex).
    If yes, store them in the appropriate accent_maps[i].
    """
    text1 = syll1.text or ""
    text2 = syll2.text or ""
    norm1 = normalize_word(text1)
    norm2 = normalize_word(text2)

    for i, (accent_name, accent_chars) in enumerate(accents.items()):
        # If each syllable has at least one of these accent characters
        if any(ch in accent_chars for ch in norm1) and any(ch in accent_chars for ch in norm2):
            # Store the raw text of syll1 -> syll2
            accent_maps[i][text1] = text2


def accentually_responding_syllables_of_line_pair(strophe_line, antistrophe_line):
    """
    For two <l> elements that pass metrically_responding_lines(), returns
    a list [acute_map, grave_map, circumflex_map].
    
    Special rules:
      - If one canonical slot is a double resolution unit and the other is a single heavy, 
        skip accent matching (they never match).
      - If both are double, compare their sub-syllables 1-to-1 and 2-to-2.
      - Otherwise, compare single-to-single as before.

    For example, in the below lines (last lines from the first two strophes of Pind. Ol. 2), the first and fifth syllables have acutes:
        <syll weight="light">ἄ</syll><syll weight="heavy">ω</syll><syll weight="light">το</syll><syll weight="heavy">ν ὀρ</syll><syll >weight="light">θό</syll><syll weight="light">πο</syll><syll weight="heavy">λιν</syll>
        <syll weight="light">τρί</syll><syll weight="heavy">αν</syll> <syll weight="light">σφί</syll><syll weight="heavy">σιν</syll> <syll weight="light">κό</syll><syll weight="light">μι</syll><syll weight="heavy">σον</syll>
    In that case, the function should return 
        [{'ἄ': 'τρί', 'θό': 'κό'}, {}, {}]
    """
    if not metrically_responding_lines(strophe_line, antistrophe_line):
        return False

    # Build canonical accent units for each line
    units1 = build_units_for_accent(strophe_line)
    units2 = build_units_for_accent(antistrophe_line)

    # We'll accumulate matches in these maps
    accent_maps = [dict(), dict(), dict()]  # [acute_map, grave_map, circumflex_map]

    # Compare the same index units
    for u1, u2 in zip(units1, units2):
        # If one is double and the other single => skip accent matching
        if u1['type'] == 'double' and u2['type'] == 'single':
            # (Double resol. vs single heavy? => no match)
            continue
        if u1['type'] == 'single' and u2['type'] == 'double':
            # (Single heavy vs double resol.? => no match)
            continue

        # If both single => compare the single syllables
        if u1['type'] == 'single' and u2['type'] == 'single':
            do_accent_match(u1['syll'], u2['syll'], accent_maps)

        # If both double => compare sub-syllables pairwise
        elif u1['type'] == 'double' and u2['type'] == 'double':
            do_accent_match(u1['syll1'], u2['syll1'], accent_maps)
            do_accent_match(u1['syll2'], u2['syll2'], accent_maps)

    return accent_maps


def responding_acutes(strophe_line, antistrophe_line):
    """
    For two <l>:s which are metrically_responding_lines, return how many syllables with the same ordinal have the same acute accent.
    """
    accent_maps = accentually_responding_syllables_of_line_pair(strophe_line, antistrophe_line)
    if not accent_maps:
        return False
    
    return len(accent_maps[0])

def responding_graves(strophe_line, antistrophe_line):
    """
    For two <l>:s which are metrically_responding_lines, return how many syllables with the same ordinal have the same grave accent.
    """
    accent_maps = accentually_responding_syllables_of_line_pair(strophe_line, antistrophe_line)
    if not accent_maps:
        return False
    
    return len(accent_maps[1])

def accentually_responding_syllables_of_strophe_pair(strophe, antistrophe):
    """
    Takes a pair of 
    <strophe type="strophe" responsion="XXXX"> and 
    <strophe type="antistrophe" responsion="XXXX"> XML elements with identical responsion attributes, and containing <l>'s with nested <syll> elements.
    Returns a list of maps of pairs of syllables with the both same ordinal and accent (acute, grave or circumflex).
    """
    # Check matching responsion
    if strophe.get('responsion') != antistrophe.get('responsion'):
        return False
    
    strophe_lines = strophe.findall('l')
    antistrophe_lines = antistrophe.findall('l')
    
    # Check line counts
    if len(strophe_lines) != len(antistrophe_lines):
        return False
    
    # Prepare combined maps for the strophe pair
    combined_accent_maps = [dict(), dict(), dict()]  # [acute_map, grave_map, circumflex_map]
    
    # Process each pair of lines
    for s_line, a_line in zip(strophe_lines, antistrophe_lines):
        if not metrically_responding_lines(s_line, a_line):
            print(f"Lines {s_line.get('n')} and {a_line.get('n')} do not metrically respond.")
            return False
        line_maps = accentually_responding_syllables_of_line_pair(s_line, a_line)
        if not line_maps:
            continue
        for i in range(3):
            combined_accent_maps[i].update(line_maps[i])
    
    return combined_accent_maps

strophe_line = etree.fromstring('<l n="" metre=""><syll weight="light">ἄ</syll><syll weight="heavy">ῶ</syll><syll weight="light">το</syll><syll weight="heavy">ν ὀρ</syll><syll weight="light">θό</syll><syll weight="light">πο</syll><syll weight="heavy">λὶν</syll></l>')
antistrophe_line = etree.fromstring('<l n="" metre=""><syll weight="light">τρί</syll><syll weight="heavy">ὦν</syll> <syll weight="light">σφί</syll><syll weight="heavy">σιν</syll> <syll weight="light">κό</syll><syll weight="light">μι</syll><syll weight="heavy">σὸν</syll></l>')
accent_maps = accentually_responding_syllables_of_line_pair(strophe_line, antistrophe_line)
print(f'Line total: {accent_maps}')
print(f'acutes: {len(accent_maps[0])}, graves: {len(accent_maps[1])}, circumflexes: {len(accent_maps[2])}')

strophe_line = etree.fromstring('<strophe type="strophe" responsion="0001"><l n="" metre=""><syll weight="light">ἄ</syll><syll weight="heavy">ῶ</syll><syll weight="light">το</syll><syll weight="heavy">ν ὀρ</syll><syll weight="light">θό</syll><syll weight="light">πο</syll><syll weight="heavy">λὶν</syll></l></strophe>')
antistrophe_line = etree.fromstring('<strophe type="strophe" responsion="0001"><l n="" metre=""><syll weight="light">τρί</syll><syll weight="heavy">ὦν</syll> <syll weight="light">σφί</syll><syll weight="heavy">σιν</syll> <syll weight="light">κό</syll><syll weight="light">μι</syll><syll weight="heavy">σὸν</syll></l></strophe>')
accent_maps = accentually_responding_syllables_of_strophe_pair(strophe_line, antistrophe_line)
print(f'Strophe total: {accent_maps}')
print(f'acutes: {len(accent_maps[0])}, graves: {len(accent_maps[1])}, circumflexes: {len(accent_maps[2])}')

# Parse the file
tree = etree.parse("responsion_acharnenses_processed.xml")

# Find matching strophe/antistrophe with responsion="0001"
strophe = tree.xpath('//strophe[@type="strophe" and @responsion="0001"]')[0]
antistrophe = tree.xpath('//strophe[@type="antistrophe" and @responsion="0001"]')[0]

# Call the function
accent_maps = accentually_responding_syllables_of_strophe_pair(strophe, antistrophe)
print(accent_maps)
print(f'acutes: {len(accent_maps[0])}, graves: {len(accent_maps[1])}, circumflexes: {len(accent_maps[2])}')
#print(f'Strophe total: {accent_maps}')
#print(f'acutes: {len(accent_maps[0])}, graves: {len(accent_maps[1])}, circumflexes: {len(accent_maps[2])}')