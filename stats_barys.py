#!/usr/bin/env python3

"""
stats_barys.py

A variant of stats.py that implements barys/oxys accentual responsion,
and improves readability for barys matches by including the previous syllable's text
if the barys is not purely circumflex-based.
"""

from lxml import etree
from grc_utils import normalize_word

# ------------------------------------------------------------------------
# 1) IMPORT WHAT'S UNCHANGED FROM stats.py
# ------------------------------------------------------------------------
# Adjust these imports based on your actual code organization and exports in stats.py
from stats import (
    canonical_sylls,                # same metrical logic
    metrically_responding_lines,    # same line-to-line matching
    build_units_for_accent,         # same 'unit' building logic
    is_heavy,                       # same helper
    has_acute,                      # same helper
    accents                         # same accent dict
)

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
    Returns True if these two single syllables respond "barys":
      (1) both have circumflex, OR
      (2) both are heavy & each's preceding syllable has an acute, OR
      (3) one has circumflex & the other meets #2
    """
    c1 = has_circumflex(syll1)
    c2 = has_circumflex(syll2)
    h1 = is_heavy(syll1)
    h2 = is_heavy(syll2)

    prev_acute_1 = (prev_syll1 is not None) and has_acute(prev_syll1)
    prev_acute_2 = (prev_syll2 is not None) and has_acute(prev_syll2)

    # (1) both circumflex
    if c1 and c2:
        return True

    # (2) both heavy & each's preceding syll has an acute
    if h1 and h2 and prev_acute_1 and prev_acute_2:
        return True

    # (3) one has circumflex, the other meets #2
    meets_2_for_syll1 = (h1 and prev_acute_1)
    meets_2_for_syll2 = (h2 and prev_acute_2)
    if (c1 and meets_2_for_syll2) or (c2 and meets_2_for_syll1):
        return True

    return False


def oxys_responsion(syll1, syll2):
    """
    Returns True if these two single syllables respond "oxys":
      - both are heavy
      - both have an acute
    """
    return (
        is_heavy(syll1) and
        is_heavy(syll2) and
        has_acute(syll1) and
        has_acute(syll2)
    )

# ------------------------------------------------------------------------
# 3) HELPER FOR PRINTING BARYS TEXT (PREPEND PREV SYLL IF NEEDED)
# ------------------------------------------------------------------------
def get_barys_print_text(curr_syll, prev_syll):
    """
    If curr_syll has a circumflex, we just return its text.
    Otherwise (i.e. if barys is triggered by heavy+prev-acute logic),
    we prepend the previous syllable's text if available.
    """
    if has_circumflex(curr_syll):
        # purely circumflex-based barys
        return curr_syll.text or ""
    else:
        # barys from heavy + acute logic => show previous + current
        if prev_syll is not None:
            return (prev_syll.text or "") + (curr_syll.text or "")
        else:
            return curr_syll.text or ""

# ------------------------------------------------------------------------
# 4) UNIT-BY-UNIT COMPARISONS
# ------------------------------------------------------------------------
def do_barys_single_vs_single(u1, u2, barys_list, oxys_list, all_sylls_1, all_sylls_2):
    """
    Compare strophe single vs antistrophe single for barys or oxys matches.
    If barys => check if it's purely circumflex or not; if not, prepend the previous syllable's text.
    """
    s_syll = u1['syll']
    a_syll = u2['syll']

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

    # Barys check
    if barys_responsion(s_syll, a_syll, prev_s_syll, prev_a_syll):
        strophe_text = get_barys_print_text(s_syll, prev_s_syll)
        anti_text    = get_barys_print_text(a_syll, prev_a_syll)

        barys_list.append({
            (u1['line_n'], u1['unit_ord']): strophe_text,
            (u2['line_n'], u2['unit_ord']): anti_text
        })

    # Oxys check (FIX: we must append to oxys_list here, not barys_list!)
    elif oxys_responsion(s_syll, a_syll):
        oxys_list.append({
            (u1['line_n'], u1['unit_ord']): s_syll.text or "",
            (u2['line_n'], u2['unit_ord']): a_syll.text or ""
        })


def do_barys_double_vs_double(u1, u2, barys_list, oxys_list):
    """
    Compare resolution pair vs resolution pair for barys or oxys.
    We'll specifically check the 2nd sub-syllable in each pair with the 1st as 'prev'.
    """
    s1 = u1['syll1']
    s2 = u1['syll2']
    a1 = u2['syll1']
    a2 = u2['syll2']

    # Attempt barys for (s2,a2) with prev = (s1,a1)
    if barys_responsion(s2, a2, prev_syll1=s1, prev_syll2=a1):
        strophe_text = get_barys_print_text(s2, s1)
        anti_text    = get_barys_print_text(a2, a1)

        barys_list.append({
            (u1['line_n'], u1['unit_ord']): strophe_text,
            (u2['line_n'], u2['unit_ord']): anti_text
        })

    # Oxys check (FIX: again, must append to oxys_list)
    elif oxys_responsion(s2, a2):
        oxys_list.append({
            (u1['line_n'], u1['unit_ord']): s2.text or "",
            (u2['line_n'], u2['unit_ord']): a2.text or ""
        })


def do_barys_double_vs_single(u_double, u_single, barys_list, oxys_list):
    """
    Compare a double in strophe vs a single in antistrophe, or vice versa.
    We'll check the 2nd sub-syllable in the double for barys/oxys.
    """
    d1 = u_double['syll1']
    d2 = u_double['syll2']
    s_syll = u_single['syll']

    # Barys check => (d2, s_syll), with d1 as 'previous' for d2
    if barys_responsion(d2, s_syll, prev_syll1=d1, prev_syll2=None):
        strophe_text = get_barys_print_text(d2, d1)
        anti_text    = s_syll.text or ""  # or find the single's prev if needed

        barys_list.append({
            (u_double['line_n'], u_double['unit_ord']): strophe_text,
            (u_single['line_n'], u_single['unit_ord']): anti_text
        })

    # Oxys check (FIX: must append to oxys_list here)
    elif oxys_responsion(d2, s_syll):
        oxys_list.append({
            (u_double['line_n'], u_double['unit_ord']): d2.text or "",
            (u_single['line_n'], u_single['unit_ord']): s_syll.text or ""
        })

# ------------------------------------------------------------------------
# 5) LINE-PAIR FUNCTION
# ------------------------------------------------------------------------
def barys_accentually_responding_syllables_of_line_pair(strophe_line, antistrophe_line):
    """
    Returns [barys_list, oxys_list] if the lines are metrically responding, else False.
    """
    if not metrically_responding_lines(strophe_line, antistrophe_line):
        return False

    units1 = build_units_for_accent(strophe_line)
    units2 = build_units_for_accent(antistrophe_line)

    if len(units1) != len(units2):
        return False

    all_sylls_1 = strophe_line.findall('.//syll')
    all_sylls_2 = antistrophe_line.findall('.//syll')

    barys_list = []
    oxys_list  = []

    for u1, u2 in zip(units1, units2):
        if u1['unit_ord'] != u2['unit_ord']:
            continue

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
# 6) STROPHE-PAIR FUNCTION
# ------------------------------------------------------------------------
def barys_accentually_responding_syllables_of_strophe_pair(strophe, antistrophe):
    """
    For each matching pair of <l> lines, gather barys/oxys matches.
    Returns [ [barys matches], [oxys matches] ] or False if mismatch.
    """
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

        combined_barys.extend(line_barys_oxys[0])
        combined_oxys.extend(line_barys_oxys[1])

    return [combined_barys, combined_oxys]


# ------------------------------------------------------------------------
# 7) MAIN
# ------------------------------------------------------------------------
if __name__ == "__main__":
    # Example usage:
    tree = etree.parse("responsion_acharnenses_compiled.xml")

    # Suppose we pick the pair with responsion="0001"
    strophe = tree.xpath('//strophe[@type="strophe" and @responsion="0001"]')[0]
    antistrophe = tree.xpath('//strophe[@type="antistrophe" and @responsion="0001"]')[0]

    accent_maps = barys_accentually_responding_syllables_of_strophe_pair(strophe, antistrophe)
    if not accent_maps:
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