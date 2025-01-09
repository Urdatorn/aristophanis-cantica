#!/usr/bin/env python3

"""
stats_barys.py

A variant of stats.py that implements barys/oxys accentual responsion,
and prints combined text if:
 - barys is from heavy+acute logic (prepend previous syllable),
 - oxys is from the new rule (append next syllable's text).

Updated oxys criteria for single vs single:
   Two single syllables respond "oxys" iff:
    1) both have acute
    2) each is either the last syll in its line OR followed by a light syllable
Weight of the oxys syllable is irrelevant.

Also, for printing we now combine the matched syllable's text with
the NEXT syllable's text if present, e.g. "ἄξ" + "ε" => "ἄξε".
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


def count_all_barys_oxys(tree):
    """
    Count all syllables that satisfy barys or oxys criteria, regardless of matching.
    
    Parameters:
    tree (etree._ElementTree): The parsed XML tree
    
    Returns:
    dict: Dictionary with counts of potential 'barys' and 'oxys' syllables
    """
    counts = {
        'barys': 0,
        'oxys': 0
    }
    
    # Get all syllables
    all_sylls = tree.findall('.//syll')
    
    for i, syll in enumerate(all_sylls):
        # Get the line this syllable belongs to
        line = syll.getparent().getparent()  # syll -> word -> line
        line_sylls = line.findall('.//syll')
        
        # Get previous and next syllables if they exist
        prev_syll = None if i == 0 else all_sylls[i-1]
        
        # Check for barys potential
        is_circumflex = has_circumflex(syll)
        is_heavy_with_prev_acute = (
            is_heavy(syll) and 
            prev_syll is not None and 
            has_acute(prev_syll)
        )
        
        if is_circumflex or is_heavy_with_prev_acute:
            counts['barys'] += 1
            
        # Check for oxys potential
        if has_acute(syll) and next_syll_is_light_or_none(syll, line_sylls):
            counts['oxys'] += 1
    
    return counts


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


##############################################################################
# 2a) OXYS LOGIC: updated criterion
##############################################################################
def next_syll_is_light_or_none(curr_syll, all_sylls):
    """
    Returns True if 'curr_syll' is the last in its line
    OR the next syllable is weight="light".
    """
    try:
        idx = all_sylls.index(curr_syll)
    except ValueError:
        return False

    # If it's the last syllable in the line
    if idx == len(all_sylls) - 1:
        return True

    # Otherwise check if next is light
    nxt = all_sylls[idx + 1]
    return (nxt.get('weight') == 'light')


def oxys_responsion_single_syllables(s_syll, a_syll, all_sylls_1, all_sylls_2):
    """
    Two single syllables respond "oxys" iff each:
      1) has an acute
      2) is last or followed by a light syllable
    """
    if not has_acute(s_syll):
        return False
    if not has_acute(a_syll):
        return False

    if not next_syll_is_light_or_none(s_syll, all_sylls_1):
        return False
    if not next_syll_is_light_or_none(a_syll, all_sylls_2):
        return False

    return True


# ------------------------------------------------------------------------
# 3) HELPER FOR PRINTING BARYS / OXYS TEXT
# ------------------------------------------------------------------------
def get_barys_print_text(curr_syll, prev_syll):
    """
    For barys: if curr_syll has a circumflex, we just return it.
    If barys is from heavy+acute logic => prepend prev_syll's text.
    """
    if has_circumflex(curr_syll):
        return curr_syll.text or ""
    else:
        if prev_syll is not None:
            return (prev_syll.text or "") + (curr_syll.text or "")
        else:
            return curr_syll.text or ""


def get_oxys_print_text(curr_syll, next_syll):
    """
    For oxys: we want to append the next syllable's text if it exists.
    So e.g. "ἄξ" + "ε" => "ἄξε".
    """
    if curr_syll is None:
        return ""

    curr_text = curr_syll.text or ""
    if next_syll is None:
        return curr_text

    next_text = next_syll.text or ""
    return curr_text + next_text

# ------------------------------------------------------------------------
# 4) SINGLE-LINE HELPER FUNCS
# ------------------------------------------------------------------------
def do_barys_single_vs_single(u1, u2, barys_list, oxys_list, all_sylls_1, all_sylls_2):
    """
    Compare strophe single vs antistrophe single for barys or oxys matches.
    If barys => if not purely circumflex, prepend the previous syll text.
    If oxys => if next syll exists, append it.
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

    def get_next(syll, all_sylls):
        try:
            idx = all_sylls.index(syll)
            if idx < len(all_sylls) - 1:
                return all_sylls[idx + 1]
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

    # Oxys check => use updated rule + print next syll text if present
    elif oxys_responsion_single_syllables(s_syll, a_syll, all_sylls_1, all_sylls_2):
        next_s_syll = get_next(s_syll, all_sylls_1)
        next_a_syll = get_next(a_syll, all_sylls_2)

        # build the "expanded" text
        strophe_text = get_oxys_print_text(s_syll, next_s_syll)
        anti_text    = get_oxys_print_text(a_syll, next_a_syll)

        oxys_list.append({
            (u1['line_n'], u1['unit_ord']): strophe_text,
            (u2['line_n'], u2['unit_ord']): anti_text
        })


