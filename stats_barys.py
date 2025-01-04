# stats_barys.py

#!/usr/bin/env python3
"""
stats_barys.py

This file reuses the basic metrical and accent helpers from stats.py
but overrides the accentual “barys/oxys” responsion logic.

You’ll need 'stats.py' in the same directory, or otherwise on your Python path.
"""

# ------------------------------------------------------------------------
# 1) IMPORTS (from your existing stats.py)
# ------------------------------------------------------------------------


from stats import (
    canonical_sylls,
    metrically_responding_lines,
    build_units_for_accent,
    is_heavy,
    has_acute,
    accents
)

from lxml import etree
from grc_utils import normalize_word

# If you do NOT export 'accents' from stats.py, you can define it here or import from vowels:
# from vowels import (UPPER_SMOOTH_ACUTE, ..., LOWER_DIAERESIS_CIRCUMFLEX)


# ------------------------------------------------------------------------
# 2) NEW BARYS/OXYS LOGIC
# ------------------------------------------------------------------------
def has_circumflex(syll):
    """
    Returns True if the given syll element has a circumflex accent.
    """
    text = syll.text or ""
    norm = normalize_word(text)
    return any(ch in accents['circumflex'] for ch in norm)


def barys_responsion(syll1, syll2, prev_syll1=None, prev_syll2=None):
    """
    Returns True if these two single syllables respond "barys" per your spec:
      (1) both have circumflex
      (2) both are heavy & each's preceding syllable has an acute
      (3) one has circumflex & the other meets #2
    """
    c1 = has_circumflex(syll1)
    c2 = has_circumflex(syll2)
    h1 = is_heavy(syll1)
    h2 = is_heavy(syll2)

    # preceding syllable acute?
    prev_acute_1 = (prev_syll1 is not None) and has_acute(prev_syll1)
    prev_acute_2 = (prev_syll2 is not None) and has_acute(prev_syll2)

    # (1) both have circumflex
    if c1 and c2:
        return True

    # (2) both heavy & preceding each has acute
    if h1 and h2 and prev_acute_1 and prev_acute_2:
        return True

    # (3) one has circumflex, the other is #2
    meets_2_for_syll1 = h1 and prev_acute_1
    meets_2_for_syll2 = h2 and prev_acute_2

    if (c1 and meets_2_for_syll2) or (c2 and meets_2_for_syll1):
        return True

    return False


def oxys_responsion(syll1, syll2):
    """
    Returns True if these two single syllables respond "oxys":
      - both are heavy
      - both have an acute
    """
    return (is_heavy(syll1) and is_heavy(syll2)
            and has_acute(syll1) and has_acute(syll2))


# ------------------------------------------------------------------------
# 3) UNIT-BY-UNIT COMPARISONS (like do_single_vs_single, etc.)
# ------------------------------------------------------------------------
def do_barys_single_vs_single(u1, u2, barys_list, oxys_list, all_sylls_1, all_sylls_2):
    """
    Compare strophe single vs. antistrophe single for barys or oxys matches.
    Figure out the 'previous' syllables (naive approach) and then do barys/oxys checks.
    """
    s_syll = u1['syll']
    a_syll = u2['syll']

    # minimal approach to get the previous <syll>
    def get_prev(syll, all_sylls):
        try:
            idx = all_sylls.index(syll)
            if idx > 0:
                return all_sylls[idx - 1]
        except ValueError:
            pass
        return None

    prev_s_syll = get_prev(s_syll, all_sylls_1)
    prev_a_syll = get_prev(a_syll, all_sylls_2)

    # Check barys
    if barys_responsion(s_syll, a_syll, prev_s_syll, prev_a_syll):
        barys_list.append({
            (u1['line_n'], u1['unit_ord']): s_syll.text or "",
            (u2['line_n'], u2['unit_ord']): a_syll.text or ""
        })
    # If not barys, check oxys
    elif oxys_responsion(s_syll, a_syll):
        oxys_list.append({
            (u1['line_n'], u1['unit_ord']): s_syll.text or "",
            (u2['line_n'], u2['unit_ord']): a_syll.text or ""
        })


def do_barys_double_vs_double(u1, u2, barys_list, oxys_list):
    """
    Compare resolution pair vs resolution pair for barys or oxys.
    Example: check if the 2nd sub-syllable in each pair respond barys or oxys.
    """
    s1 = u1['syll1']
    s2 = u1['syll2']
    a1 = u2['syll1']
    a2 = u2['syll2']

    # Example logic: treat s2 vs. a2 as the potential match, with s1 and a1 as "previous"
    if barys_responsion(s2, a2, prev_syll1=s1, prev_syll2=a1):
        barys_list.append({
            (u1['line_n'], u1['unit_ord']): s2.text or "",
            (u2['line_n'], u2['unit_ord']): a2.text or ""
        })
    elif oxys_responsion(s2, a2):
        oxys_list.append({
            (u1['line_n'], u1['unit_ord']): s2.text or "",
            (u2['line_n'], u2['unit_ord']): a2.text or ""
        })


