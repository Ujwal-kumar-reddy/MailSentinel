import html
import re


def normalize(value):
    value = html.unescape(value).casefold()
    value = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", " ", value, flags=re.S)
    value = re.sub(r"</?[a-z][^<>]{0,1000}>", " ", value)
    value = re.sub(r"(?:https?://|www\.)\S+", " webaddress ", value)
    value = re.sub(r"\b[\w.+-]+@[\w.-]+\.\w+\b", " emailaddress ", value)
    return " ".join(value.split())


def combine(subject, body):
    return subject.strip() + "\n" + body.strip()
