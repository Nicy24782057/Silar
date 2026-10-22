import re

from .errors import invalid_output

NORMALIZER_VERSION = "silar-normalizer-0.1.0"


def normalize(text):
    """Only whitespace changes; preserve case, punctuation, numbers and negation."""
    if not isinstance(text, str):
        raise invalid_output()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if any(ord(c) < 32 and c not in "\n\t" for c in text):
        raise invalid_output()
    lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in text.split("\n")]
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    if not result or len(result) > 10000:
        raise invalid_output()
    return result
