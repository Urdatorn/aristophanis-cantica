#!/usr/bin/env python3

"""
stats_barys.py

This script analyzes **barys/oxys accentual responsion** in **strophic poetry**, specifically in Ancient Greek cantica.
It extends `stats.py` with updated **barys and oxys detection rules** and handles both **single responsion** and **polystrophic responsion**.

------------------------------
## **Logic Flow**
------------------------------

1) **XML Parsing & Data Extraction**
   - Parses a TEI-XML formatted **responsion_ach_compiled.xml**.
   - Extracts **syllables** and their attributes (accent, weight, position).
   - Groups **lines** into **strophes** and **antistrophes** based on responsion structure.

2) **Barys and Oxys Detection**
   - **Barys:** A syllable qualifies if:
     - It has a **circumflex accent**, OR
     - It is **heavy** and its **preceding syllable has an acute**.
   - **Oxys:** Two single syllables respond "oxys" if:
     - Both have an **acute accent**, AND
     - Each is **either the last syllable** in its line OR **followed by a light syllable**.

3) **Line-based Responsion Processing**
   - Checks if **two lines metrically respond**.
   - Extracts **units of accent comparison** (single or resolution-pair).
   - **Matches syllables** between corresponding positions in the two lines.
   - Stores **barys and oxys matches**.

4) **Strophe-based Responsion Processing**
   - Groups **corresponding lines** in **strophe-antistrophe pairs**.
   - Applies line-based responsion logic to **each line pair**.
   - Aggregates **barys and oxys matches** across the strophe.

5) **Polystrophic Responsion Handling**
   - Handles **multiple strophes** in **polystrophic cantica**.
   - Uses **pairwise comparisons** across strophes.
   - Aggregates **only complete n-tuples**, ensuring all strophes participate in each match.

6) **Output Formatting**
   - Prints **total counts** of barys/oxys matches for each canticum.
   - Lists **each match with its exact syllable position and text**.
   - **Polystrophic matches** are formatted separately with **n-tuple alignment**.

"""

import argparse
from lxml import etree

