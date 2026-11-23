import re

FOLD_PATTERN = re.compile(r"^(?P<group>.*?)[\s_\-·]*(?<![a-z])fold[\s_\-]*(?P<fold>\d+)$", re.IGNORECASE)


def parse_fold_name(name):
    match = FOLD_PATTERN.match(name.strip())
    if not match:
        return None
    group = match.group("group").strip(" _-·")
    if not group:
        return None
    return group, int(match.group("fold"))
