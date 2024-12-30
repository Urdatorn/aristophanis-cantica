from lxml import etree

# Load and parse the TEI XML file
xml_file = "tlg/tlg0019003.xml"  # Update this path if needed
tree = etree.parse(xml_file)

# Define the TEI namespace
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

# Initialize variables
chorus_lines = []
capture = False

# Loop through all <l> elements in the <body>
for line in tree.xpath("//tei:body//tei:l", namespaces=ns):
    # Check if the line has a speaker label "Χο."
    label = line.find("tei:label[@type='speaker']", namespaces=ns)

    if label is not None and label.text.strip() == "Χο.":
        capture = True

    if capture:
        # Collect line text while capturing
        line_text = ''.join(line.itertext()).strip()
        chorus_lines.append(line_text)

    # Stop capturing when a new speaker appears
    next_label = line.find("tei:label[@type='speaker']", namespaces=ns)
    if next_label is not None and next_label.text.strip() != "Χο." and capture:
        capture = False

# Save extracted lines to a text file
output_file = "chorus_lines.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(chorus_lines))

print(f"Saved {len(chorus_lines)} chorus lines to {output_file}")