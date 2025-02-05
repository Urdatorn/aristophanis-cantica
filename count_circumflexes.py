from lxml import etree
from vowels import (
    UPPER_SMOOTH_CIRCUMFLEX, UPPER_ROUGH_CIRCUMFLEX, LOWER_CIRCUMFLEX,
    LOWER_SMOOTH_CIRCUMFLEX, LOWER_ROUGH_CIRCUMFLEX, LOWER_DIAERESIS_CIRCUMFLEX
)

# Define circumflex accent character set
circumflex_accents = set(
    UPPER_SMOOTH_CIRCUMFLEX + UPPER_ROUGH_CIRCUMFLEX + LOWER_CIRCUMFLEX
    + LOWER_SMOOTH_CIRCUMFLEX + LOWER_ROUGH_CIRCUMFLEX + LOWER_DIAERESIS_CIRCUMFLEX
)

def extract_and_concatenate_strophes(xml_file, responsion_id):
    """Extracts all <strophe> elements with a specific responsion, concatenates their text, and removes line breaks."""
    tree = etree.parse(xml_file)
    strophes = tree.xpath(f'//strophe[@responsion="{responsion_id}"]')

    concatenated_text = ""
    
    for strophe in strophes:
        for syll in strophe.xpath('.//syll'):
            text = (syll.text or "").strip()  # Normalize whitespace
            concatenated_text += text  # Concatenate all syllable texts

    return concatenated_text.replace("\n", "")  # Remove line breaks

def count_circumflexes(text):
    """Counts the number of circumflex accents in a given string."""
    return sum(1 for char in text if char in circumflex_accents)

if __name__ == "__main__":
    xml_file = "responsion_ach_compiled.xml"
    responsion_id = "ach01"

    text_content = extract_and_concatenate_strophes(xml_file, responsion_id)
    num_circumflexes = count_circumflexes(text_content)

    print(f"Number of circumflex accents in responsion '{responsion_id}': {num_circumflexes}")