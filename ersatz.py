# -*- coding: utf-8 -*-
'''
Ports of contour compatibility logic from Anna Conser's Greek-Poetry project, esp. methods from the syllable and stanza classes.
The port includes:
    - class-based logic to functional 
    - machine scanned source to manually scanned sources
    - support for polystrophic songs

@author: Albin Thörn Cleland, Lunds universitet, albin.thorn_cleland@klass.lu.se
@license: MIT
'''

import xml.etree.ElementTree as ET
from lxml import etree
import re

from visualize import restore_text
from vowels import vowel
from clitics import is_enclitic, is_proclitic
from stats import accents, metrically_responding_lines_polystrophic


###############################################################################
# 1) AUX
###############################################################################


line = '<l n="204" metre="4 tr^" speaker="ΧΟ."><syll weight="heavy">Τῇ</syll><syll weight="light">δε</syll> <syll weight="heavy">πᾶ</syll><syll weight="light" anceps="True">ς ἕ</syll><syll weight="heavy">που</syll>, <syll weight="light">δί</syll><syll weight="heavy">ω</syll><syll weight="light" anceps="True">κε</syll> <syll weight="heavy">καὶ</syll> <syll weight="light">τὸ</syll><syll weight="heavy">ν ἄν</syll><syll weight="light" anceps="True">δρα</syll> <syll weight="heavy">πυν</syll><syll weight="light">θά</syll><syll weight="heavy">νου</syll> </l>'
antistrophe = '''<l n="219" metre="4 tr^"><syll weight="heavy">Νῦν</syll> <syll weight="light">δ' ἐ</syll><syll weight="heavy">πει</syll><syll weight="heavy" anceps="True">δὴ</syll> <syll weight="heavy">στερ</syll><syll weight="light">ρὸ</syll><syll weight="heavy">ν ἤ</syll><syll weight="heavy" anceps="True">δη</syll> <syll weight="heavy">τοὐ</syll><syll weight="light">μὸ</syll><syll weight="heavy">ν ἀν</syll><syll weight="heavy" anceps="True">τικ</syll><syll weight="heavy">νή</syll><syll weight="light">μι</syll><syll weight="heavy">ον</syll> </l>'''
root = ET.fromstring(line)


def space_before(syll):
    """Returns True if there is a space before the first vowel in the syllable's text."""
    text = syll.text if syll.text else ""
    for i, char in enumerate(text):
        if vowel(char):  # Find the first vowel
            return i > 0 and text[i - 1] == " "
    return False


def space_after(syll):
    """Returns True if there is a space after the last vowel in the syllable's text."""
    text = syll.text if syll.text else ""
    last_vowel_index = -1

    for i, char in enumerate(text):
        if vowel(char):
            last_vowel_index = i  # Keep track of the last vowel position

    return last_vowel_index != -1 and last_vowel_index < len(text) - 1 and text[last_vowel_index + 1] == " "


def all_accents_line(xml_line):
    """
    Iterates through an <l> of <syll> elements and creates a list of accents.
    """
    accents_line = []
    for i, s in enumerate(xml_line):
        if not s.text:
            accents_line.append(None)
            continue
        if any(ch in accents['acute'] for ch in s.text):
            accents_line.append('A')
        if any(ch in accents['circumflex'] for ch in s.text):
            accents_line.append('C')
        if any(ch in accents['grave'] for ch in s.text):
            accents_line.append('G')
        else:
            accents_line.append(None)
    return accents_line

#print(f'{len(all_accents_line(root))} ACCENTS: {all_accents_line(root)}') 

def all_accents_line_polystrophic(*xml_lines):
    """
    Takes multiple <l> elements and returns a list of accent lists, one for each line.
    """
    return [all_accents_line(line) for line in xml_lines]


def all_accents_at_position(*xml_lines):
    """
    Takes multiple XML <l> elements, applies all_accents_line to each, and returns
    lists where each inner list contains the accents for a given syllabic position
    across all lines, while merging resolved syllables.
    """
    if not metrically_responding_lines_polystrophic(*xml_lines):
        raise ValueError("Lines do not metrically respond.")

    # Get accents for each line
    accents_per_line = [all_accents_line(line) for line in xml_lines]
    
    # Get syllables with resolution merging
    merged_syllables_per_line = []
    for line in xml_lines:
        syllables = [child for child in line if child.tag == "syll"]
        merged_syllables = []
        i = 0
        while i < len(syllables):
            current = syllables[i]
            is_res = current.get("resolution") == "True"

            if is_res and i + 1 < len(syllables) and syllables[i + 1].get("resolution") == "True":
                # Merge two consecutive resolved syllables into a sublist
                merged_syllables.append([current, syllables[i + 1]])
                i += 2
            else:
                merged_syllables.append(current)
                i += 1
        merged_syllables_per_line.append(merged_syllables)

    # Verify equal lengths after merging
    num_positions = len(merged_syllables_per_line[0])
    if any(len(ms) != num_positions for ms in merged_syllables_per_line):
        raise ValueError("Mismatch in syllable counts across lines after merging resolution.")

    # Group accents by position
    grouped_accents = list(map(list, zip(*accents_per_line)))

    return grouped_accents


