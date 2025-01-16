from lxml import etree
import sys

def validate_xml(schema_path, xml_path):
    try:
        # Parse the Relax NG schema
        with open(schema_path, 'rb') as schema_file:
            relaxng_doc = etree.parse(schema_file)
            relaxng = etree.RelaxNG(relaxng_doc)

        # Parse the XML file
        with open(xml_path, 'rb') as xml_file:
            xml_doc = etree.parse(xml_file)

        # Validate the XML against the schema
        if relaxng.validate(xml_doc):
            print(f"{xml_path} is valid.")
        else:
            print(f"{xml_path} is invalid.")
            for error in relaxng.error_log:
                print(error)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate_rnc.py <schema.rnc> <file.xml>")
        sys.exit(1)

    schema_file = sys.argv[1]
    xml_file = sys.argv[2]

    validate_xml(schema_file, xml_file)
