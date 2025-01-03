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
    """
    Builds a string representing the strophe line's metrical pattern.
    """
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
    """
    Given an <l> element, return the original text without XML markup.
    """
    text_fragments = []
    
    # Iterate over children of <l> in order
    for child in l_element:
        # Ignore <label> tags, in case they appear
        if child.tag == 'label':
            continue

        # If it's a syllable, we take whatever text is inside
        if child.tag == 'syll' and child.text:
            text_fragments.append(child.text)
        
        # If there's a tail (text after the element), append it too
        # (Though in most TEI-like structures, the tail of a <syll> is often whitespace
        # or empty. Adjust if you do need it.)
        if child.tail:
            text_fragments.append(child.tail)

    # Join everything together, removing double spaces if necessary
    combined = ''.join(text_fragments)
    return ' '.join(combined.split())  # This step just normalizes spacing


def metre_strophe_with_accents(strophe, antistrophe):
    s_lines = strophe.findall('l')
    a_lines = antistrophe.findall('l')
    if len(s_lines) != len(a_lines):
        return "Line-count mismatch!"

    lines_output = []
    for s_line, a_line in zip(s_lines, a_lines):
        # 1) Determine accent positions
        acutes_set, circ_set = extract_strophe_accent_positions(s_line, a_line)
        # 2) Build the metre pattern
        pattern_str = metre_line_with_accents(s_line, acutes_set, circ_set)
        line_n = s_line.get('n', '???')

        # 3) Reconstruct the original text from the <l> element
        original_text = restore_text(s_line)

        # Output: two lines for each <l>
        lines_output.append(f"{line_n}: {pattern_str}")
        lines_output.append(original_text)

    return "\n".join(lines_output)


if __name__ == "__main__":
    tree = etree.parse("responsion_acharnenses_compiled.xml")

    strophe = tree.xpath('//strophe[@type="strophe" and @responsion="0001"]')[0]
    antistrophe = tree.xpath('//strophe[@type="antistrophe" and @responsion="0001"]')[0]

    print("Strophe with accent-annotated metre (plus the original text):")
    print(metre_strophe_with_accents(strophe, antistrophe))

    print("\nAntistrophe with accent-annotated metre (plus original text):")
    print(metre_strophe_with_accents(antistrophe, strophe))