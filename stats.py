from lxml import etree

from grc_utils import normalize_word

from vowels import (
    UPPER_SMOOTH_ACUTE, UPPER_ROUGH_ACUTE, LOWER_ACUTE, LOWER_SMOOTH_ACUTE, LOWER_ROUGH_ACUTE, LOWER_DIAERESIS_ACUTE,
    UPPER_SMOOTH_GRAVE, UPPER_ROUGH_GRAVE, LOWER_GRAVE, LOWER_SMOOTH_GRAVE, LOWER_ROUGH_GRAVE, LOWER_DIAERESIS_GRAVE,
    UPPER_SMOOTH_CIRCUMFLEX, UPPER_ROUGH_CIRCUMFLEX, LOWER_CIRCUMFLEX, LOWER_SMOOTH_CIRCUMFLEX, LOWER_ROUGH_CIRCUMFLEX, LOWER_DIAERESIS_CIRCUMFLEX
)

###############################################################################
# ACCENT CHARACTERS
###############################################################################
accents = {
    'acute': set(
        UPPER_SMOOTH_ACUTE + UPPER_ROUGH_ACUTE + LOWER_ACUTE
        + LOWER_SMOOTH_ACUTE + LOWER_ROUGH_ACUTE + LOWER_DIAERESIS_ACUTE
    ),
    'grave': set(
        UPPER_SMOOTH_GRAVE + UPPER_ROUGH_GRAVE + LOWER_GRAVE
        + LOWER_SMOOTH_GRAVE + LOWER_ROUGH_GRAVE + LOWER_DIAERESIS_GRAVE
    ),
    'circumflex': set(
        UPPER_SMOOTH_CIRCUMFLEX + UPPER_ROUGH_CIRCUMFLEX + LOWER_CIRCUMFLEX
        + LOWER_SMOOTH_CIRCUMFLEX + LOWER_ROUGH_CIRCUMFLEX + LOWER_DIAERESIS_CIRCUMFLEX
    )
}

###############################################################################
# 0) UTILITY FUNCTIONS
###############################################################################


def polystrophic(tree, responsion):
    strophes = tree.xpath(f'//strophe[@responsion="{responsion}"]')
    return len(strophes) > 2


def count_all_syllables(tree):
    """
    Returns the total count of canonical syllables across all lines in the XML tree.
    Uses the canonical_sylls function to process each line according to the special rules
    for resolution, anceps, and brevis in longo.
    
    Parameters:
    tree (etree._ElementTree): The parsed XML tree containing lines of text
    
    Returns:
    int: Total count of canonical syllables
    """
    total_count = 0
    
    # Find all line elements in the tree
    lines = tree.findall('.//l')
    
    # For each line, get its canonical syllables and add their count
    for line in lines:
        syllable_list = canonical_sylls(line)
        total_count += len(syllable_list)
        
    return total_count


def count_all_accents(tree):
    """
    Counts all occurrences of acute, grave, and circumflex accents across all
    strophes and antistrophes in the entire XML tree.
    """
    counts = {
        'acute': 0,
        'grave': 0,
        'circumflex': 0
    }

    all_sylls = tree.xpath('//strophe//syll | //antistrophe//syll')

    for syll in all_sylls:
        text = syll.text or ""
        norm_text = normalize_word(text)

        for accent_type, accent_chars in accents.items():
            if any(char in norm_text for char in accent_chars):
                counts[accent_type] += 1

    return counts


def count_all_accents_canticum(tree, responsion):
    """
    Counts all occurrences of acute, grave, and circumflex accents across
    all strophes and antistrophes in the XML tree for a specific responsion.
    """
    counts = {
        'acute': 0,
        'grave': 0,
        'circumflex': 0
    }

    # XPath to select syllables within strophes and antistrophes for the given responsion
    all_sylls = tree.xpath(f'//strophe[@responsion="{responsion}"]//syll | //antistrophe[@responsion="{responsion}"]//syll')

    for syll in all_sylls:
        text = syll.text or ""
        norm_text = normalize_word(text)

        for accent_type, accent_chars in accents.items():
            if any(char in norm_text for char in accent_chars):
                counts[accent_type] += 1

    return counts


###############################################################################
# 1) METRICAL RESPONSION
###############################################################################


