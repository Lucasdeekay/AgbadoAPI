def write_to_txt_file(filename, text, append=False):
    """
    Writes the given text to a text file.

    Args:
        filename (str): The name of the text file.
        text (str): The text to write to the file.
        append (bool, optional): If True, appends the text to the file.
                                 If False, overwrites the file. Defaults to False.

    Returns:
        bool: True if the write operation was successful, False otherwise.
    """
    try:
        mode = "a" if append else "w"  # 'a' for append, 'w' for write (overwrite)
        with open(filename, mode) as file:
            file.write(text)
        return True
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False

