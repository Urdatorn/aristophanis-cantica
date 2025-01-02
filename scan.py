import re

# File paths
input_file = "responsion_acharnenses_scan.xml"
output_file = "responsion_acharnenses_processed.xml"

# Mapping of brackets to <syll> tags
bracket_map = {
    "[": '<syll weight="heavy">',
    "]": '</syll>',
    "{": '<syll weight="light">',
    "}": '</syll>',
}

# Read the entire XML file as plain text
with open(input_file, "r", encoding="utf-8") as f:
    xml_content = f.read()


# Function to replace bracketed text inside <l> elements
def replace_in_l_elements(xml_text):
    # Regex to match <l>...</l> elements (non-greedy for single <l>)
    l_pattern = re.compile(r"(<l[^>]*>)(.*?)(</l>)", re.DOTALL)

    def replace_brackets(match):
        opening, content, closing = match.groups()
        # Perform bracket replacement within the content of <l>
        for key, value in bracket_map.items():
            content = content.replace(key, value)
        
        # Split into separate <syll> per line
        content = re.sub(r"(</syll>)", r"\1\n", content)
        content = re.sub(r"(<syll weight=\"[^\"]*\">)", r"\n\1", content)

        # Remove trailing/leading spaces and line breaks
        content = re.sub(r"\s*\n\s*", "\n", content).strip()
        
        # Return the modified <l> block
        return f"{opening}\n{content}\n{closing}"

    # Apply bracket replacement only within <l> tags (preserve sibling structure)
    return l_pattern.sub(replace_brackets, xml_text)


# Process <l> elements
processed_xml = replace_in_l_elements(xml_content)


# Prettify (Optional): Clean up indentations for readability
def prettify(xml_text):
    lines = xml_text.split("\n")
    indent = 0
    prettified_lines = []

    for line in lines:
        stripped = line.strip()

        # Reduce indent for closing tags (except <l>)
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


# Save the updated XML to file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(prettify(processed_xml))

print(f"Processed XML saved to {output_file}")