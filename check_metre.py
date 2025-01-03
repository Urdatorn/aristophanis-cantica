from lxml import etree

def metre_strophe(strophe):
    lines = strophe.findall('l')
    result = []

    for line in lines:
        # 1) Recursively gather *all* <syll> elements within <l>, 
        #    including those nested under <conjecture>, <add>, etc.
        syllables = line.findall('.//syll')

        line_pattern = []
        i = 0

        while i < len(syllables):
            syll = syllables[i]

            # (A) anceps="True" => x (ignore weight)
            if syll.get('anceps') == 'True':
                line_pattern.append('x')
                i += 1
                continue

            # (B) resolution="True": check if next also has resolution="True"
            if syll.get('resolution') == 'True':
                # Look ahead
                if i + 1 < len(syllables) and syllables[i + 1].get('resolution') == 'True':
                    # Two consecutive resolution => (uu)
                    line_pattern.append('(uu)')
                    i += 2
                    continue
                else:
                    # Single resolution => 'u'
                    line_pattern.append('u')
                    i += 1
                    continue

            # (C) Normal case => check weight
            weight = syll.get('weight', '')
            if weight == 'heavy':
                line_pattern.append('-')
            else:
                # Default to 'u' for 'light'
                line_pattern.append('u')

            i += 1

        # Join the line pattern for the current line
        result.append(''.join(line_pattern))

    # Return multi-line string: one line of metre per <l>
    return '\n'.join(result)

# Parse the XML file
tree = etree.parse("responsion_acharnenses_processed.xml")

# Find matching strophe/antistrophe with responsion="0001"
strophe = tree.xpath('//strophe[@type="strophe" and @responsion="0001"]')[0]
antistrophe = tree.xpath('//strophe[@type="antistrophe" and @responsion="0001"]')[0]

# Print the metre patterns
print("Strophe Metre Pattern:")
print(metre_strophe(strophe))

print("\nAntistrophe Metre Pattern:")
print(metre_strophe(antistrophe))