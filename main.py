import sys
from lxml import etree
from stats import (
    accentually_responding_syllables_of_strophe_pair,
    accents,
    count_all_syllables,
    count_all_accents
)
from stats_barys import barys_accentually_responding_syllables_of_strophe_pair, count_all_barys_oxys
from grc_utils import normalize_word


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


def print_combined_summary(overall_counts, total_counts, barys_total, oxys_total, total_sylls):
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

    print(r"""
                                     _             
 _ __ ___  ___ _ __   ___  _ __  ___(_) ___  _ __  
| '__/ _ \/ __| '_ \ / _ \| '_ \/ __| |/ _ \| '_ \ 
| | |  __/\__ \ |_) | (_) | | | \__ \ | (_) | | | |
|_|  \___||___/ .__/ \___/|_| |_|___/_|\___/|_| |_|
              |_|                                  
    """)
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
    verbose = '-verbose' in sys.argv
    tree = etree.parse("responsion_acharnenses_compiled.xml")

    responsion_numbers = {"0001", "0002", "0003"}

    # Get total possible accent counts and total syllables
    total_counts = count_all_accents(tree)
    total_syllables = count_all_syllables(tree)

    # Process accentual responsions
    overall_counts, responsion_summaries = process_responsions(tree, responsion_numbers)

    # Process barys/oxys responsions
    barys_total, oxys_total, barys_summaries = process_barys_responsions(tree, responsion_numbers)

    # Print combined summary
    print_combined_summary(overall_counts, total_counts, barys_total, oxys_total, total_syllables)

    # Print detailed output for each responsion only if verbose
    if verbose:
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

            print(f"\nResponsion: {responsion} (BARYS/OXYS)")
            print(f"Barys matches: {barys_summaries[responsion]['barys']}")
            print(f"Oxys matches:  {barys_summaries[responsion]['oxys']}")