def do_barys_double_vs_single(u_double, u_single, barys_list, oxys_list):
    """
    Compare a double (resolution) in strophe vs. a single in antistrophe, or vice versa.
    Typically we compare the double's 2nd sub-syllable with the single's syllable.
    """
    d1 = u_double['syll1']
    d2 = u_double['syll2']
    s_syll = u_single['syll']

    # We'll consider d1 as "previous" for d2. 
    # If you want to find a 'previous' in the single line, you'd do a separate lookup.
    if barys_responsion(d2, s_syll, prev_syll1=d1, prev_syll2=None):
        barys_list.append({
            (u_double['line_n'], u_double['unit_ord']): d2.text or "",
            (u_single['line_n'], u_single['unit_ord']): s_syll.text or ""
        })
    elif oxys_responsion(d2, s_syll):
        oxys_list.append({
            (u_double['line_n'], u_double['unit_ord']): d2.text or "",
            (u_single['line_n'], u_single['unit_ord']): s_syll.text or ""
        })


# ------------------------------------------------------------------------
# 4) PER-LINE FUNCTION
# ------------------------------------------------------------------------
def barys_accentually_responding_syllables_of_line_pair(strophe_line, antistrophe_line):
    """
    Returns [barys_list, oxys_list] if they are metrically responding, else False.

    barys_list, oxys_list are each a list of dicts like:
      [ { (line_n, unit_ord): "text", (line_n, unit_ord): "text" }, ... ]
    """
    # 1) Metrical check
    if not metrically_responding_lines(strophe_line, antistrophe_line):
        return False

    # 2) Build units
    units1 = build_units_for_accent(strophe_line)
    units2 = build_units_for_accent(antistrophe_line)

    if len(units1) != len(units2):
        return False

    # For "previous syllable" lookups
    all_sylls_1 = strophe_line.findall('.//syll')
    all_sylls_2 = antistrophe_line.findall('.//syll')

    # results
    barys_list = []
    oxys_list  = []

    # 3) Compare units by ordinal
    for u1, u2 in zip(units1, units2):
        if u1['unit_ord'] != u2['unit_ord']:
            continue  # or break, depending on your logic

        # single vs single
        if u1['type'] == 'single' and u2['type'] == 'single':
            do_barys_single_vs_single(u1, u2, barys_list, oxys_list, all_sylls_1, all_sylls_2)

        # double vs double
        elif u1['type'] == 'double' and u2['type'] == 'double':
            do_barys_double_vs_double(u1, u2, barys_list, oxys_list)

        # double vs single
        elif u1['type'] == 'double' and u2['type'] == 'single':
            do_barys_double_vs_single(u1, u2, barys_list, oxys_list)

        # single vs double
        elif u1['type'] == 'single' and u2['type'] == 'double':
            do_barys_double_vs_single(u2, u1, barys_list, oxys_list)

    return [barys_list, oxys_list]


# ------------------------------------------------------------------------
# 5) PER-STROPHE FUNCTION
# ------------------------------------------------------------------------
def barys_accentually_responding_syllables_of_strophe_pair(strophe, antistrophe):
    """
    Takes:
      strophe:     <strophe type="strophe"     responsion="XXX">
      antistrophe: <strophe type="antistrophe" responsion="XXX">

    For each matching pair of <l> lines, checks barys/oxys matches.
    Returns [ [barys matches], [oxys matches] ] or False if mismatch.
    """
    # same @responsion?
    if strophe.get('responsion') != antistrophe.get('responsion'):
        return False

    s_lines = strophe.findall('l')
    a_lines = antistrophe.findall('l')

    if len(s_lines) != len(a_lines):
        return False

    combined_barys = []
    combined_oxys  = []

    for s_line, a_line in zip(s_lines, a_lines):
        if not metrically_responding_lines(s_line, a_line):
            print(f"Lines {s_line.get('n')} and {a_line.get('n')} do not metrically respond.")
            return False

        line_barys_oxys = barys_accentually_responding_syllables_of_line_pair(s_line, a_line)
        if line_barys_oxys is False:
            return False

        # line_barys_oxys => [barys_list, oxys_list]
        combined_barys.extend(line_barys_oxys[0])
        combined_oxys.extend(line_barys_oxys[1])

    return [combined_barys, combined_oxys]


# ------------------------------------------------------------------------
# 6) MAIN
# ------------------------------------------------------------------------
if __name__ == "__main__":
    # Example usage with an XML compiled for responsion checks
    tree = etree.parse("responsion_acharnenses_compiled.xml")

    # For instance, pick strophe & antistrophe with responsion="0001"
    strophe = tree.xpath('//strophe[@type="strophe" and @responsion="0001"]')[0]
    antistrophe = tree.xpath('//strophe[@type="antistrophe" and @responsion="0001"]')[0]

    # Get overall barys/oxys matches
    accent_maps = barys_accentually_responding_syllables_of_strophe_pair(strophe, antistrophe)
    if accent_maps is False:
        print("No barys/oxys responsion found or mismatch in lines.")
    else:
        barys_list, oxys_list = accent_maps

        print(f"Barys matches: {len(barys_list)}")
        print(f"Oxys matches:  {len(oxys_list)}\n")

        # Print them more clearly
        if barys_list:
            print("--- BARYS MATCHES ---")
            for i, pair_dict in enumerate(barys_list, start=1):
                print(f"  Pair #{i}:")
                for (line_id, unit_ord), text in pair_dict.items():
                    print(f"    (line {line_id}, ord={unit_ord}) => \"{text}\"")
                print()

        if oxys_list:
            print("--- OXYS MATCHES ---")
            for i, pair_dict in enumerate(oxys_list, start=1):
                print(f"  Pair #{i}:")
                for (line_id, unit_ord), text in pair_dict.items():
                    print(f"    (line {line_id}, ord={unit_ord}) => \"{text}\"")
                print()