from lxml import etree
import re

################
### SETTINGS ###
################

cantica = [
    [(284, 301), (335, 346)],  # Strophe + 1 Antistrophe
    [(358, 365), (385, 392)],  # Strophe + 1 Antistrophe
    [(665, 675), (692, 702)],  # Strophe + 1 Antistrophe
    [(836, 841), (842, 847), (848, 853), (854, 859)]  # Strophe + 3 Antistrophes
]

responsion_counter = 2

xml_file = "tlg/tlg0019001.xml"
output_file = "responsion_acharnenses_raw.xml"

################
################
################

tree = etree.parse(xml_file)

# 1) Remove namespace prefixes directly from parsed XML
for elem in tree.getiterator():
    elem.tag = etree.QName(elem).localname  # Strip namespace prefix

# 2) Remove all <pb/> and <lb/> elements
for pb in tree.xpath("//pb"):
    pb.getparent().remove(pb)
for lb in tree.xpath("//lb"):
    lb.getparent().remove(lb)

# -----------------------------------------------------------------------------
# 3) Remove <label type="speaker" ...> from within <l>; 
#    if label text is not "Str." or "Ant.", set speaker= on <l>.
# -----------------------------------------------------------------------------
for line_el in tree.xpath("//body//l"):
    labels = line_el.xpath("./label[@type='speaker']")
    for label_el in labels:
        label_text = (label_el.text or "").strip()
        # If label text is neither "Str." nor "Ant.", add speaker= to <l>
        if label_text and label_text not in ["Str.", "Ant."]:
            if "speaker" not in line_el.attrib:
                line_el.set("speaker", label_text)
        # Remove the label element either way
        line_el.remove(label_el)

# -----------------------------------------------------------------------------
# 4) Update any remaining <label> elements (those not inside <l> or 
#    not type="speaker" or unmatched) to be self-closing with speaker= attribute
# -----------------------------------------------------------------------------
for label in tree.xpath("//label"):
    speaker_text = (label.text or "").strip()
    label.attrib.clear()  # Remove all existing attributes
    label.set("speaker", speaker_text)  # Add speaker attribute
    label.text = None  # Make the <label> self-closing

# 5) Add or preserve metre="" to all <l> elements
for l in tree.xpath("//body//l"):
    if "metre" not in l.attrib:
        l.set("metre", "")

# 6) Replace &lt; and &gt; within text nodes with <conjecture> tags
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

# 7) Create the root elements (without namespace prefixes)
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

line_counts = {}
mismatch_log = []

# 8) Build strophe + multiple antistrophes for each canticum
for canticum in cantica:
    # Create strophe/antistrophe containers with dynamic responsion number
    responsion_str = f"{responsion_counter:04d}"

    # (A) Extract the strophe and antistrophes from the list
    strophe_range = canticum[0]  # The first entry is always the strophe
    antistrophes = canticum[1:]  # Remaining entries are the antistrophes

    # (B) Create the strophe element
    strophe_element = etree.SubElement(
        chorus_element, "strophe",
        attrib={"type": "strophe", "responsion": responsion_str}
    )
    strophe_element.text = "\n"

    # (C) We'll also create placeholders for line counts
    line_counts[responsion_str] = {"strophe": 0, "antistrophes": []}

    # 8.1) Populate the strophe lines
    for line in tree.xpath("//body//l"):
        line_number = line.get("n")
        if line_number and is_in_range(line_number, strophe_range[0], strophe_range[1]):
            if 'rend' in line.attrib:
                del line.attrib['rend']
            etree.strip_elements(line, "space", with_tail=False)
            strophe_element.append(line)
            line_counts[responsion_str]["strophe"] += 1

    # 8.2) For each antistrophe range, build <strophe type="antistrophe">
    for anti_range in antistrophes:
        anti_element = etree.SubElement(
            chorus_element, "strophe",
            attrib={"type": "antistrophe", "responsion": responsion_str}
        )
        anti_element.text = "\n"
        # We'll track line count
        line_count_for_this_antistroph = 0

        # Populate this antistrophe
        for line in tree.xpath("//body//l"):
            line_number = line.get("n")
            if line_number and is_in_range(line_number, anti_range[0], anti_range[1]):
                if 'rend' in line.attrib:
                    del line.attrib['rend']
                etree.strip_elements(line, "space", with_tail=False)
                anti_element.append(line)
                line_count_for_this_antistroph += 1

        line_counts[responsion_str]["antistrophes"].append(line_count_for_this_antistroph)

    # Increment responsion for the next canticum
    responsion_counter += 1

# 9) Compare line counts of strophe vs. antistrophes
for responsion, counts in line_counts.items():
    strophe_count = counts["strophe"]
    antistro_count_list = counts["antistrophes"]
    for idx, a_count in enumerate(antistro_count_list, start=1):
        if a_count != strophe_count:
            mismatch_log.append(
                f"Mismatch for responsion={responsion}, "
                f"antistrophe #{idx} (lines={a_count}), strophe lines={strophe_count}"
            )

# 10) Save the new TEI XML to file
with open(output_file, "wb") as f:
    etree.ElementTree(output_root).write(
        f, encoding="UTF-8", xml_declaration=True, pretty_print=True
    )

# 11) Print mismatches, if any
if mismatch_log:
    print("\nLine count mismatches detected:")
    for mismatch in mismatch_log:
        print(mismatch)
else:
    print("No line count mismatches detected.")

print(f"Updated TEI XML saved to {output_file}")