from lxml import etree
import re

from grc_utils import short_set, syllabifier

irrelevant = r"""[‘’'\u0387\u037e\u00b7.,!?;:"()\[\]\{\}<>\-—…\n«»†×⏑⏓– ]"""

def process_xml(file_path):
    # Parse the XML file
    tree = etree.parse(file_path)
    root = tree.getroot()

    # Find all <l> elements using XPath
    l_elements = root.xpath("//l")

    for l in l_elements:
        # Replace the text content with the syllabified version
        original_text = l.text
        if original_text:
            print(f"Original text: {original_text}")
            syllables = syllabifier(original_text)
            for idx, syllable in enumerate(syllables):

                if re.sub(irrelevant, "", syllable)[-1] in short_set | {"^"}:
                    syllables[idx] = "{" + syllable + "}"
                else:
                    syllables[idx] = "[" + syllable + "]"
            
            syllabified_text = "".join(syllables)
            print(f"Syllabified text: {syllabified_text}")
            
            l.text = syllabified_text

    # Save the modified XML back to a file
    output_path = file_path.replace(".xml", "_modified.xml")
    tree.write(output_path, pretty_print=True, encoding="utf-8", xml_declaration=True)
    print(f"Modified XML saved to {output_path}")

# Example usage
if __name__ == "__main__":
    process_xml("data/scan/responsion_ec_scan.xml")
    print("".join(syllabifier("ἄνοιξον, ἀσπάζου με. ")))