def canonical_sylls(xml_line):
    """
    Transforms a scanned line into an abstract metre representation.

    Returns a list of 'weights' for the line, with the following rules:
      - Contraction: A heavy syllable with contraction="True" counts as two 'light'.
      - Resolution: Two consecutive syllables both with resolution="True" count as one 'heavy'.
      - Anceps: A syllable with anceps="True" becomes 'anceps', ignoring weight.
      - Brevis in longo: A syllable with brevis_in_longo="True" is treated as 'heavy'.
      - Otherwise, use 'heavy' or 'light' from the <syll weight="..."> attribute.
    """
    syllables = xml_line.findall('.//syll')
    result = []
    i = 0

    while i < len(syllables):
        current = syllables[i]
        is_anceps = current.get('anceps') == 'True'
        is_res = current.get('resolution') == 'True'
        is_contraction = current.get('contraction') == 'True'
        is_brevis_in_longo = current.get('brevis_in_longo') == 'True'
        current_weight = current.get('weight', '')

        # (a) Two consecutive resolution => treat as one 'heavy'
        if is_res and (i + 1 < len(syllables)) and (syllables[i + 1].get('resolution') == 'True'):
            result.append('heavy')
            i += 2
            continue

        # (b) If anceps => 'anceps'
        if is_anceps:
            result.append('anceps')
            i += 1
            continue

        # (c) Contraction logic: heavy with contraction="True" => 'light', 'light'
        if is_contraction and current_weight == 'heavy':
            result.extend(['light', 'light'])
            i += 1
            continue

        # (d) brevis_in_longo logic: brevis_in_longo="True" => 'heavy'
        if is_brevis_in_longo:
            result.append('heavy')
            i += 1
            continue

        # (e) Default behavior: use 'weight' if valid, otherwise 'light'
        result.append(current_weight if current_weight in ('heavy', 'light') else 'light')
        i += 1

    return result


def metrically_responding_lines(strophe_line, antistrophe_line):
    """
    Returns True if the two lines share the same 'canonical' sequence of syllables.
    Considers:
      - Consecutive resolution="True" => 'heavy'.
      - 'anceps' matches anything.
      - Light syll with brevis_in_longo="True" is treated as 'heavy'.
    """
    c1 = canonical_sylls(strophe_line)
    c2 = canonical_sylls(antistrophe_line)

    if len(c1) != len(c2):
        return False

    for s1, s2 in zip(c1, c2):
        if s1 == 'anceps' or s2 == 'anceps':
            continue
        if s1 != s2:
            return False

    return True


###############################################################################
# 2) ACCENTUAL RESPONSION
###############################################################################
def build_units_for_accent(line):
    """
    Convert a <l> element into a list of 'units' for accent comparison:
      - single -> {'type': 'single', 'syll': sElem, 'unit_ord': #, 'line_n': line_n}
      - double -> {'type': 'double', 'syll1': s1, 'syll2': s2, 'unit_ord': #, 'line_n': line_n}

    'unit_ord' increments by 1 for each single/double block, so that
    consecutive resolution="True" lights become one 'double' unit.
    """
    sylls = line.findall('.//syll')
    units = []
    i = 0
    line_n = line.get('n') or "???"
    unit_ordinal = 1

    while i < len(sylls):
        s = sylls[i]
        is_res = s.get('resolution') == 'True'

        if is_res and (i + 1 < len(sylls)) and (sylls[i + 1].get('resolution') == 'True'):
            # double unit
            units.append({
                'type': 'double',
                'syll1': sylls[i],
                'syll2': sylls[i + 1],
                'unit_ord': unit_ordinal,
                'line_n': line_n
            })
            i += 2
        else:
            # single
            units.append({
                'type': 'single',
                'syll': s,
                'unit_ord': unit_ordinal,
                'line_n': line_n
            })
            i += 1

        unit_ordinal += 1

    return units


def has_acute(syll):
    """
    Returns True if the given syll element has an acute accent.
    """
    text = syll.text or ""
    norm = normalize_word(text)
    return any(ch in accents['acute'] for ch in norm)


def is_heavy(syll):
    """Helper to check if a single syllable is heavy (per @weight)."""
    return (syll.get('weight') == 'heavy')


def do_single_vs_single(u1, u2, accent_lists):
    """
    Normal single-syllable vs single-syllable check.
    We do check for all accent categories (acute, grave, circumflex).
    """
    s_syll = u1['syll']
    a_syll = u2['syll']
    text_s = s_syll.text or ""
    text_a = a_syll.text or ""
    norm_s = normalize_word(text_s)
    norm_a = normalize_word(text_a)

    for i, (accent_name, accent_chars) in enumerate(accents.items()):
        # If both have *some* char from accent_chars => record a match
        if any(ch in accent_chars for ch in norm_s) and any(ch in accent_chars for ch in norm_a):
            accent_lists[i].append({
                (u1['line_n'], u1['unit_ord']): text_s,
                (u2['line_n'], u2['unit_ord']): text_a
            })


