import re

# File paths
input_file = "responsion_acharnenses_scan.xml"
output_file = "responsion_acharnenses_compiled.xml"

# Mapping of brackets to <syll> tags
bracket_map = {
    "(_": '<macron>',
    "_)": '</macron>',
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
    l_pattern = re.compile(r"(<l[^>]*>)(.*?)(</l>)", re.DOTALL)

    def replace_brackets(match):
        opening, content, closing = match.groups()
        for key, value in bracket_map.items():
            content = content.replace(key, value)
        return f"{opening}\n{content}\n{closing}"

    return l_pattern.sub(replace_brackets, xml_text)


def apply_brevis_in_longo(xml_text):
    """Mark the last light non-resolution <syll> of each <l> with brevis_in_longo='True'."""
    # Regex to match <l>...</l> blocks
    l_pattern = re.compile(r"(<l[^>]*>)(.*?)(</l>)", re.DOTALL)

    def mark_final_syllable(match):
        opening, content, closing = match.groups()

        # Match all <syll> elements
        syll_matches = list(re.finditer(r'<syll[^>]*>', content))

        if syll_matches:
            # Find the last <syll> element
            last_syll_match = syll_matches[-1]
            last_syll = last_syll_match.group()

            # Check if it's light and doesn't have resolution="True"
            if 'weight="light"' in last_syll and 'resolution="True"' not in last_syll:
                # Add the brevis_in_longo="True" attribute
                updated_syll = re.sub(r'(>)', r' brevis_in_longo="True"\1', last_syll, count=1)
                content = content[:last_syll_match.start()] + updated_syll + content[last_syll_match.end():]

        return f"{opening}{content}{closing}"

    return l_pattern.sub(mark_final_syllable, xml_text)


def order_l_attributes(xml_text):
    """Ensure 'n' appears first, 'metre' second, and special attributes last in <l>."""
    l_pattern = re.compile(r'<l([^>]*)>', re.DOTALL)

    def reorder_attributes(match):
        raw_attributes = match.group(1)
        attrib_dict = dict(re.findall(r'(\S+?)="(.*?)"', raw_attributes))

        n = attrib_dict.pop("n", "")
        metre = attrib_dict.pop("metre", "")
        special = {k: v for k, v in attrib_dict.items() if "brevis_in_longo" in k or "resolution" in k}

        # Place n and metre first
        ordered_attribs = [f'n="{n}"', f'metre="{metre}"'] if n else [f'metre="{metre}"']
        # Add other attributes
        for k, v in attrib_dict.items():
            if k not in special:
                ordered_attribs.append(f'{k}="{v}"')
        # Append special attributes last
        for k, v in special.items():
            ordered_attribs.append(f'{k}="{v}"')

        return f'<l {" ".join(ordered_attribs)}>'

    return l_pattern.sub(reorder_attributes, xml_text)


# Step 1: Compile scanned bracket patterns into <syll> tags
processed_xml = compile_scan(xml_content)

# Step 2: Apply brevis_in_longo rule for the final light syllables
processed_xml = apply_brevis_in_longo(processed_xml)

# Step 3: Reorder <l> attributes to ensure correct order
processed_xml = order_l_attributes(processed_xml)


def prettify(xml_text):
    """Proper indentation for all tags, including <l> and <syll>."""
    lines = xml_text.split("\n")
    indent = 0
    prettified_lines = []
    inside_l = False

    for line in lines:
        stripped = line.strip()

        # Decrease indent for closing tags (except <l> and </syll>)
        if stripped.startswith("</") and not stripped.startswith("</l") and not stripped.startswith("</syll>"):
            indent -= 1

        # Handle <l> indentation
        if stripped.startswith("<l"):
            prettified_lines.append("  " * max(indent, 0) + stripped)
            inside_l = True
            continue
        elif stripped.startswith("</l"):
            prettified_lines.append("  " * max(indent, 0) + stripped)
            inside_l = False
            continue

        # Handle <syll> inside <l> indentation
        if inside_l and stripped.startswith("<syll"):
            prettified_lines.append("  " * (indent + 1) + stripped)
            continue

        prettified_lines.append("  " * max(indent, 0) + stripped)

        # Increase indent for opening tags (except <l> and <syll>)
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