import re

_ESC_MD_V2 = r"_-[]()~>#+-=|{}.!"


def escape_markdown_v2(text: str) -> str:
    # Minimal replacer for MarkdownV2 escaping
    if text is None:
        return ""
    return re.sub(r'([\\_\-\[\]\(\)~>#\+\-=\|{}.!])', r"\\\\\\1", str(text))