###############################################################################
# 2) WORD BREAK ANALYSIS
###############################################################################


def get_words_xml(l_element):
    '''
    Doesn't support resolution yet
    '''
    words = []
    current_word = []

    syllables = [child for child in l_element if child.tag == "syll"]
    for syll in syllables:
        print(f'Syllables: |{ET.tostring(syll, encoding="unicode", method="xml")}|')

    for i, syll in enumerate(syllables):
        syll_xml = ET.tostring(syll, encoding='unicode', method='xml')
        current_word.append(syll_xml)
        next_syll = syllables[i + 1] if i + 1 < len(syllables) else None

        if space_after(syll):
            print()
            print(f'SPACE AFTER CASE: |{syll}|')
            words.append("".join(current_word))  # Store current word
            current_word = []  # Start a new word
        elif syll.tail and " " in syll.tail:
            print()
            print(f'TAIL CASE: |{syll.tail}|')
            words.append("".join(current_word))
            current_word = []
        elif next_syll is not None and space_before(next_syll):
            print()
            print(f'SPACE BEFORE NEXT CASE: |{next_syll}|')
            words.append("".join(current_word))
            current_word = []

    if current_word:
        words.append("".join(current_word))

    cleaned_words = []
    for word in words:
        root = ET.fromstring(f"<wrapper>{word}</wrapper>")
        for syll in root.iter("syll"):  
            syll.tail = None

        cleaned_words.append("".join(ET.tostring(syll, encoding="unicode", method="xml") for syll in root))
    words = cleaned_words

    return words


test_line = '<l n="204" metre="4 tr^" speaker="ΧΟ."><syll weight="heavy">Τῇ</syll><syll weight="light">δε</syll> <syll weight="heavy">πᾶ</syll><syll weight="light" anceps="True">ς ἕ</syll><syll weight="heavy">που</syll>, </l>'
root = etree.fromstring(test_line)
words_xml = get_words_xml(root)
print(f'WORDS: {words_xml}')  #
if words_xml == ['<syll weight="heavy">Τῇ</syll><syll weight="light">δε</syll>', '<syll weight="heavy">πᾶ</syll>', '<syll weight="light" anceps="True">ς ἕ</syll><syll weight="heavy">που</syll>']:
    print('PASS')
else:
    print('FAIL')


###############################################################################
# 3) SINGLE LINE CONTOUR ANALYSIS
###############################################################################


def get_contours_line(l_element):
        """
        Adapted from a method in class_stanza
        Iterates through an <l> of <syll> elements and creates a list of melodic contours.

        Note that 'N' is a contour that will not contradict any following contour. 
        It's a feature and not a bug that e.g. a circumflex at wordend will have 'N' contour.
        """

        contours = []
        pre_accent = True
        last_contour = ''

        syllables = [child for child in l_element if child.tag == "syll"]
        for i, s in enumerate(syllables):
            contour = ''
            next_syll = syllables[i + 1] if i + 1 < len(syllables) else None
            word_end = space_after(s) or (s.tail and " " in s.tail) or (next_syll is not None and space_before(next_syll))

            # Check for word-end in middle of resolved syllable [CHECK]
            is_res = s.get('resolution') == 'True'
            if is_res and word_end: # jag tror detta fångar den ursprungliga logiken
                pre_accent = True
            
            # Check for ENCLITICS (excluding τοῦ), and correct previous syllable [CHECK]
            if s.text and is_enclitic(s.text) and not is_proclitic(s.text):
                if contours and contours[-1] == 'N':
                    contours[-1] = last_contour
                    pre_accent = False

            # MAIN ACCENT followed by characteristic fall [CHECK]
            if s.text and any(ch in accents['acute'] or ch in accents['circumflex'] for ch in s.text):
                if any(ch in accents['circumflex'] for ch in s.text):
                    print(f'CIRCUMFLEX: {s.text}')
                if pre_accent:
                    contour = 'DN-A'
                    pre_accent = False
                else:  # unless a second accent caused by an enclitic
                    contour = 'DN'
            # BEFORE ACCENT, the melody rises
            elif pre_accent:
                contour = 'UP'
            # AFTER ACCENT, the melody falls
            elif not pre_accent:
                contour = 'DN'

            # WORD END can be followed by any note [CHECK]
            if word_end:
                last_contour = contour  # copy contour in case of subsequent enclitic
                contour = 'N'
                pre_accent = True

            # Except PROCLITICS and GRAVES followed by a very small rise or a repetition
            if (s.text and is_proclitic(s.text)) or any(ch in accents['grave'] for ch in s.text):
                contour = 'UP-G'

            contours.append(contour)

        return contours


