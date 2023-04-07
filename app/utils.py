import re

"""

Utility functions

"""

def tag_string_to_list(tags):
    if not tags:
        return []
    return [tag for tag in tags.replace(" ", "").split(",") if tag]


# NOTE: the named arguments can be escaped
def get_named_arguments(fmt_string):
    pattern = re.compile(r'{(?P<name>\w+)}')
    return pattern.findall(fmt_string)

