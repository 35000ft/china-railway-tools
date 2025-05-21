def is_not_blank(input_string) -> bool:
    return bool(input_string and isinstance(input_string, str) and input_string.strip())


def is_blank(input_string) -> bool:
    return not is_not_blank(input_string)
