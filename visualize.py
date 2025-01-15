import sys
from lxml import etree
from stats import (
    accentually_responding_syllables_of_line_pair,
    build_units_for_accent,
    canonical_sylls,
    has_acute
)
from vowels import vowel


def extract_strophe_accent_positions(strophe_line, antistrophe_line):
    accent_map = accentually_responding_syllables_of_line_pair(strophe_line, antistrophe_line)
    if not accent_map:
        return set(), set()

    acutes_list, _, circ_list = accent_map
    strophe_n = strophe_line.get('n')

    acutes_set = set()
    for dct in acutes_list:
        for (line_id, unit_ord) in dct.keys():
            if line_id == strophe_n:
                acutes_set.add(unit_ord)

    circ_set = set()
    for dct in circ_list:
        for (line_id, unit_ord) in dct.keys():
            if line_id == strophe_n:
                circ_set.add(unit_ord)

    return acutes_set, circ_set


def interpret_space_in_syllable(syll_text: str) -> tuple[bool, bool]:
    """
    Determine whether to place a space before or after the scansion symbol
    based on the position of the first space relative to the first vowel.
    
    Returns:
        (space_before, space_after)
    """
    # Find the first vowel index
    first_vowel_index = next((i for i, c in enumerate(syll_text) if vowel(c)), -1)
    if first_vowel_index == -1:
        # No vowel => no special space logic
        return (False, False)

    # Find the first space index
    space_index = syll_text.find(' ')
    if space_index == -1:
        # No space => no word boundary from within this syllable
        return (False, False)

    # If the first space is before the first vowel => space goes before
    if space_index < first_vowel_index:
        return (True, False)
    else:
        # If the space is after the first vowel => space goes after
        return (False, True)


def metre_line_with_accents(s_line, acutes_set, circ_set):
    """
    Builds a scansion line pattern, inserting spaces in the pattern wherever
    the syllable's text has a space in relation to its first vowel. 
    """
    # We assume you have these from elsewhere in your code:
    # canonical_sylls(s_line) to get each syllable's processed weight
    # build_units_for_accent(s_line) to identify 'single' vs. 'double'
    syll_weights = canonical_sylls(s_line)
    units = build_units_for_accent(s_line)

    line_pattern = []

    for i, u in enumerate(units):
        ord_ = u['unit_ord']

        # SINGLE SYLLABLE UNITS
        if u['type'] == 'single':
            syll = u['syll']
            text = syll.text or ""  # The actual text for reference
            weight = syll_weights[i]
            anceps = (syll.get('anceps') == 'True')
            space_before, space_after = interpret_space_in_syllable(text)

            # Figure out the scansion symbol (pattern) for this syllable
            if weight == 'anceps':
                pattern = 'x'
            elif weight == 'heavy':
                if ord_ in circ_set:
                    pattern = '-^'
                elif ord_ in acutes_set:
                    pattern = "-'"
                else:
                    # Check if this is 'brevis in longo' turned heavy
                    is_brevis_in_longo = (
                        syll.get('weight') == 'light'
                        and i == len(units) - 1
                        and syll.get('resolution') != 'True'
                    )
                    pattern = 'U' if is_brevis_in_longo else '-'
            else:
                # weight == 'light'
                if ord_ in acutes_set:
                    pattern = "u'"
                else:
                    pattern = 'u'

            # Now add spaces around the pattern based on interpret_space_in_syllable
            if space_before:
                line_pattern.append(" ")
            line_pattern.append(pattern)
            if space_after:
                line_pattern.append(" ")

        # DOUBLE SYLLABLE UNITS
        elif u['type'] == 'double':
            s1 = u['syll1']
            s2 = u['syll2']
            # Typically no special "spaces" for double syllables unless you decide otherwise
            if ord_ in acutes_set:
                if has_acute(s1):
                    line_pattern.append("(u'u)")
                elif has_acute(s2):
                    line_pattern.append("(uu')")
                else:
                    line_pattern.append("(uu)")
            else:
                line_pattern.append("(uu)")

    # Return the joined pattern without any extra trimming 
    # (so leading/trailing spaces only show up if your text *truly* implies them)
    return ''.join(line_pattern)


def restore_text(l_element):
    text_fragments = []
    
    for child in l_element:
        if child.tag == 'label':
            continue

        if child.tag == 'syll' and child.text:
            text_fragments.append(child.text)
        
        if child.tail:
            text_fragments.append(child.tail)

    combined = ''.join(text_fragments)
    return ' '.join(combined.split())


def metre_strophe_with_accents(strophe, antistrophe):
    s_lines = strophe.findall('l')
    a_lines = antistrophe.findall('l')
    if len(s_lines) != len(a_lines):
        return "Line-count mismatch!"

    lines_output = []
    for s_line, a_line in zip(s_lines, a_lines):
        acutes_set, circ_set = extract_strophe_accent_positions(s_line, a_line)
        pattern_str = metre_line_with_accents(s_line, acutes_set, circ_set)
        line_n = s_line.get('n', '???')
        original_text = restore_text(s_line)

        lines_output.append(f"{line_n}: {pattern_str}")
        lines_output.append(original_text)

    return "\n".join(lines_output)


from lxml import etree

def visualize_responsion(responsion):
    tree = etree.parse("responsion_acharnenses_compiled.xml")

    strophes = tree.xpath(f'//strophe[@type="strophe" and @responsion="{responsion}"]')
    antistrophes = tree.xpath(f'//strophe[@type="antistrophe" and @responsion="{responsion}"]')

    if len(strophes) != len(antistrophes):
        print(f"Mismatch in strophe and antistrophe counts for responsion {responsion}.")
        return

    # ANSI color codes
    RED = '\033[31m'
    GREEN = '\033[32m'
    RESET = '\033[0m'

    def color_accents(text):
        # Replace ^ and ´ with colored versions, resetting the color after each character
        return text.replace('^', f"{RED}^{RESET}").replace("'", f"{GREEN}'{RESET}")

    for strophe, antistrophe in zip(strophes, antistrophes):
        print(f"\nResponsion: {responsion}")
        print("\nStrophe:")
        strophe_text = metre_strophe_with_accents(strophe, antistrophe)
        print(color_accents(strophe_text))

        print("\nAntistrophe:")
        antistrophe_text = metre_strophe_with_accents(antistrophe, strophe)
        print(color_accents(antistrophe_text))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python visualize.py <responsion_number>")
        sys.exit(1)

    responsion_number = sys.argv[1]
    visualize_responsion(responsion_number)