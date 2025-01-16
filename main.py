import sys
from lxml import etree
from stats import (
    accentually_responding_syllables_of_strophe_pair,
    accents,
    count_all_syllables,
    count_all_accents,
    count_all_accents_canticum
)
from stats_barys import (
    barys_accentually_responding_syllables_of_strophe_pair, 
    count_all_barys_oxys,
    count_all_barys_oxys_canticum
)
from grc_utils import normalize_word


def get_all_responsion_numbers(tree):
    """
    Extracts all unique responsion numbers from the XML tree.
    """
    responsions = set()
    strophes = tree.xpath('//strophe[@responsion]')
    for strophe in strophes:
        responsions.add(strophe.get('responsion'))
    return responsions


def process_responsions(tree, responsion_numbers):
    overall_counts = {
        'acute': 0,
        'grave': 0,
        'circumflex': 0
    }
    responsion_summaries = {}

    for responsion in responsion_numbers:
        strophes = tree.xpath(f'//strophe[@type="strophe" and @responsion="{responsion}"]')
        antistrophes = tree.xpath(f'//strophe[@type="antistrophe" and @responsion="{responsion}"]')

        if len(strophes) != len(antistrophes):
            print(f"Mismatch in line count for responsion {responsion}: "
                  f"{len(strophes)} strophes, {len(antistrophes)} antistrophes.\n")
            continue

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

        responsion_summaries[responsion] = counts

        overall_counts['acute'] += counts['acute']
        overall_counts['grave'] += counts['grave']
        overall_counts['circumflex'] += counts['circumflex']

    return overall_counts, responsion_summaries


def process_barys_responsions(tree, responsion_numbers):
    barys_total = 0
    oxys_total = 0
    barys_summaries = {}

    for responsion in responsion_numbers:
        strophes = tree.xpath(f'//strophe[@type="strophe" and @responsion="{responsion}"]')
        antistrophes = tree.xpath(f'//strophe[@type="antistrophe" and @responsion="{responsion}"]')

        if len(strophes) != len(antistrophes):
            print(f"Mismatch in line count for responsion {responsion}: "
                  f"{len(strophes)} strophes, {len(antistrophes)} antistrophes.\n")
            continue

        barys_count = 0
        oxys_count = 0

        for strophe, antistrophe in zip(strophes, antistrophes):
            barys_maps = barys_accentually_responding_syllables_of_strophe_pair(strophe, antistrophe)
            if barys_maps:
                barys_count += len(barys_maps[0])
                oxys_count += len(barys_maps[1])

        barys_summaries[responsion] = {
            'barys': barys_count,
            'oxys': oxys_count
        }

        barys_total += barys_count
        oxys_total += oxys_count

    return barys_total, oxys_total, barys_summaries


def print_combined_summary(overall_counts, total_counts, barys_total, oxys_total, total_sylls, responsion_numbers):
    """
    Prints the combined summary of accentual and barys responsion statistics.
    """
    # Format the responsion numbers as a comma-separated string
    responsion_list = ', '.join(sorted(responsion_numbers))

    # Calculate totals
    total_responsive = sum(overall_counts.values())
    total_all_accents = sum(total_counts.values())

    # Calculate percentages for accentual responsion
    acute_percent = (overall_counts['acute'] / total_counts['acute'] * 100) if total_counts['acute'] > 0 else 0
    grave_percent = (overall_counts['grave'] / total_counts['grave'] * 100) if total_counts['grave'] > 0 else 0
    circum_percent = (overall_counts['circumflex'] / total_counts['circumflex'] * 100) if total_counts['circumflex'] > 0 else 0
    total_accent_percent = (total_responsive / total_all_accents * 100) if total_all_accents > 0 else 0

    # Get total potential barys and oxys counts
    all_barys_oxys = count_all_barys_oxys(tree)
    total_potential_barys = all_barys_oxys['barys']
    total_potential_oxys = all_barys_oxys['oxys']
    total_potential = total_potential_barys + total_potential_oxys

    # Calculate percentages for barys/oxys
    barys_percent = (barys_total / total_potential_barys * 100) if total_potential_barys > 0 else 0
    oxys_percent = (oxys_total / total_potential_oxys * 100) if total_potential_oxys > 0 else 0
    total_percent = ((barys_total + oxys_total) / total_potential * 100) if total_potential > 0 else 0

    # Print header and responsion numbers
    print(r"""
                                     _             
 _ __ ___  ___ _ __   ___  _ __  ___(_) ___  _ __  
| '__/ _ \/ __| '_ \ / _ \| '_ \/ __| |/ _ \| '_ \ 
| | |  __/\__ \ |_) | (_) | | | \__ \ | (_) | | | |
|_|  \___||___/ .__/ \___/|_| |_|___/_|\___/|_| |_|
              |_|                                  
    """)
    print(f"Cantica: {responsion_list}\n")

    print("### ACCENTUAL RESPONSION: ###")
    print(f"Acute:      {overall_counts['acute']}/{total_counts['acute']} = {acute_percent:.1f}%")
    print(f"Grave:      {overall_counts['grave']}/{total_counts['grave']} = {grave_percent:.1f}%")
    print(f"Circumflex: {overall_counts['circumflex']}/{total_counts['circumflex']} = {circum_percent:.1f}%")
    print(f"TOTAL: {total_responsive}/{total_all_accents} = {total_accent_percent:.1f}%")
    print("################\n")

    print("### BARYS RESPONSION: ###")
    print(f"Barys matches:      {barys_total}/{total_potential_barys} = {barys_percent:.1f}%")
    print(f"Oxys matches:       {oxys_total}/{total_potential_oxys} = {oxys_percent:.1f}%")
    print(f"TOTAL: {barys_total + oxys_total}/{total_potential} = {total_percent:.1f}%")
    print("################\n")


