def read_file_content(file_path):
    encodings = ['utf-8', 'ISO-8859-1', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except Exception as e:
            print(f"Error reading {file_path} with encoding {encoding}: {e}")
    
    raise IOError(f"Failed to read {file_path} with all tried encodings.")