import urllib.parse

def sanitize_input(input_value):
    if isinstance(input_value, str):
        return urllib.parse.quote(input_value.strip())
    return input_value
