import re


def strip_html_tags(text):
    return re.sub("<.+?>", "", text, count=0, flags=re.IGNORECASE | re.DOTALL)


def extract_command_args(message_text):
    return " ".join(message_text.split()[1:])