if __name__ == "__main__":
    # Parse the XML tree
    tree = etree.parse("responsion_acharnenses_compiled.xml")
    
    # Check for verbose flag
    verbose = '-verbose' in sys.argv
    if verbose:
        sys.argv.remove('-verbose')  # Remove the flag to simplify argument parsing

    # Get specific responsion numbers or default to all
    if len(sys.argv) > 1:
        responsion_numbers = set(sys.argv[1:])
    else:
        responsion_numbers = get_all_responsion_numbers(tree)

    # Get total possible accent counts and total syllables
    total_counts = count_all_accents(tree)
    total_syllables = count_all_syllables(tree)

    # Process accentual responsions
    overall_counts, responsion_summaries = process_responsions(tree, responsion_numbers)

    # Process barys/oxys responsions
    barys_total, oxys_total, barys_summaries = process_barys_responsions(tree, responsion_numbers)

    # Print combined summary
    print_combined_summary(overall_counts, total_counts, barys_total, oxys_total, total_syllables, responsion_numbers)

    # Print detailed output for each responsion if verbose
    if verbose:
        # Sort responsion numbers numerically
        sorted_responsion_numbers = sorted(responsion_numbers)

        for responsion in sorted_responsion_numbers:
            if responsion in responsion_summaries:
                counts = responsion_summaries[responsion]
                barys_data = barys_summaries[responsion]

                # Get strophe-specific totals for accents
                canticum_totals = count_all_accents_canticum(tree, responsion)

                # Get strophe-specific totals for barys and oxys
                canticum_barys_oxys = count_all_barys_oxys_canticum(tree, responsion)
                total_canticum_barys = canticum_barys_oxys['barys']
                total_canticum_oxys = canticum_barys_oxys['oxys']
                total_canticum_barys_oxys = total_canticum_barys + total_canticum_oxys

                # Total responsive accents for this canticum
                total_responsive = sum(counts.values())
                total_possible = sum(canticum_totals.values())
                total_accent_percent = (total_responsive / total_possible * 100) if total_possible > 0 else 0

                # Percentages for accents
                acute_percent = (counts['acute'] / canticum_totals['acute'] * 100) if canticum_totals['acute'] > 0 else 0
                grave_percent = (counts['grave'] / canticum_totals['grave'] * 100) if canticum_totals['grave'] > 0 else 0
                circum_percent = (counts['circumflex'] / canticum_totals['circumflex'] * 100) if canticum_totals['circumflex'] > 0 else 0

                # Percentages for barys/oxys
                barys_total = barys_data['barys']
                oxys_total = barys_data['oxys']
                barys_percent = (barys_total / total_canticum_barys * 100) if total_canticum_barys > 0 else 0
                oxys_percent = (oxys_total / total_canticum_oxys * 100) if total_canticum_oxys > 0 else 0
                total_barys_oxys_percent = ((barys_total + oxys_total) / total_canticum_barys_oxys * 100) if total_canticum_barys_oxys > 0 else 0

                # Print verbose details
                print(f"\nCanticum: {responsion}")
                print(f"Acute matches:      {counts['acute']:<5}/{canticum_totals['acute']:<5} = {acute_percent:>6.1f}%")
                print(f"Grave matches:      {counts['grave']:<5}/{canticum_totals['grave']:<5} = {grave_percent:>6.1f}%")
                print(f"Circumflex matches: {counts['circumflex']:<5}/{canticum_totals['circumflex']:<5} = {circum_percent:>6.1f}%")
                print(f"Total:              {total_responsive:<5}/{total_possible:<5} = {total_accent_percent:>6.1f}%")
                print(f"Barys matches:      {barys_total:<5}/{total_canticum_barys:<5} = {barys_percent:>6.1f}%")
                print(f"Oxys matches:       {oxys_total:<5}/{total_canticum_oxys:<5} = {oxys_percent:>6.1f}%")
                print(f"Total:              {barys_total + oxys_total:<5}/{total_canticum_barys_oxys:<5} = {total_barys_oxys_percent:>6.1f}%")