def do_double_vs_double(u1, u2, accent_lists):
    """
    Special resolution vs resolution logic (both are 'double').
    
    The user wants them to match (and only for acutes) if:
      - EITHER both pairs have the acute on their first sub-syllable,
      - OR both pairs have the acute on their second sub-syllable.

    We assume “both sub-syllables cannot have accent at once,” 
    so no need to check the corner case. 
    """
    s1 = u1['syll1']
    s2 = u1['syll2']
    a1 = u2['syll1']
    a2 = u2['syll2']

    strophe_first_acute  = has_acute(s1)
    strophe_second_acute = has_acute(s2)
    anti_first_acute     = has_acute(a1)
    anti_second_acute    = has_acute(a2)

    # Case (a): Both have acute on the first sub-syllable
    if strophe_first_acute and anti_first_acute:
        accent_lists[0].append({
            (u1['line_n'], u1['unit_ord']): s1.text or "",
            (u2['line_n'], u2['unit_ord']): a1.text or ""
        })

    # Case (b): Both have acute on the second sub-syllable
    if strophe_second_acute and anti_second_acute:
        accent_lists[0].append({
            (u1['line_n'], u1['unit_ord']): s2.text or "",
            (u2['line_n'], u2['unit_ord']): a2.text or ""
        })


def do_double_vs_single(u_double, u_single, accent_lists):
    """
    Rule: "They respond if and only if the second syll in the pair 
    has the acute, *and* the single (heavy) has acute."

    So we check:
      1) The single must be 'heavy' 
      2) The double's second sub-syllable must have an acute
      3) The single must have an acute
      4) We record in accent_lists[0] (the 'acute' list)
    """
    d1 = u_double['syll1']
    d2 = u_double['syll2']
    s_syll = u_single['syll']

    if not is_heavy(s_syll):
        return  # no match

    if has_acute(d2) and has_acute(s_syll):
        accent_lists[0].append({
            (u_double['line_n'], u_double['unit_ord']): d2.text or "",
            (u_single['line_n'], u_single['unit_ord']): s_syll.text or ""
        })


def accentually_responding_syllables_of_line_pair(strophe_line, antistrophe_line):
    """
    Returns a triple-list [ [dict, ...], [dict, ...], [dict, ...] ]
    for [acute_matches, grave_matches, circumflex_matches].
    
    If lines are not metrically responding => return False.
    
    We only consider units that share the same ordinal index:
      - single vs single => normal check for all accents
      - double vs double => special rule for acute
      - double vs single => special rule for acute
      - single vs double => same logic, reversed

    """
    if not metrically_responding_lines(strophe_line, antistrophe_line):
        return False

    units1 = build_units_for_accent(strophe_line)
    units2 = build_units_for_accent(antistrophe_line)

    if len(units1) != len(units2):
        return False

    accent_lists = [[], [], []]  # [acutes, graves, circumflexes]

    for u1, u2 in zip(units1, units2):
        # same ordinal check
        if u1['unit_ord'] != u2['unit_ord']:
            continue

        # (A) single vs single
        if u1['type'] == 'single' and u2['type'] == 'single':
            do_single_vs_single(u1, u2, accent_lists)

        # (B) double vs double
        elif u1['type'] == 'double' and u2['type'] == 'double':
            do_double_vs_double(u1, u2, accent_lists)

        # (C) double vs single
        elif u1['type'] == 'double' and u2['type'] == 'single':
            do_double_vs_single(u1, u2, accent_lists)

        # (D) single vs double
        elif u1['type'] == 'single' and u2['type'] == 'double':
            # just reverse the order
            do_double_vs_single(u2, u1, accent_lists)

    return accent_lists


def accentually_responding_syllables_of_strophe_pair(strophe, antistrophe):
    """
    Takes a <strophe type="strophe" responsion="XXXX"> and
    a <strophe type="antistrophe" responsion="XXXX"> with the same @responsion.

    For each pair of lines, checks if they are metrically & accentually responding.
    Accumulates all accent matches (acute, grave, circumflex) in a triple-list:
    
      [
         [ { (s_line, s_ord): '...', (a_line, a_ord): '...' }, ... ],  # acute
         [ ... ],                                                     # grave
         [ ... ]                                                      # circumflex
      ]

    Returns False if mismatch in responsion or line counts.
    """
    if strophe.get('responsion') != antistrophe.get('responsion'):
        return False

    s_lines = strophe.findall('l')
    a_lines = antistrophe.findall('l')
    if len(s_lines) != len(a_lines):
        return False

    combined_accent_lists = [[], [], []]  # [acutes, graves, circumflexes]

    for s_line, a_line in zip(s_lines, a_lines):
        if not metrically_responding_lines(s_line, a_line):
            print(f"Lines {s_line.get('n')} and {a_line.get('n')} do not metrically respond.")
            return False

        line_accent_lists = accentually_responding_syllables_of_line_pair(s_line, a_line)
        if line_accent_lists is False:
            return False

        for i in range(3):
            combined_accent_lists[i].extend(line_accent_lists[i])

    return combined_accent_lists


