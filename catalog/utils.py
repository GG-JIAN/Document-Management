import re


def split_authors(value):
    """Split submitted author names on Chinese enumeration or semicolon separators."""
    return [part.strip() for part in re.split(r"[、；;]+", value or "") if part.strip()]


def normalize_authors(value):
    """Store author names with one consistent visible separator."""
    return "、".join(split_authors(value))


def split_keyword_names(value):
    """Split and deduplicate keyword names from common Chinese/English separators."""
    if isinstance(value, (list, tuple)):
        value = ",".join(str(item) for item in value)
    names = []
    seen = set()
    for part in re.split(r"[,，、；;]+", value or ""):
        name = " ".join(part.split())
        key = name.casefold()
        if name and key not in seen:
            names.append(name)
            seen.add(key)
    return names
