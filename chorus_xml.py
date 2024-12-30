from lxml import etree

# Load and parse the TEI XML file
xml_file = "tlg/tlg0019003.xml"  # Replace with your file path
tree = etree.parse(xml_file)

# Define the TEI namespace
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

# Create a new TEI XML root for the output
output_root = etree.Element("{http://www.tei-c.org/ns/1.0}TEI", nsmap=ns)
text_element = etree.SubElement(output_root, "{http://www.tei-c.org/ns/1.0}text")
body_element = etree.SubElement(text_element, "{http://www.tei-c.org/ns/1.0}body")

# Extract lines spoken by "Χο."
capture = False

# Loop through all <l> elements in the <body>
for line in tree.xpath("//tei:body//tei:l", namespaces=ns):
    # Check if the current line starts a chorus block
    label = line.find("tei:label[@type='speaker']", namespaces=ns)

    if label is not None and label.text.strip() == "Χο.":
        capture = True

    # Stop capturing if a new speaker appears
    if capture:
        # Check if this line is the next speaker's label (after a chorus block)
        next_label = line.find("tei:label[@type='speaker']", namespaces=ns)
        if next_label is not None and next_label.text.strip() != "Χο." and line != label:
            capture = False
            continue  # Do not include this line in the output

        # Remove <tei:space> elements within the line
        etree.strip_elements(line, "{http://www.tei-c.org/ns/1.0}space", with_tail=False)

        # Remove 'rend' attribute from <l> elements
        if 'rend' in line.attrib:
            del line.attrib['rend']

        # Append the cleaned line to the new TEI body
        body_element.append(line)

# Save the corrected TEI XML to a file
output_file = "chorus_lines_cleaned.xml"
etree.ElementTree(output_root).write(
    output_file, encoding="UTF-8", xml_declaration=True, pretty_print=True
)

print(f"Saved cleaned chorus lines to {output_file}")