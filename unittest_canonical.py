import unittest
from lxml import etree

# Import the function to test
from stats import canonical_sylls  # Replace `your_module` with the actual module name


class TestCanonicalSylls(unittest.TestCase):
    def setUp(self):
        """Set up reusable XML snippets for testing."""
        self.parser = etree.XMLParser(remove_blank_text=True)

    def test_contraction_counts_as_two_lights(self):
        xml = """
        <l n="1" metre="D">
          <syll weight="heavy" contraction="True">ἄρ</syll>
          <syll weight="light">τε</syll>
        </l>
        """
        line = etree.fromstring(xml, parser=self.parser)
        self.assertEqual(canonical_sylls(line), ['light', 'light', 'light'])

    def test_resolution_counts_as_one_heavy(self):
        xml = """
        <l n="2" metre="D">
          <syll weight="light" resolution="True">ἀ</syll>
          <syll weight="light" resolution="True">να</syll>
          <syll weight="heavy">γνά</syll>
        </l>
        """
        line = etree.fromstring(xml, parser=self.parser)
        self.assertEqual(canonical_sylls(line), ['heavy', 'heavy'])

    def test_anceps_counts_as_anceps(self):
        xml = """
        <l n="3" metre="D">
          <syll weight="light" anceps="True">τε</syll>
          <syll weight="heavy">ναί</syll>
        </l>
        """
        line = etree.fromstring(xml, parser=self.parser)
        self.assertEqual(canonical_sylls(line), ['anceps', 'heavy'])

    def test_brevis_in_longo_counts_as_heavy(self):
        xml = """
        <l n="4" metre="D">
          <syll weight="light">ἀ</syll>
          <syll weight="light" brevis_in_longo="True">τε</syll>
        </l>
        """
        line = etree.fromstring(xml, parser=self.parser)
        self.assertEqual(canonical_sylls(line), ['light', 'heavy'])

    def test_default_weight_handling(self):
        xml = """
        <l n="5" metre="D">
          <syll>ἀ</syll>
          <syll weight="heavy">νά</syll>
        </l>
        """
        line = etree.fromstring(xml, parser=self.parser)
        self.assertEqual(canonical_sylls(line), ['light', 'heavy'])

    def test_complex_line(self):
        xml = """
        <l n="6" metre="D">
          <syll weight="heavy">ἄρ</syll>
          <syll weight="light" resolution="True">τε</syll>
          <syll weight="light" resolution="True">ναί</syll>
          <syll weight="light" brevis_in_longo="True">γα</syll>
          <syll weight="light" anceps="True">κοί</syll>
          <syll weight="heavy" contraction="True">γνά</syll>
        </l>
        """
        line = etree.fromstring(xml, parser=self.parser)
        self.assertEqual(canonical_sylls(line), [
            'heavy',  # First heavy syllable
            'heavy',  # Resolution pair
            'heavy',  # brevis_in_longo
            'anceps',  # Anceps syllable
            'light', 'light'  # Contraction
        ])

    def test_empty_line(self):
        xml = """
        <l n="7" metre="D">
        </l>
        """
        line = etree.fromstring(xml, parser=self.parser)
        self.assertEqual(canonical_sylls(line), [])

    def test_no_syll_attributes(self):
        xml = """
        <l n="8" metre="D">
          <syll>ἀ</syll>
          <syll>νά</syll>
        </l>
        """
        line = etree.fromstring(xml, parser=self.parser)
        self.assertEqual(canonical_sylls(line), ['light', 'light'])


if __name__ == "__main__":
    unittest.main()