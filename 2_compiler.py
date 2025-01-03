import re
from lxml import etree

# File paths
input_file = "responsion_acharnenses_scan.xml"
output_file = "responsion_acharnenses_compiled.xml"

# Mapping of brackets to <syll> tags
# Original:
#   [ -> heavy
#   ] -> close heavy
#   { -> light
#   } -> close light
#
# Now including four new entries:
#   [# -> heavy + anceps
#   [% -> heavy + contraction
#   [€ -> heavy + resolution
#   {€ -> light + resolution
# IMPORTANT: Put multi-character keys (e.g. "[#") before single-character keys ("[")
bracket_map = {
    "[#": '<syll weight="heavy" anceps="True">',
    "{#": '<syll weight="light" anceps="True">',
    "[%": '<syll weight="heavy" contraction="True">',
    "{€": '<syll weight="light" resolution="True">',

    "[": '<syll weight="heavy">',
    "]": '</syll>',
    "{": '<syll weight="light">',
    "}": '</syll>'
}

# Read the entire XML file as plain text
with open(input_file, "r", encoding="utf-8") as f:
    xml_content = f.read()


def replace_in_l_elements(xml_text):
    """Replace bracket patterns inside <l> elements only."""
    # Regex to match <l>...</l> blocks
    l_pattern = re.compile(r"(<l[^>]*>)(.*?)(</l>)", re.DOTALL)

    def replace_brackets(match):
        opening, content, closing = match.groups()
        # Perform bracket replacement within <l>
        for key, value in bracket_map.items():
            content = content.replace(key, value)

        # Split each syllable onto a new line
        content = re.sub(r"(</syll>)", r"\1\n", content)
        content = re.sub(r"(<syll weight=\"[^\"]*\">)", r"\n\1", content)

        # Remove extra spaces/line breaks
        content = re.sub(r"\s*\n\s*", "\n", content).strip()

        return f"{opening}\n{content}\n{closing}"

    return l_pattern.sub(replace_brackets, xml_text)


# Process <l> elements
processed_xml = replace_in_l_elements(xml_content)


def prettify(xml_text):
    """Optional: Simple indentation for readability."""
    lines = xml_text.split("\n")
    indent = 0
    prettified_lines = []

    for line in lines:
        stripped = line.strip()

        # Decrease indent for closing tags (except <l>)
        if stripped.startswith("</") and not stripped.startswith("</l"):
            indent -= 1

        prettified_lines.append("  " * max(indent, 0) + stripped)

        # Increase indent for opening tags (except <l> or <syll>)
        if (
            stripped.startswith("<")
            and not stripped.startswith("</")
            and not stripped.endswith("/>")
            and not stripped.startswith("<l")
            and not stripped.startswith("<syll")
        ):
            indent += 1

    return "\n".join(prettified_lines)


# Write out the processed file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(prettify(processed_xml))

print(f"Processed XML saved to {output_file}")