from grc_utils import normalize_word
from stats import (
    polystrophic,
    metrically_responding_lines_polystrophic,
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


def count_all_barys_oxys_canticum(tree, responsion):
    """
    Count all syllables that satisfy barys or oxys criteria for a specific responsion.

    Parameters:
    tree (etree._ElementTree): The parsed XML tree
    responsion (str): The responsion number to filter strophes/antistrophes

    Returns:
    dict: Dictionary with counts of potential 'barys' and 'oxys' syllables
    """
    counts = {
        'barys': 0,
        'oxys': 0
    }

    # Restrict to syllables in the specific responsion
    all_sylls = tree.xpath(f'//strophe[@responsion="{responsion}"]//syll | //antistrophe[@responsion="{responsion}"]//syll')

    for syll in all_sylls:
        # Get the line this syllable belongs to
        line = syll.getparent().getparent()  # syll -> word -> line
        line_sylls = line.findall('.//syll')

        # Find the index of the current syllable in its line
        try:
            syll_index = line_sylls.index(syll)
        except ValueError:
            # Syllable not found in its parent line, skip
            continue

        # Get previous and next syllables in the same line
        prev_syll = line_sylls[syll_index - 1] if syll_index > 0 else None
        next_syll = line_sylls[syll_index + 1] if syll_index + 1 < len(line_sylls) else None

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
# BARYS RESPONSION
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


# ------------------------------------------------------------------------
# OXYS RESPONSION
# ------------------------------------------------------------------------


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
# HELPER FOR PRINTING BARYS / OXYS TEXT
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
# PER-LINE FUNCTION
# ------------------------------------------------------------------------


def barys_accentually_responding_syllables_of_lines(*lines):
    """
    Processes barys and oxys responsion for any number of metrically responding lines.

    Parameters:
    *lines: Variable number of <l> elements (lines).

    Returns:
    list: [barys_list, oxys_list], or False if mismatch.
    """
    if not metrically_responding_lines_polystrophic(*lines):
        print(f"Lines {[line.get('n') for line in lines]} do not metrically respond.")
        return False

    # Build accent units for each line
    all_units = []
    for line in lines:
        line_units = build_units_for_accent(line)
        for unit in line_units:
            unit['line'] = line  # Attach the `line` key
        all_units.append(line_units)

    # Ensure all lines have the same number of units
    unit_counts = [len(units) for units in all_units]
    if len(set(unit_counts)) > 1:
        print(f"Unit count mismatch across lines {[line.get('n') for line in lines]}.")
        return False

    barys_list = []
    oxys_list = []

    # Process units at each index across all lines
    for unit_idx in range(unit_counts[0]):
        units = [units_list[unit_idx] for units_list in all_units]

        # Get full syllable lists for each line
        all_syll_lists = [unit['line'].findall('.//syll') for unit in units]

        # Retrieve syllables, previous syllables, and next syllables
        sylls = [u['syll'] if u['type'] == 'single' else u['syll2'] for u in units]
        prev_sylls = []
        next_sylls = []

        for u, syll_list, syll in zip(units, all_syll_lists, sylls):
            try:
                idx = syll_list.index(syll)
                prev_sylls.append(syll_list[idx - 1] if idx > 0 else None)
                next_sylls.append(syll_list[idx + 1] if idx < len(syll_list) - 1 else None)
            except ValueError:
                prev_sylls.append(None)
                next_sylls.append(None)

        # Check for barys responsion
        if all(barys_responsion(syll, sylls[0], prev_syll, prev_sylls[0]) for syll, prev_syll in zip(sylls, prev_sylls)):
            barys_list.append({
                (u['line_n'], u['unit_ord']): get_barys_print_text(syll, prev_syll)
                for u, syll, prev_syll in zip(units, sylls, prev_sylls)
            })

        # Check for oxys responsion
        if all(oxys_responsion_single_syllables(syll, sylls[0], u['line'].findall('.//syll'), units[0]['line'].findall('.//syll')) for syll, u in zip(sylls, units)):
            oxys_list.append({
                (u['line_n'], u['unit_ord']): get_oxys_print_text(syll, next_syll)
                for u, syll, next_syll in zip(units, sylls, next_sylls)
            })

    return [barys_list, oxys_list]


# ------------------------------------------------------------------------
# PER-STROPHE FUNCTION
# ------------------------------------------------------------------------


def barys_accentually_responding_syllables_of_strophes_polystrophic(*strophes):
    """
    Processes barys and oxys responsion for any number of strophes.

    Parameters:
    *strophes: Variable number of <strophe> elements.

    Returns:
    list: [barys_list, oxys_list], or False if mismatch.
    """
    # Ensure all strophes share the same responsion
    responsions = {strophe.get('responsion') for strophe in strophes}
    if len(responsions) != 1:
        print(f"Strophes have mismatched responsions: {responsions}")
        return False

    # Extract lines from each strophe
    strophe_lines = [strophe.findall('l') for strophe in strophes]

    # Ensure all strophes have the same number of lines
    line_counts = [len(lines) for lines in strophe_lines]
    if len(set(line_counts)) > 1:
        print(f"Line count mismatch across strophes: {line_counts}")
        return False

    combined_barys = []
    combined_oxys = []

    # Process each line group across all strophes
    for line_group in zip(*strophe_lines):  # Transpose the line matrix
        # Evaluate responsion for the current line group
        line_barys_oxys = barys_accentually_responding_syllables_of_lines(*line_group)
        if line_barys_oxys is False:
            print(f"Lines {[line.get('n') for line in line_group]} do not metrically respond.")
            return False

        combined_barys.extend(line_barys_oxys[0])
        combined_oxys.extend(line_barys_oxys[1])

    return [combined_barys, combined_oxys]


# ------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------


if __name__ == "__main__":

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Analyze responsion statistics for a play.")
    parser.add_argument("infix", help="Infix of the play file (e.g., 'ach' for 'responsion_ach_compiled.xml').")
    args = parser.parse_args()

    input_file = f"responsion_{args.infix}_compiled.xml"

    # Parse the XML tree
    tree = etree.parse(input_file)

    # Get all unique responsion numbers
    responsion_numbers = set(
        strophe.get("responsion")
        for strophe in tree.xpath('//strophe[@type="strophe"]')
    )

    # Process each responsion
    for responsion in sorted(responsion_numbers):
        print(f"\nCanticum: {responsion}")

        # Determine if the canticum is polystrophic
        if polystrophic(tree, responsion):
            print("Polystrophic: Yes")

            # Get all strophes for the responsion
            strophes = tree.xpath(f'//strophe[@responsion="{responsion}"]')

            # Use updated polystrophic processing
            barys_oxys_results = barys_accentually_responding_syllables_of_strophes_polystrophic(*strophes)

            if not barys_oxys_results:
                print("No valid barys/oxys matches found.\n")
                continue  # Skip to next responsion if no results

            barys_list, oxys_list = barys_oxys_results

            print(f"Barys matches: {len(barys_list)}")
            print(f"Oxys matches:  {len(oxys_list)}\n")

            # Detailed printing for polystrophic matches
            if barys_list:
                print("--- BARYS MATCHES ---")
                for match_idx, match_set in enumerate(barys_list, start=1):
                    print(f"  Match #{match_idx}:")
                    for (line_id, unit_ord), text in match_set.items():
                        print(f"    (line {line_id}, ord={unit_ord}) => \"{text}\"")
                    print()

            if oxys_list:
                print("--- OXYS MATCHES ---")
                for match_idx, match_set in enumerate(oxys_list, start=1):
                    print(f"  Match #{match_idx}:")
                    for (line_id, unit_ord), text in match_set.items():
                        print(f"    (line {line_id}, ord={unit_ord}) => \"{text}\"")
                    print()

        else:
            print("Polystrophic: No")

            # Get the first strophe and antistrophe for non-polystrophic processing
            strophes = tree.xpath(f'//strophe[@type="strophe" and @responsion="{responsion}"]')
            antistrophes = tree.xpath(f'//strophe[@type="antistrophe" and @responsion="{responsion}"]')

            # Process the first strophe and antistrophe pair
            if strophes and antistrophes:
                barys_oxys_results = barys_accentually_responding_syllables_of_strophes_polystrophic(strophes[0], antistrophes[0])
            else:
                barys_oxys_results = [[], []]  # No valid pairs

            if not barys_oxys_results:
                print("No valid barys/oxys matches found.\n")
                continue  # Skip to next responsion if no results

            barys_list, oxys_list = barys_oxys_results

            print(f"Barys matches: {len(barys_list)}")
            print(f"Oxys matches:  {len(oxys_list)}\n")

            # Detailed printing for non-polystrophic
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