the_text = restore_text(root)
contours = get_contours_line(root)

arrow_dict = {        
                      'N'     : 'x',
                      '='     : '=',
                      '=-A'   : '≠',
                      'UP-G'  : '≤',
                      'UP'    : '↗',
                      'DN-A'  : '⇘',
                      'DN'    : '↘',
                      'CIRC-DN': '★↘',
                      'CIRC-X' : '★x',
                     }

arrows = [arrow_dict[contour] for contour in contours]
#print(f'{the_text} => {contours} => {arrows}')


###############################################################################
# 4) POLYSTROPHIC LINE CONTOURS COMPARISON
###############################################################################


def all_contours_line(*xml_lines):
    """
    Intermediary between get_contours(l_element) and contour().

    Takes multiple XML <l> elements, applies get_contours to each, and returns
    lists where each inner list contains the contours for a given syllabic position
    across all lines, while merging resolved syllables.

    - Ensures all input lines metrically respond.
    - Merges two <syll> elements with resolution="True" into a sublist.
    
    Example:
        all_contours(line1, line2, line3) 
        returns [
            [contour1_line1, contour1_line2, contour1_line3],
            [contour2_line1, contour2_line2, contour2_line3],
            ...
        ]
    """

    if not metrically_responding_lines_polystrophic(*xml_lines):
        raise ValueError("Lines do not metrically respond.")

    contours_per_line = [get_contours_line(line) for line in xml_lines]

    merged_syllables_per_line = []
    for line in xml_lines:
        syllables = [child for child in line if child.tag == "syll"]
        merged_syllables = []
        i = 0
        while i < len(syllables):
            current = syllables[i]
            is_res = current.get("resolution") == "True"

            if is_res and i + 1 < len(syllables) and syllables[i + 1].get("resolution") == "True":
                # Merge two consecutive resolved syllables into a sublist
                merged_syllables.append([current, syllables[i + 1]])
                i += 2  # Skip next syllable
            else:
                merged_syllables.append(current)
                i += 1

        merged_syllables_per_line.append(merged_syllables)

    # Ensure all lines have the same number of syllables after merging resolution
    num_syllables = len(merged_syllables_per_line[0])
    if any(len(ms) != num_syllables for ms in merged_syllables_per_line):
        raise ValueError("Mismatch in syllable counts across lines after merging resolution.")

    # Transpose the lists: group contours by syllable position
    grouped_contours = list(map(list, zip(*contours_per_line)))

    return grouped_contours


def contour_syll(all_contours_at_position: list, all_accents_at_position: list) -> str:
    '''
    Polystrophic adaptation of a method in Conser's class_syllable.

    Comparing the contours of a certain position in an arbitrarily polystrophic canticum.
    '''
    combined = ''
    if all(accent == 'C' for accent in all_accents_at_position): # CASE 1
    #if all(a == 'C' for a in self.all_accents) or (
    #        'C' in self.all_accents and self.prosody in ['⏕', '⏔']):
    
            # In order to make this work, I need to limit to resolutions 
            # with accent on first syllable.
    
        if 'DN-A' in all_contours_at_position:
            combined = 'CIRC-DN'
        else:
            combined = 'CIRC-X'
    elif 'DN-A' in all_contours_at_position: # CASE 2
        if all(contour == 'DN-A' for contour in all_contours_at_position):
            combined = 'DN-A'
        elif {'UP-G', 'UP'} & set(all_contours_at_position):
            combined = '=-A'
        else:
            combined = 'DN'
    elif 'DN' in all_contours_at_position: # CASE 3
        if {'UP-G', 'UP'} & set(all_contours_at_position):
            combined = '='
        else:
            combined = 'DN'
    elif 'UP-G' in all_contours_at_position: # CASE 4
        combined = 'UP-G'
    elif 'UP' in all_contours_at_position: # CASE 5
        combined = 'UP'
    else:
        combined = 'N'
    
    return combined


