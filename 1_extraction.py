from lxml import etree
import re

# Load and parse the TEI XML file
xml_file = "tlg/tlg0019001.xml"  # Update with your file path
tree = etree.parse(xml_file)

# Remove namespace prefixes directly from parsed XML
for elem in tree.getiterator():
    elem.tag = etree.QName(elem).localname  # Strip namespace prefix

# Update <label> elements to be self-closing with only speaker= attribute
for label in tree.xpath("//label"):
    speaker_text = label.text.strip() if label.text else ""
    label.attrib.clear()  # Remove all existing attributes
    label.set("speaker", speaker_text)  # Add speaker attribute
    label.text = None  # Make the <label> self-closing

# Add or preserve metre="" to all <l> elements
for l in tree.xpath("//body//l"):
    if "metre" not in l.attrib:
        l.set("metre", "")

# Replace &lt; and &gt; within text nodes with <conjecture> tags
def replace_conjecture(text):
    if text:
        text = re.sub(r'&lt;', '<conjecture author="" ref="">', text)
        text = re.sub(r'&gt;', '</conjecture>', text)
    return text

# Apply conjecture replacement to <l> and sub-elements
for element in tree.xpath("//body//l"):
    if element.text:
        element.text = replace_conjecture(element.text)
    for subelem in element:
        if subelem.tail:
            subelem.tail = replace_conjecture(subelem.tail)

# Create the root elements (without namespace prefixes)
output_root = etree.Element("TEI")
text_element = etree.SubElement(output_root, "text")
body_element = etree.SubElement(text_element, "body")

# Create the <chorus> container
chorus_element = etree.SubElement(body_element, "chorus")

# Helper function to check if a line number is in a given range (handles spans)
def is_in_range(line_number, start, end):
    if '-' in line_number:
        n_start, n_end = map(int, line_number.split('-'))
        return (n_start >= start and n_start <= end) or (n_end >= start and n_end <= end)
    else:
        n = int(line_number)
        return start <= n <= end

# Define pairs of strophe-antistrophe ranges
pairs = [
    {"strophe": (204, 218), "antistrophe": (219, 233)},
    {"strophe": (358, 365), "antistrophe": (385, 392)},
    {"strophe": (665, 675), "antistrophe": (692, 702)},
]

responsion_counter = 1
line_counts = {}
mismatch_log = []

# Loop through all <l> elements (now without namespaces)
for pair in pairs:
    # Create strophe and antistrophe containers with dynamic responsion number
    responsion_str = f"{responsion_counter:04d}"
    strophe_element = etree.SubElement(
        chorus_element, "strophe", attrib={
            "type": "strophe",
            "responsion": responsion_str
        }
    )
    strophe_element.text = "\n"

    antistrophe_element = etree.SubElement(
        chorus_element, "strophe", attrib={
            "type": "antistrophe",
            "responsion": responsion_str
        }
    )
    antistrophe_element.text = "\n"

    # Initialize line count for this responsion pair
    line_counts[responsion_str] = {"strophe": 0, "antistrophe": 0}

    # Process lines for the current strophe-antistrophe pair
    for line in tree.xpath("//body//l"):
        line_number = line.get("n")
        if line_number:
            # Strophe processing
            if is_in_range(line_number, *pair["strophe"]):
                if 'rend' in line.attrib:
                    del line.attrib['rend']
                etree.strip_elements(line, "space", with_tail=False)
                strophe_element.append(line)
                line_counts[responsion_str]["strophe"] += 1
            
            # Antistrophe processing
            if is_in_range(line_number, *pair["antistrophe"]):
                if 'rend' in line.attrib:
                    del line.attrib['rend']
                etree.strip_elements(line, "space", with_tail=False)
                antistrophe_element.append(line)
                line_counts[responsion_str]["antistrophe"] += 1

    # Increment responsion for the next pair
    responsion_counter += 1

# Log line count mismatches (but continue processing)
for responsion, counts in line_counts.items():
    if counts["strophe"] != counts["antistrophe"]:
        mismatch_log.append(
            f"Mismatch in line count for responsion {responsion}: "
            f"{counts['strophe']} lines in strophe, "
            f"{counts['antistrophe']} lines in antistrophe."
        )

# Save the new TEI XML to file
output_file = "responsion_acharnenses.xml"
with open(output_file, "wb") as f:
    etree.ElementTree(output_root).write(
        f, encoding="UTF-8", xml_declaration=True, pretty_print=True
    )

# Print mismatches, if any
if mismatch_log:
    print("\nLine count mismatches detected:")
    for mismatch in mismatch_log:
        print(mismatch)
else:
    print("No line count mismatches detected.")

print(f"Updated TEI XML saved to {output_file}")