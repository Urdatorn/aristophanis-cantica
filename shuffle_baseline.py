import os
import shutil
import xml.etree.ElementTree as ET
import random

def shuffle_lines_within_strophes(xml_input_path, xml_output_path):
    tree = ET.parse(xml_input_path)
    root = tree.getroot()

    for strophe in root.findall('.//strophe'):
        l_elements = [l for l in strophe.findall('l')]
        random.shuffle(l_elements)

        for l in l_elements:
            strophe.remove(l)
        for l in l_elements:
            strophe.append(l)

    tree.write(xml_output_path, encoding="utf-8", xml_declaration=True)

def run_shuffling_loop(start=15, stop=101):
    for i in range(start, stop):
        prev_dir = f"data/compiled/baseline_tetrameter_shuffled{i - 1}"
        curr_dir = f"data/compiled/baseline_tetrameter_shuffled{i}"
        input_filename = "responsion_tetrametershuffled_compiled.xml"
        output_filename = f"responsion_tetrametershuffled_compiled{i}.xml"

        # Create the new folder
        os.makedirs(curr_dir, exist_ok=True)

        # Copy all contents from previous folder
        if os.path.exists(prev_dir):
            for fname in os.listdir(prev_dir):
                src_path = os.path.join(prev_dir, fname)
                dst_path = os.path.join(curr_dir, fname)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
        else:
            raise FileNotFoundError(f"Previous directory {prev_dir} does not exist!")

        # Shuffle the XML and save in current dir
        input_path = os.path.join(curr_dir, input_filename)
        output_path = os.path.join(curr_dir, output_filename)
        shuffle_lines_within_strophes(input_path, output_path)

if __name__ == "__main__":
    run_shuffling_loop()