def contour_line(*xml_lines):
    '''
    Polystrophic adaptation of a method in Conser's class_syllable (here for a whole line instead of one syllable).

    Comparing the contours of a certain position in an arbitrarily polystrophic canticum.
    '''
    grouped_contours = all_contours_line(*xml_lines)
    grouped_accents = all_accents_at_position(*xml_lines)

    combined_contours = []

    for contours, accents in zip(grouped_contours, grouped_accents):
        combined = contour_syll(contours, accents)
        combined_contours.append(combined)

    return combined_contours
        


strophe = '<l n="204" metre="4 tr^" speaker="ΧΟ."><syll weight="heavy">Τῇ</syll><syll weight="light">δε</syll> <syll weight="heavy">πᾶ</syll><syll weight="light" anceps="True">ς ἕ</syll><syll weight="heavy">που</syll>, <syll weight="light">δί</syll><syll weight="heavy">ω</syll><syll weight="light" anceps="True">κε</syll> <syll weight="heavy">καὶ</syll> <syll weight="light">τὸ</syll><syll weight="heavy">ν ἄν</syll><syll weight="light" anceps="True">δρα</syll> <syll weight="heavy">πυν</syll><syll weight="light">θά</syll><syll weight="heavy">νου</syll> </l>'
antistrophe = '''<l n="219" metre="4 tr^"><syll weight="heavy">Νῦν</syll> <syll weight="light">δ' ἐ</syll><syll weight="heavy">πει</syll><syll weight="heavy" anceps="True">δὴ</syll> <syll weight="heavy">στερ</syll><syll weight="light">ρὸ</syll><syll weight="heavy">ν ἤ</syll><syll weight="heavy" anceps="True">δη</syll> <syll weight="heavy">τοὐ</syll><syll weight="light">μὸ</syll><syll weight="heavy">ν ἀν</syll><syll weight="heavy" anceps="True">τικ</syll><syll weight="heavy">νή</syll><syll weight="light">μι</syll><syll weight="heavy">ον</syll> </l>'''
root_strophe = ET.fromstring(line)
root_antistrophe = ET.fromstring(antistrophe)
grouped_contours = all_contours_line(root_strophe, root_antistrophe)
print()
print(f'GROUPED CONTOURS:') 
print() 
print(f'{grouped_contours}')
for i, contours in enumerate(grouped_contours):
    print(f'{i + 1}: {contours}')

combined_contours = contour_line(root_strophe, root_antistrophe)
print()
print(f'COMBINED CONTOURS:')
print()
for i, contour in enumerate(combined_contours):
    print(f'{i + 1}: {contour}')


###############################################################################
# 5) THE STATS
###############################################################################


def match_status (self):
        """Categorizes the relationship of the syllable contours in different 
        responding stanzas in the following scheme:
            CIRC:All have a circumflex
            M1 : All have a post-accentual fall (acute/circumflex)
            M2 : Post-accentual fall and downward motion
            M3 : All rising or all falling
            M4 : Compatible via a word break (see note below)
            C1 : Post-accentual fall paired with UP or UP-G
            C2 : UP and DN
            C3 : UP-G and DN
        Note: BUILT TO ANALYZE STANZA PAIRS, rather than Pindar, etc.  If multiple 
        stanzas were being analyzed together, it would be better to distinguish
        the percentage of stanzas that agree at a level, rather than just a binary.
        
        :return str status: a code indicating the level of alignment.
        """
        if self._match_status:
            return self._match_status
        status = ''
        contours = self.all_contours
        #Check for matches:
        if all(a == 'C' for a in self.all_accents):
            status = 'CIRC'
        elif all(c == 'DN-A' for c in contours):
            status = 'M1'
        elif all(c in ['DN-A', 'DN'] for c in contours):
            status = 'M2'
        elif all(c in ['UP', 'UP-G'] for c in contours):
            status = 'M3'
        elif all(c == 'DN' for c in contours):
            status = 'M3'
        elif all(c in ['DN-A', 'DN', 'N'] for c in contours):
            status = 'M4'
        elif all(c in ['UP', 'UP-G', 'N'] for c in contours):
            status = 'M4'
        elif all(c == 'N' for c in contours):
            status = 'M4'
        else:
            #Check for and sort conflicts:
            if 'DN-A' in contours:
                status = 'C1'
            elif 'UP' in contours:
                status = 'C2'
            elif 'UP-G' in contours:
                status = 'C3'
            else:
                assert False, 'Missing Stat Category for syl {}'.format(self.number)
        self._match_status = status
        return status


def is_match (self):
    return self.match_status in ['M1', 'CIRC']

def is_repeat (self):
    return self.contour in ['=', '=-A']

def is_clash (self):
    return self.match_status == 'C1'