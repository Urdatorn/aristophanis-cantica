from lxml import etree

def metre_strophe(strophe):
    lines = strophe.findall('l')
    result = []
    for line in lines:
        syllables = line.findall('syll')
        line_result = ''.join('-' if syll.get('weight') == 'heavy' else 'u' for syll in syllables)
        result.append(line_result)
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