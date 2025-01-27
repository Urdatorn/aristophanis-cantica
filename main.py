#!/usr/bin/env python3

import os
import argparse
from lxml import etree
from stats import (
    accentually_responding_syllables_of_strophe_pair,
    count_all_syllables,
    count_all_accents,
)
from stats_barys import (
    barys_accentually_responding_syllables_of_strophe_pair,
    count_all_barys_oxys,
)

# Ordered list of allowed play infixes
ALLOWED_INFIXES = [
    "ach",
    "eq",
    "nu",
    "v",
    "pax",
    "av",
    "lys",
    "th",
    "ra",
    "ec",
    "pl"
]


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


def print_combined_summary(
    overall_counts,
    total_counts,
    barys_total,
    oxys_total,
    total_syllables,
    responsion_numbers,
    infix_list,
    tree
):
    """
    Prints the combined summary of accentual and barys responsion statistics,
    including the set of plays analyzed in the correct order.
    """
    # Reorder the plays in infix_list according to ALLOWED_INFIXES
    ordered_infix_list = [inf for inf in ALLOWED_INFIXES if inf in infix_list]

    responsion_list = ', '.join(sorted(responsion_numbers))
    infix_list_str = ', '.join(ordered_infix_list)
    total_responsive = sum(overall_counts.values())
    total_all_accents = sum(total_counts.values())
    acute_percent = (overall_counts['acute'] / total_counts['acute'] * 100) if total_counts['acute'] > 0 else 0
    grave_percent = (overall_counts['grave'] / total_counts['grave'] * 100) if total_counts['grave'] > 0 else 0
    circum_percent = (overall_counts['circumflex'] / total_counts['circumflex'] * 100) if total_counts['circumflex'] > 0 else 0
    total_accent_percent = (total_responsive / total_all_accents * 100) if total_all_accents > 0 else 0

    all_barys_oxys = count_all_barys_oxys(tree)
    total_potential_barys = all_barys_oxys['barys']
    total_potential_oxys = all_barys_oxys['oxys']
    total_potential = total_potential_barys + total_potential_oxys

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
    print(f"Analyzed Plays: {infix_list_str}")
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
    parser = argparse.ArgumentParser(description="Analyze responsion statistics from plays.")
    parser.add_argument(
        "args",
        nargs="*",
        help="Play infixes (e.g., 'eq', 'ach') or responsion attributes (e.g., 'v01')."
    )
    args = parser.parse_args()

    total_counts = {"acute": 0, "grave": 0, "circumflex": 0}
    overall_counts = {"acute": 0, "grave": 0, "circumflex": 0}
    total_barys = 0
    total_oxys = 0
    responsion_numbers = set()
    infix_list = []
    total_syllables = 0
    tree = None  # Will reuse/overwrite with each parse

    # If no arguments are provided, try to parse the compiled XMLs for all infixes in ALLOWED_INFIXES:
    if len(args.args) == 0:
        for infix in ALLOWED_INFIXES:
            xml_file = f"responsion_{infix}_compiled.xml"
            if os.path.exists(xml_file):
                infix_list.append(infix)
                tree = etree.parse(xml_file)

                # Collect responsion numbers
                responsion_nums = get_all_responsion_numbers(tree)
                responsion_numbers.update(responsion_nums)

                # Syllable and accent counts
                file_counts = count_all_accents(tree)
                for key in total_counts:
                    total_counts[key] += file_counts[key]

                file_sylls = count_all_syllables(tree)
                total_syllables += file_sylls

                # Accentual responsion details
                file_overall, file_summaries = process_responsions(tree, responsion_nums)
                for key in overall_counts:
                    overall_counts[key] += file_overall[key]

                # Barys/oxys responsion details
                file_barys, file_oxys, file_barys_summaries = process_barys_responsions(tree, responsion_nums)
                total_barys += file_barys
                total_oxys += file_oxys

    else:
        # If arguments are provided, parse them in the order they were given.
        # But still we only end up printing them in the ALLOWED_INFIXES order at summary-time.
        for arg in args.args:
            if arg in ALLOWED_INFIXES:
                # It's a play infix
                if arg not in infix_list:
                    infix_list.append(arg)
                input_file = f"responsion_{arg}_compiled.xml"
                tree = etree.parse(input_file)

                responsion_nums = get_all_responsion_numbers(tree)
                responsion_numbers.update(responsion_nums)

                file_counts = count_all_accents(tree)
                for key in total_counts:
                    total_counts[key] += file_counts[key]

                file_sylls = count_all_syllables(tree)
                total_syllables += file_sylls

                file_overall, file_summaries = process_responsions(tree, responsion_nums)
                for key in overall_counts:
                    overall_counts[key] += file_overall[key]

                file_barys, file_oxys, file_barys_summaries = process_barys_responsions(tree, responsion_nums)
                total_barys += file_barys
                total_oxys += file_oxys

            else:
                # Treat as a responsion ID (e.g., "v01")
                responsion = arg
                infix = arg[:2]  # first two chars to guess the play
                input_file = f"responsion_{infix}_compiled.xml"
                # If that infix is in ALLOWED_INFIXES, add it to infix_list if not present
                if infix in ALLOWED_INFIXES and infix not in infix_list:
                    infix_list.append(infix)

                tree = etree.parse(input_file)
                responsion_numbers.add(responsion)

                file_counts = count_all_accents(tree)
                for key in total_counts:
                    total_counts[key] += file_counts[key]

                file_sylls = count_all_syllables(tree)
                total_syllables += file_sylls

                file_overall, file_summaries = process_responsions(tree, {responsion})
                for key in overall_counts:
                    overall_counts[key] += file_overall[key]

                file_barys, file_oxys, file_barys_summaries = process_barys_responsions(tree, {responsion})
                total_barys += file_barys
                total_oxys += file_oxys

    # Print combined summary if we have at least one file processed.
    if tree is not None:
        print_combined_summary(
            overall_counts,
            total_counts,
            total_barys,
            total_oxys,
            total_syllables,
            responsion_numbers,
            infix_list,
            tree
        )
    else:
        print("No valid XML plays found. Provide arguments or ensure XML files exist in the current directory.")