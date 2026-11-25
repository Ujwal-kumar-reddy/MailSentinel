import re
from ml.text import normalize

# Quoted replies, list-manager footers and forwarded routing fields describe
# the delivery history rather than the author's current message.
BOUNDARY = re.compile(r"^\s*(?:-{2,}\s*(?:original message|forwarded message)|_{8,}|--\s*$|on .{1,240} wrote:\s*$|to unsubscribe\b|(?:https?://\S+\s+)?mailing list information\b)", re.I)
ROUTING = re.compile(r"^\s*(?:received|return-path|message-id|in-reply-to|references|list-[\w-]+|x-[\w-]+|mime-version|content-type|content-transfer-encoding):", re.I)


def visible_text(text):
    subject, _, body = text.partition("\n")
    lines = []
    for line in body.splitlines():
        if BOUNDARY.match(line) and lines:
            break
        if line.lstrip().startswith(">") or ROUTING.match(line):
            continue
        lines.append(line)
    return " ".join(normalize(subject + " " + " ".join(lines)).split()[:160])