def do_barys_double_vs_double(u1, u2, barys_list, oxys_list):
    """
    Compare resolution pair vs resolution pair for barys or oxys.
    We'll specifically check the 2nd sub-syllable in each pair with the 1st as 'prev'.

    We do not fully implement the "append next syll text" here, 
    but you can replicate the pattern if you want sub-syllable wise.
    """
    s1 = u1['syll1']
    s2 = u1['syll2']
    a1 = u2['syll1']
    a2 = u2['syll2']

    # Barys
    if barys_responsion(s2, a2, prev_syll1=s1, prev_syll2=a1):
        strophe_text = get_barys_print_text(s2, s1)
        anti_text    = get_barys_print_text(a2, a1)

        barys_list.append({
            (u1['line_n'], u1['unit_ord']): strophe_text,
            (u2['line_n'], u2['unit_ord']): anti_text
        })

    # If you want "oxys" for double sub-syllables, you'd do something similar here:
    # elif <some condition>:
    #    pass


def do_barys_double_vs_single(u_double, u_single, barys_list, oxys_list):
    """
    Compare a double in strophe vs a single in antistrophe, or vice versa.
    We'll check the 2nd sub-syllable in the double for barys/oxys.
    For printing, we haven't added the next-syll logic, but you can adapt similarly if wanted.
    """
    d1 = u_double['syll1']
    d2 = u_double['syll2']
    s_syll = u_single['syll']

    if barys_responsion(d2, s_syll, prev_syll1=d1, prev_syll2=None):
        strophe_text = get_barys_print_text(d2, d1)
        anti_text    = s_syll.text or ""

        barys_list.append({
            (u_double['line_n'], u_double['unit_ord']): strophe_text,
            (u_single['line_n'], u_single['unit_ord']): anti_text
        })

    # For oxys, you can do a partial approach if desired
    # elif <some condition>:
    #     pass


# ------------------------------------------------------------------------
# 5) PER-LINE FUNCTION
# ------------------------------------------------------------------------
def barys_accentually_responding_syllables_of_line_pair(strophe_line, antistrophe_line):
    """
    Returns [barys_list, oxys_list] if they are metrically responding, else False.
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
# 6) PER-STROPHE FUNCTION
# ------------------------------------------------------------------------
def barys_accentually_responding_syllables_of_strophe_pair(strophe, antistrophe):
    """
    For each matching pair of <l> lines, gather barys/oxys matches, 
    returning [ [barys], [oxys] ] or False if mismatch.
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

    # Suppose we pick strophe & antistrophe with responsion="0001"
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