def count_characters(file_path):
    """
    Count total characters (including spaces) in a file.
    
    Args:
        file_path: Path to input file
        
    Returns:
        int: Total character count
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return len(content)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return 0
    except Exception as e:
        print(f"Error reading file: {e}")
        return 0

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python count_chars.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    count = count_characters(file_path)
    print(f"Total characters in {file_path}: {count}")