if __name__ == "__main__":
    tree = etree.parse("responsion_nu_compiled.xml")

    # Specify the responsion numbers to process
    responsion_numbers = {"nu01"}

    # Print ASCII logo at the start
    print(r"""
                                     _             
 _ __ ___  ___ _ __   ___  _ __  ___(_) ___  _ __  
| '__/ _ \/ __| '_ \ / _ \| '_ \/ __| |/ _ \| '_ \ 
| | |  __/\__ \ |_) | (_) | | | \__ \ | (_) | | | |
|_|  \___||___/ .__/ \___/|_| |_|___/_|\___/|_| |_|
              |_|                                  
    """)

    # Initialize counters for overall summary
    overall_counts = {
        'acute': 0,
        'grave': 0,
        'circumflex': 0
    }

    # Store individual responsion results
    responsion_summaries = {}

    # Collect and process all strophes and antistrophes matching the responsion numbers
    for responsion in responsion_numbers:
        strophes = tree.xpath(f'//strophe[@type="strophe" and @responsion="{responsion}"]')
        antistrophes = tree.xpath(f'//strophe[@type="antistrophe" and @responsion="{responsion}"]')

        # Ensure we only process matching pairs
        if len(strophes) != len(antistrophes):
            print(f"Mismatch in line count for responsion {responsion}: "
                  f"{len(strophes)} strophes, {len(antistrophes)} antistrophes.\n")
            continue

        # Initialize responsion-specific counts
        counts = {
            'acute': 0,
            'grave': 0,
            'circumflex': 0
        }

        for strophe, antistrophe in zip(strophes, antistrophes):
            accent_maps = accentually_responding_syllables_of_strophe_pair(strophe, antistrophe)

            if accent_maps:
                counts['acute'] += len(accent_maps[0])
                counts['grave'] += len(accent_maps[1])
                counts['circumflex'] += len(accent_maps[2])

        # Store summary for the current responsion
        responsion_summaries[responsion] = counts

        # Accumulate totals for overall summary
        overall_counts['acute'] += counts['acute']
        overall_counts['grave'] += counts['grave']
        overall_counts['circumflex'] += counts['circumflex']

    # Print summary section
    print("### SUMMARY: ###")
    responsion_range = '-'.join(sorted(responsion_numbers))
    print(f"Responsion: {responsion_range}")
    print(f"Acute matches:      {overall_counts['acute']}")
    print(f"Grave matches:      {overall_counts['grave']}")
    print(f"Circumflex matches: {overall_counts['circumflex']}")
    print("################\n")

    # Proceed with detailed printouts for each responsion (original logic preserved)
    for responsion, counts in responsion_summaries.items():
        strophes = tree.xpath(f'//strophe[@type="strophe" and @responsion="{responsion}"]')
        antistrophes = tree.xpath(f'//strophe[@type="antistrophe" and @responsion="{responsion}"]')

        print(f"\nResponsion: {responsion}")
        print(f"Acute matches:      {counts['acute']}")
        print(f"Grave matches:      {counts['grave']}")
        print(f"Circumflex matches: {counts['circumflex']}")
        print("\nDetailed accent pairs (prettified):\n")

        for strophe, antistrophe in zip(strophes, antistrophes):
            accent_maps = accentually_responding_syllables_of_strophe_pair(strophe, antistrophe)
            
            if accent_maps:
                labels = ["ACUTE", "GRAVE", "CIRCUMFLEX"]
                for i, label in enumerate(labels):
                    print(f"--- {label} MATCHES ({len(accent_maps[i])}) ---")
                    for idx, pair_dict in enumerate(accent_maps[i], start=1):
                        print(f"  Pair #{idx}:")
                        for (line_id, unit_ord), text in pair_dict.items():
                            print(f"    ({line_id}, ordinal={unit_ord}) => \"{text}\"")
                        print()
            else:
                print(f"No accentual responsion found for responsion {responsion}.")