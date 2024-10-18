def get_code(fn: callable):
    """
    Takes a function and converts it to a string of the implementation within the file
    of the function (it doesn't parse the full AST, or sub-functions etc.)

    Args:
        fn: the function to convert to a string of the code implementation.

    Returns:
        The string of the code implementation.
    """
    with open(fn.__code__.co_filename) as file:
        offset_content = file.readlines()[fn.__code__.co_firstlineno - 1 :]
    first_line = offset_content[1]
    fn_indentation = len(first_line) - len(first_line.lstrip())
    fn_str = [offset_content[0], first_line]
    for line in offset_content[2:]:
        indentation = len(line) - len(line.lstrip())
        if indentation < fn_indentation:
            break
        fn_str.append(line)
    return "".join(fn_str)
