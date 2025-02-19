# -*- coding: utf-8 -*-
'''
Ports of contour compatibility logic from Anna Conser's Greek-Poetry project, esp. methods from the syllable and stanza classes.
The port includes:
    - class-based logic to functional 
    - machine scanned source to manually scanned sources
    - support for polystrophic songs

How we compute compatibility of XML lines:
    STEP 1 Get "intra-line" contours for each line *token*, i.e. contours based on accents and word-breaks.
        - get_contours_line
    STEP 2 Get "inter-line" contours (still) for each line *type*, i.e. contours based on the contours of several responding lines.
        - all_contours_at_position
    STEP 3 Get detailed match status for each line *type*, i.e. the match type or clash type of the contours in different responding lines.
        - match_status_line
    STEP 4 Summarize match status as simple MATCH, CLASH, or REPEAT for each line *token*.


*xml_lines => 

@author: Albin Thörn Cleland, Lunds universitet, albin.thorn_cleland@klass.lu.se
@license: MIT
'''

import xml.etree.ElementTree as ET
from lxml import etree

from visualize import restore_text
from grc_utils import is_enclitic, is_proclitic, vowel
from stats import accents, metrically_responding_lines_polystrophic
from words import space_after, space_before


###############################################################################
# 1) AUX
###############################################################################


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
        raise ValueError(f"Lines {[line.get('n', 'unknown') for line in xml_lines]} do not metrically respond.")

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
    mismatched_lines = []
    for i, ms in enumerate(merged_syllables_per_line):
        if len(ms) != num_syllables:
            mismatched_lines.append(xml_lines[i].get('n', 'unknown'))
    if mismatched_lines:
        raise ValueError(f"Mismatch in syllable counts across lines {mismatched_lines} after merging resolution.")

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
        

###############################################################################
# 5) THE STATS
###############################################################################


