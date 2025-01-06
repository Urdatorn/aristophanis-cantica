import re

# File paths
input_file = "responsion_acharnenses_scan.xml"
output_file = "responsion_acharnenses_compiled.xml"

# Mapping of brackets to <syll> tags
#
# IMPORTANT: Put multi-character keys (e.g. "[#") before single-character keys ("[")
bracket_map = {
    "[#": '<syll weight="heavy" anceps="True">',
    "{#": '<syll weight="light" anceps="True">',
    "[%": '<syll weight="heavy" contraction="True">',
    "[€": '<syll weight="heavy" contraction="True">',
    "{€": '<syll weight="light" resolution="True">',

    "[": '<syll weight="heavy">',
    "]": '</syll>',
    "{": '<syll weight="light">',
    "}": '</syll>'
}

# Read the entire XML file as plain text
with open(input_file, "r", encoding="utf-8") as f:
    xml_content = f.read()


def compile_scan(xml_text):
    """Compile bracket patterns inside <l> elements into <syll> tags."""
    # Regex to match <l>...</l> blocks
    l_pattern = re.compile(r"(<l[^>]*>)(.*?)(</l>)", re.DOTALL)

    def replace_brackets(match):
        opening, content, closing = match.groups()
        # Perform bracket replacement within <l>
        for key, value in bracket_map.items():
            content = content.replace(key, value)

        return f"{opening}\n{content}\n{closing}"

    return l_pattern.sub(replace_brackets, xml_text)


def apply_brevis_in_longo(xml_text):
    """Add brevis_in_longo attribute to the last light syllable of each <l>."""
    # Regex to find all <l>...</l> blocks
    l_pattern = re.compile(r"(<l[^>]*>)(.*?)(</l>)", re.DOTALL)

    def mark_final_syllable(match):
        opening, content, closing = match.groups()

        # Find all <syll> elements inside <l>
        syll_matches = re.findall(r'<syll[^>]*>', content)

        if syll_matches:
            # Get the last syllable in the line
            last_syll_match = syll_matches[-1]
            
            # Check if it's a light syllable without resolution="True"
            if 'weight="light"' in last_syll_match and 'resolution="True"' not in last_syll_match:
                
                # Insert brevis_in_longo but ensure weight stays first
                updated_syll = re.sub(
                    r'(<syll )',  # Start of the <syll> tag
                    r'\1weight="light" brevis_in_longo="True" ',
                    last_syll_match
                )

                # Replace the last occurrence
                content = content[::-1].replace(last_syll_match[::-1], updated_syll[::-1], 1)[::-1]

        return f"{opening}{content}{closing}"

    return l_pattern.sub(mark_final_syllable, xml_text)


# Step 1: Compile scanned bracket patterns into <syll> tags
processed_xml = compile_scan(xml_content)

# Step 2: Apply brevis_in_longo rule for the final light syllables
processed_xml = apply_brevis_in_longo(processed_xml)


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
    f.write(processed_xml)

print(f"Processed XML saved to {output_file}")