from lxml import etree

from grc_utils import is_enclitic, is_proclitic
from stats import accents, metrically_responding_lines_polystrophic
from visualize import restore_text
from utils.words import space_after, space_before


def get_contours_line(l_element):
        """
        Adapted from a method in class_stanza
        Iterates through an <l> of <syll> elements and creates a list of melodic contours.
        - DN-A = βαρύς; melody falls after *main* acute or circumflex.
        - DN = Melody falls after non-main accent.
        - UP: Melody rises before the accent.

        - UP-G: Melody rises before the grave.
        - N: No restrictions on the contour.

        Note that 'N' is a contour that will not contradict any following contour. 
        It's a feature and not a bug that e.g. a circumflex at word end will have 'N' contour.
        """

        contours = []
        pre_accent = True # means we're either on the accented syll or earlier in a word, e.g. 'κε' and 'λεύ' in κελεύῃς.
        last_contour = ''

        syllables = [child for child in l_element if child.tag == "syll"]
        for i, s in enumerate(syllables):
            contour = ''
            next_syll = syllables[i + 1] if i + 1 < len(syllables) else None
            word_end = space_after(s) or (s.tail and " " in s.tail) or (next_syll is not None and space_before(next_syll))

            # Check for word-end in middle of resolved syllable [CHECK]
            is_first_res = next_syll.get('resolution') == 'True'
            if is_first_res and word_end: # = first of two resolution syllables with a word end in between
                pre_accent = True # cf. later below
            
            # Check for ENCLITICS (excluding τοῦ), and correct previous syllable [CHECK]
            if s.text and is_enclitic(s.text) and not is_proclitic(s.text):
                if contours and contours[-1] == 'N':
                    contours[-1] = last_contour
                    pre_accent = False

            # MAIN ACCENT followed by characteristic fall [CHECK]
            if s.text and any(ch in accents['acute'] or ch in accents['circumflex'] for ch in s.text):
                if pre_accent:
                    contour = 'DN-A' # = βαρύς, e.g. the second position in 'λο πήδα' and 'κελεύῃς'
                    pre_accent = False
                else:  # unless a second accent caused by an enclitic
                    contour = 'DN'
            # BEFORE ACCENT, the melody rises
            elif pre_accent:
                contour = 'UP'
            # AFTER ACCENT, the melody falls 
            else: # no accent and not pre accent
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


def all_contours_line(*xml_lines):
    """
    Intermediary between get_contours(l_element) and position-based compatibility stats of set of responding lines.

    Takes multiple XML <l> elements, applies get_contours to each, and returns
    lists where each inner list contains the contours for a given syllabic position
    across all lines, while merging resolved syllables.

    - Ensures all input lines metrically respond.
    - Merges two <syll> elements with resolution="True" into a sublist.
    
    Example:
        all_contours_line(line1, line2, line3) 
        returns [
            [contour1_line1, contour1_line2, contour1_line3],
            [contour2_line1, contour2_line2, contour2_line3],
            ...
        ]
    """

    if not metrically_responding_lines_polystrophic(*xml_lines):
        raise ValueError(f"all_contours_line: Lines {[line.get('n', 'unknown') for line in xml_lines]} do not metrically respond.")

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
        raise ValueError(f"all_contours_line: Mismatch in syllable counts across lines {mismatched_lines} after merging resolution.")

    # Transpose the lists: group contours by syllable position
    grouped_contours = list(map(list, zip(*contours_per_line)))

    return grouped_contours


def compatibility_line(*xml_lines) -> list[float]:
    '''
    Computes the contour of a line from a set of responding strophes,
    evaluates matches and repetitions, 
    and returns a list of float ratios indicating the degree of compatibility at each position.

    For every position, the ratio of the largest subset of internally matching strophes to the total amount of strophes is computed.
    - "Matching" means being in [UP, UP-G, N] or [DN, DN-A, N].
    - E.g: given 5 strophes, where 1 and 2 match, and 3, 4 and 5 match, the second group is the largest and the ratio returned would be 3/5 = 0.6.
    - Unambiguous matches thus yield 1. No position yields less than 1 / n, where n is the number of strophes.
    - NB resolved sylls are in sublists
    
    Returns a list of floats, one for each position.
    - To "re-binarize" the results later, simply interpret 1 as MATCH and everything else as REPEAT.
    '''
    print('Processing the following set of responding lines...')
    line_numbers = [line.get('n') for line in xml_lines]
    for line_number, line in zip(line_numbers, xml_lines):
        print(f'\tLine {line_number}: \t{restore_text(line)[30]}...')

    compatibility_ratios = []

    position_lists = all_contours_line(*xml_lines)
    for position in position_lists: # position K = [contourK_line1, contourK_line2, ..., contourK_lineN], where N is number of resp. strophes
        
        all_resolved = True
        for strophe in position:
            if isinstance(strophe, list): # only resolved positions are lists
                continue
            else:
                all_resolved = False
                break

        up = []
        down = []

        for strophe in position: # this is in an invididual syllable's contour
            if isinstance(strophe, list): # checking sublists of two resolved syllable contours
                if all_resolved == True: # proceed as normal if all strophes resolve
                    for resolved_syll in strophe:
                        if resolved_syll in ['UP', 'UP-G', 'N']:
                            up.append(resolved_syll)
                        elif resolved_syll in ['DN', 'DN-A', 'N']:
                            down.append(resolved_syll)
                        else:
                            raise ValueError(f"Unknown contour {resolved_syll} in compatibility_line.")
                
                # special logic to compare resolved and unresolved syllables
                # six obvious combinations:
                # 1. UP(-G) and UP(-G) = UP
                # 2. DN(-A) and DN(-A) = DN
                # 3-4. UP(-G) and N (and vice versa) = UP
                # 5-6. DN(-A) and N (and vice versa) = DN 
                # but these two are less obvious:
                # 5. UP(-G) and DN(-A) = N?
                # 6. DN and UP = N?
                # 
                else: 
                       pass # logic goes here
                    
            elif strophe in ['UP', 'UP-G', 'N']:
                up.append(strophe)
                print(f'{strophe} added to up')
            elif strophe in ['DN', 'DN-A', 'N']:
                print(f'{strophe} added to down')
                down.append(strophe)
            else:
                raise ValueError(f"Unknown contour {strophe} in compatibility_line.")

        max_len = max(len(up), len(down)) # for even N, N/2 <= max_len <= N, otherwise N/2 < max_len < N
        position_compatibility_ratio = max_len / len(position)
        compatibility_ratios.append(position_compatibility_ratio)

        






        

            



def compatibility_canticum(xml_file_path, canticum_ID):
    pass


def compatibility_play(xml_file_path):
    """
    """
    tree = etree.parse(xml_file_path)
    root = tree.getroot()

    cantica = set()
    for strophe in root.xpath('//strophe[@responsion]'):
        cantica.add(strophe.get('responsion'))

    list_of_lists_of_compatibility_per_position_lists = [] # for every canticum, compiling a list of one compatibility-per-position float list for every line

    for canticum in cantica:
        result = compatibility_canticum(xml_file_path, canticum)
        list_of_lists_of_compatibility_per_position_lists.append(result)
    
    return list_of_lists_of_compatibility_per_position_lists