def match_status_syll(all_contours_at_position: list, all_accents_at_position: list) -> str:
    """Categorizes the relationship of the syllable contours in different 
    responding stanzas in the following scheme, where M = match and C = conflict:
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
    status = ''
    contours = all_contours_at_position
    accents = all_accents_at_position
    #Check for matches:
    if all(accent == 'C' for accent in accents):
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
            print(f'Missing Stat Category for syl {contours[0]}')
    return status


def match_status_line(*xml_lines) -> list:
    '''
    Checks contour match or contradiction of each position in the lines of an arbitrarily polystrophic canticum.
    '''
    grouped_contours = all_contours_line(*xml_lines)
    grouped_accents = all_accents_at_position(*xml_lines)

    contour_match_status = []

    for contours, accents in zip(grouped_contours, grouped_accents):
        position_status = match_status_syll(contours, accents)
        contour_match_status.append(position_status)

    return contour_match_status


def evaluation_line(contour_line, match_status_line) -> list:
    '''
    Merge of is_match, is_repeat, and is_clash from Conser's class_SylGroup,
    with support for all match codes, e.g M2, M3, etc.
    '''
    evaluation = []
    contours_and_matches = zip(contour_line, match_status_line)
    for contour, match in contours_and_matches:
        if match in ['M1', 'M2', 'M3', 'M4', 'CIRC']:
            evaluation.append('MATCH')
        elif contour in ['=', '=-A']:
            evaluation.append('REPEAT')
        elif match in ['C1', 'C2', 'C3']:
            evaluation.append('CLASH')
        else:
            evaluation.append('UNKNOWN')
    return evaluation


def present_contour_evaluation_line(*xml_lines):
    contour = contour_line(*xml_lines)
    match_status = match_status_line(*xml_lines)
    evaluation = evaluation_line(contour, match_status)
    
    # Convert XML elements to their text content
    string_lines = []
    for line in xml_lines:
        sylls = [syll.text for syll in line if syll.tag == 'syll']
        string_lines.append(sylls)
    
    # Group syllables by position
    position_texts = list(zip(*string_lines))
    
    # Print each position with its evaluation
    for i, (position, eval) in enumerate(zip(position_texts, evaluation)):
        print(f'{i + 1}: {position} => {eval}')
        

def simple_comp_stats_canticum(xml_file_path, canticum_ID):
    """
    Calculate percentage of clashes vs other evaluations in corresponding line pairs.
    Returns formatted percentage string.
    """
    tree = etree.parse(xml_file_path)
    root = tree.getroot()

    # Get strophes with matching canticum ID
    strophes = []
    antistrophes = []
    
    # Extract strophes and antistrophes
    for strophe in root.xpath(f'//strophe[@responsion="{canticum_ID}"]'):
        if strophe.get('type') == 'strophe':
            strophes = strophe.findall('l')
        elif strophe.get('type') == 'antistrophe':
            antistrophes = strophe.findall('l')

    all_evaluations = []
    
    # Process each pair of corresponding lines
    for str_line, ant_line in zip(strophes, antistrophes):
        print(f'\nProcessing \033[32m{restore_text(str_line)}\33[0m and \33[33m{restore_text(ant_line)}\33[0m')
        contours = contour_line(str_line, ant_line)
        print(f'Contour line: {contours}')
        match_status = match_status_line(str_line, ant_line)
        print(f'Match status: {match_status}')
        evaluation = evaluation_line(contours, match_status)
        print(f'Eval: {evaluation}')
        all_evaluations.extend(evaluation)

    if not all_evaluations:
        return "0.00%"

    clash_count = all_evaluations.count('CLASH')
    other_count = len(all_evaluations) - clash_count
    total_count = len(all_evaluations)

    # Calculate (CLASH - others) / total
    ratio = (clash_count - other_count) / total_count
    percentage = ratio * 100

    return f"{percentage:.1f}%"


###############################################################################
# MAIN
###############################################################################


if __name__ == '__main__':
    strophe = '<l n="204" metre="4 tr^" speaker="ΧΟ."><syll weight="heavy">Τῇ</syll><syll weight="light">δε</syll> <syll weight="heavy">πᾶ</syll><syll weight="light" anceps="True">ς ἕ</syll><syll weight="heavy">που</syll>, <syll weight="light">δί</syll><syll weight="heavy">ω</syll><syll weight="light" anceps="True">κε</syll> <syll weight="heavy">καὶ</syll> <syll weight="light">τὸ</syll><syll weight="heavy">ν ἄν</syll><syll weight="light" anceps="True">δρα</syll> <syll weight="heavy">πυν</syll><syll weight="light">θά</syll><syll weight="heavy">νου</syll> </l>'
    antistrophe = '''<l n="219" metre="4 tr^"><syll weight="heavy">Νῦν</syll> <syll weight="light">δ' ἐ</syll><syll weight="heavy">πει</syll><syll weight="heavy" anceps="True">δὴ</syll> <syll weight="heavy">στερ</syll><syll weight="light">ρὸ</syll><syll weight="heavy">ν ἤ</syll><syll weight="heavy" anceps="True">δη</syll> <syll weight="heavy">τοὐ</syll><syll weight="light">μὸ</syll><syll weight="heavy">ν ἀν</syll><syll weight="heavy" anceps="True">τικ</syll><syll weight="heavy">νή</syll><syll weight="light">μι</syll><syll weight="heavy">ον</syll> </l>'''
    root_strophe = ET.fromstring(strophe)
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

    zipped = zip(grouped_contours, combined_contours)
    for i, contours in enumerate(zipped):
        print(f'{i + 1}: {contours[0]} => {contours[1]}')

    match_status = match_status_line(root_strophe, root_antistrophe)
    print()
    print(f'MATCH STATUS:')
    print()
    zipped = zip(combined_contours, match_status)
    for i, status in enumerate(zipped):
        print(f'{i + 1}: {status[0]} => {status[1]}')

    evaluation = evaluation_line(combined_contours, match_status)
    print()
    print(f'EVALUATION:')
    print()
    present_contour_evaluation_line(root_strophe, root_antistrophe)

    xml_file_path = "responsion_ach_compiled_test.xml"
    canticum_ID = "ach01"
    result = simple_comp_stats_canticum(xml_file_path, canticum_ID)
    print(f'\nRemember: analysis indicates direction of interval just \033[35mafter\033[0m the present position!')
    print(f"Clash percentage for canticum {canticum_ID}: {result}")