from lxml import etree
from grc_utils import (
    UPPER_SMOOTH_ACUTE, UPPER_ROUGH_ACUTE, LOWER_ACUTE,
    LOWER_SMOOTH_ACUTE, LOWER_ROUGH_ACUTE, LOWER_DIAERESIS_ACUTE
)

# Define acute accent character set
acute_accents = set(
    UPPER_SMOOTH_ACUTE + UPPER_ROUGH_ACUTE + LOWER_ACUTE
    + LOWER_SMOOTH_ACUTE + LOWER_ROUGH_ACUTE + LOWER_DIAERESIS_ACUTE
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

def count_acutes(text):
    """Counts the number of acute accents in a given string."""
    return sum(1 for char in text if char in acute_accents)

if __name__ == "__main__":
    xml_file = "responsion_ach_compiled.xml"
    responsion_id = "ach01"

    text_content = extract_and_concatenate_strophes(xml_file, responsion_id)
    num_acutes = count_acutes(text_content)

    print(f"Number of acute accents in responsion '{responsion_id}': {num_acutes}")