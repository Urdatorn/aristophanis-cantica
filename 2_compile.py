import argparse
import re

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

# Argument parsing
parser = argparse.ArgumentParser(description="Compile a scanned play into <syll> XML.")
parser.add_argument("infix", help="Abbreviation for the play (e.g., 'eq').")
args = parser.parse_args()

# File paths
input_file = f"responsion_{args.infix}_scan.xml"
output_file = f"responsion_{args.infix}_compiled.xml"

# Read the entire XML file as plain text
with open(input_file, "r", encoding="utf-8") as f:
    xml_content = f.read()


def remove_skipped_lines(xml_text):
    """
    Remove <l> elements that contain the attribute skip="True".
    Ensures no blank lines or trailing indentation are left behind.
    """
    def clean_line(match):
        line = match.group(0)
        # Remove the entire line, including preceding and trailing whitespace
        return "" if line.strip() else line

    return re.sub(
        r"^[ \t]*<l[^>]*\bskip=['\"]True['\"][^>]*>.*?</l>[ \t]*\n?",
        clean_line,
        xml_text,
        flags=re.DOTALL | re.MULTILINE,
    )


def remove_skipped_parts(xml_text):
    """
    Remove content enclosed in <skip>...</skip> tags while preserving the rest of the line.
    
    Args:
        xml_text (str): The input XML text.

    Returns:
        str: The XML text with skipped parts removed.
    """
    # Use a regex pattern to match <skip>...</skip> and remove the content
    skip_pattern = re.compile(r"<skip>.*?</skip>", re.DOTALL)

    return skip_pattern.sub("", xml_text)


def compile_scan(xml_text):
    """Compile bracket patterns inside <l> elements into <syll> tags."""
    l_pattern = re.compile(r"(<l[^>]*>)(.*?)(</l>)", re.DOTALL)

    def replace_brackets(match):
        opening, content, closing = match.groups()
        for key, value in bracket_map.items():
            content = content.replace(key, value)
        # Preserve the exact formatting of the content without adding newlines
        return f"{opening}{content}{closing}"

    return l_pattern.sub(replace_brackets, xml_text)


def apply_brevis_in_longo(xml_text):
    """Mark the last light non-resolution <syll> of each <l> with brevis_in_longo='True'."""
    l_pattern = re.compile(r"(<l[^>]*>)(.*?)(</l>)", re.DOTALL)

    def mark_final_syllable(match):
        opening, content, closing = match.groups()

        syll_matches = list(re.finditer(r'<syll[^>]*>', content))

        if syll_matches:
            last_syll_match = syll_matches[-1]
            last_syll = last_syll_match.group()

            if 'weight="light"' in last_syll and 'resolution="True"' not in last_syll:
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

        ordered_attribs = [f'n="{n}"', f'metre="{metre}"'] if n else [f'metre="{metre}"']
        for k, v in attrib_dict.items():
            if k not in special:
                ordered_attribs.append(f'{k}="{v}"')
        for k, v in special.items():
            ordered_attribs.append(f'{k}="{v}"')

        return f'<l {" ".join(ordered_attribs)}>'

    return l_pattern.sub(reorder_attributes, xml_text)


def validator(text):
    """
    Validates the text for misplaced #, € and lonely < or >.

    Args:
        text (str): The input text to validate.

    Raises:
        ValueError: If a misplaced character is found.
    """
    lines = text.splitlines()

    for line_number, line in enumerate(lines, start=1):
        if '#' in line:
            raise ValueError(f"Misplaced # at line {line_number}!")
        if '€' in line:
            raise ValueError(f"Misplaced € at line {line_number}!")

        lt_count = line.count('<')
        gt_count = line.count('>')

        if lt_count > gt_count:
            raise ValueError(f"Lonely < at line {line_number}!")
        elif gt_count > lt_count:
            raise ValueError(f"Lonely > at line {line_number}!")


# Step 1: Remove skipped lines
processed_xml = remove_skipped_lines(xml_content)

# Step 1.5: Remove skipped parts of lines
processed_xml = remove_skipped_parts(processed_xml)

# Step 2: Compile scanned bracket patterns into <syll> tags
processed_xml = compile_scan(processed_xml)

# Step 3: Apply brevis_in_longo rule for the final light syllables
processed_xml = apply_brevis_in_longo(processed_xml)

# Step 4: Reorder <l> attributes to ensure correct order
processed_xml = order_l_attributes(processed_xml)

# Step 5: Validate
validator(processed_xml)

# Step 6: Write the processed file exactly as processed
with open(output_file, "w", encoding="utf-8") as f:
    f.write(processed_xml)

print(f"Processed XML saved to {output_file}")