import sys
from lxml import etree
from stats import (
    accentually_responding_syllables_of_line_pair,
    build_units_for_accent,
    metrically_responding_lines,
    accents,
    normalize_word,
    has_acute
)


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


def metre_line_with_accents(s_line, acutes_set, circ_set):
    units = build_units_for_accent(s_line)
    line_pattern = []

    for u in units:
        ord_ = u['unit_ord']

        if u['type'] == 'single':
            syll = u['syll']
            weight = syll.get('weight', '')
            anceps = (syll.get('anceps') == 'True')

            if anceps:
                line_pattern.append('x')
                continue

            if weight == 'heavy':
                if ord_ in circ_set:
                    line_pattern.append('-^')
                elif ord_ in acutes_set:
                    line_pattern.append("-'")
                else:
                    line_pattern.append('-')
            else:
                if ord_ in acutes_set:
                    line_pattern.append("u'")
                else:
                    line_pattern.append('u')

        elif u['type'] == 'double':
            s1 = u['syll1']
            s2 = u['syll2']
            if ord_ in acutes_set:
                if has_acute(s1):
                    line_pattern.append("(u'u)")
                elif has_acute(s2):
                    line_pattern.append("(uu')")
                else:
                    line_pattern.append("(uu)")
            else:
                line_pattern.append("(uu)")

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
        return text.replace('^', f"{RED}^ {RESET}").replace("'", f"{GREEN}' {RESET}")

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