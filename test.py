from lxml import etree
from stats_barys import barys_accentually_responding_syllables_of_polystrophic_canticum

tree = etree.parse("responsion_acharnenses_compiled.xml")
strophes = tree.xpath(f'//strophe[@responsion="0005"]')

print(barys_accentually_responding_syllables_of_polystrophic_canticum(strophes))
