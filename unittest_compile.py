import unittest
from lxml import etree
import os
from b_compile import apply_brevis_in_longo

class TestApplyBrevisInLongoWithFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_file = "responsion_nu_compiled.xml"
        if not os.path.exists(cls.input_file):
            raise FileNotFoundError(f"Input file '{cls.input_file}' not found.")
        cls.tree = etree.parse(cls.input_file)

    def test_brevis_in_longo_added_308_309(self):
        """
        Test line 308-309 to ensure the last syllable gets brevis_in_longo
        when metre ends with 'da' and the penultimate syllable is heavy.
        """
        line = self.tree.find(".//l[@n='308-309']")
        input_xml = etree.tostring(line, encoding="unicode")
        processed_xml = apply_brevis_in_longo(input_xml)

        # Ensure brevis_in_longo is added to the last syllable
        self.assertIn('brevis_in_longo="True"', processed_xml)

    def test_no_brevis_in_longo_on_301(self):
        """
        Test line 301 to ensure the last syllable does not get brevis_in_longo
        when metre ends with 'da' and the penultimate syllable is not heavy.
        """
        line = self.tree.find(".//l[@n='301']")
        input_xml = etree.tostring(line, encoding="unicode")
        processed_xml = apply_brevis_in_longo(input_xml)

        # Ensure brevis_in_longo is NOT added
        self.assertNotIn('brevis_in_longo="True"', processed_xml)

        # Ensure the XML structure is intact
        self.assertIn('<syll weight="light">', processed_xml)
        self.assertIn('<syll weight="heavy">', processed_xml)

    def test_no_brevis_in_longo_on_heavy_last_syll(self):
        """
        Test line with only heavy syllables to ensure brevis_in_longo is not added.
        """
        heavy_line = """
        <l n="300" metre="hex"><syll weight="heavy">ἀ</syll><syll weight="heavy">θα</syll><syll weight="heavy">νά</syll></l>
        """
        processed_xml = apply_brevis_in_longo(heavy_line)
        self.assertNotIn('brevis_in_longo="True"', processed_xml)

    def test_brevis_in_longo_light_syll(self):
        """
        Test a synthetic example with a light syllable in a line to ensure brevis_in_longo is added.
        """
        line = """
        <l n="999" metre="4 da"><syll weight="heavy">ἀ</syll><syll weight="light">νά</syll><syll weight="light">θε</syll></l>
        """
        processed_xml = apply_brevis_in_longo(line)
        self.assertIn('brevis_in_longo="True"', processed_xml)

if __name__ == "__main__":
    unittest.main()