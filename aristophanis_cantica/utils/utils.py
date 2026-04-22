'''
I include here some functionality generally useful for the inference scripts and notebooks.
''' 

from collections import Counter
from lxml import etree
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

# all the plays in chronological order
abbreviations = [
    'ach',
    'eq',
    'nu',
    'v',
    'pax',
    'av',
    'lys',
    'th',
    'ra',
    'ec',
    'pl'
]

# Pax is not an abbreviation, so no period
abbreviations_fancy = {
    'ach': 'Ach.',
    'eq': 'Eq.',
    'nu': 'Nu.',
    'v': 'V.',
    'pax': 'Pax',
    'av': 'Av.',
    'lys': 'Lys.',
    'th': 'Th.',
    'ra': 'Ra.',
    'ec': 'Ec.',
    'pl': 'Pl.'
}

def get_cohen_category(r):
    abs_r = abs(r)

    if abs_r >= 0.71:
        return "huge"
    if abs_r >= 0.51:
        return "very large"
    if abs_r >= 0.37:
        return "large"
    if abs_r >= 0.24:
        return "medium"
    if abs_r >= 0.10:
        return "small"
    if abs_r >= 0.005:
        return "very small"
    return "negligible"

polystrophic_cantica = ["ach05", # 4
                        "eq07", # 4
                        "pax01", # 3
                        "lys08", # 4
                        "ra04", # 3
                        "ra08" # 4
]

four_strophe_cantica = [
    "ach05",
    "eq07",
    "lys08",
    "ra08"
]

three_strophe_cantica = [
    "pax01",
    "ra04"
]

def get_canticum_ids(abbreviations):
    all_ids = []
    for abbreviation in abbreviations:
        file_path = ROOT / f'data/compiled/responsion_{abbreviation}_compiled.xml'
        tree = etree.parse(file_path)
        root = tree.getroot()
        strophe_elements = root.xpath("//strophe")
        all_ids.extend(strophe.get("responsion") for strophe in strophe_elements)

    seen = set()
    return [x for x in all_ids if x not in seen and not seen.add(x)]

def get_syll_count(canticum_ids):
    syll_count = {}
    for abbreviation in abbreviations:
        file_path = ROOT / f'data/compiled/responsion_{abbreviation}_compiled.xml'
        tree = etree.parse(file_path)
        root = tree.getroot()
        for strophe in root.xpath("//strophe"):
            responsion_id = strophe.get("responsion")
            if responsion_id in canticum_ids:
                syllables = strophe.xpath(".//syll")
                syll_count[responsion_id] = len(syllables)
    return syll_count

def get_strophicity(abbreviations):
    responsion_counts = Counter()

    for abbreviation in abbreviations:
        file_path = ROOT / f'data/compiled/responsion_{abbreviation}_compiled.xml'
        tree = etree.parse(file_path)
        root = tree.getroot()

        elements = root.xpath("//strophe[@responsion]") + root.xpath("//antistrophe[@responsion]")
        for el in elements:
            rid = el.get("responsion")
            if rid:
                responsion_counts[rid] += 1

    more_than_two = [rid for rid, count in responsion_counts.items() if count > 2]
    exactly_two = [rid for rid, count in responsion_counts.items() if count == 2]

    return more_than_two, exactly_two



