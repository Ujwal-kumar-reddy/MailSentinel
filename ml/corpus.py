import hashlib
import re
import statistics
import tarfile
from collections import Counter
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.request import urlopen

from ml.text import combine, normalize

DATA = Path(__file__).resolve().parent / "data"
BASE = "https://spamassassin.apache.org/old/publiccorpus/"
ARCHIVES = {"20030228_easy_ham": 0, "20030228_easy_ham_2": 0, "20030228_hard_ham": 0,
            "20030228_spam": 1, "20050311_spam_2": 1}


def read_email(raw):
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    part = msg.get_body(preferencelist=("plain", "html"))
    body = ""
    if part is not None and part.get_content_maintype() == "text":
        payload = part.get_payload(decode=True) or b""
        try:
            body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        except LookupError:
            body = payload.decode("utf-8", errors="replace")
    return str(msg.get("Subject", "")), body


def distribution(labels):
    counts = Counter(labels)
    return {"legitimate": counts[0], "spam": counts[1]}


def load():
    DATA.mkdir(exist_ok=True)
    seen, conflicts, hashes, lengths = {}, set(), {}, []
    raw_labels = []
    empty = duplicates = missing_subject = missing_body = 0
    for name, label in ARCHIVES.items():
        path = DATA / (name + ".tar.bz2")
        if not path.exists():
            with urlopen(BASE + path.name, timeout=60) as response:
                data = response.read()
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        with tarfile.open(path, "r:bz2") as archive:
            for entry in archive:
                if not entry.isfile() or not re.fullmatch(r"\d+\.[0-9a-f]{32}", Path(entry.name).name):
                    continue
                raw_labels.append(label)
                subject, body = read_email(archive.extractfile(entry).read())
                missing_subject += int(not subject.strip())
                missing_body += int(not body.strip())
                text = combine(subject[:500], body[:50000])
                key = normalize(text)
                if not key:
                    empty += 1
                elif key in seen:
                    duplicates += 1
                    if seen[key][1] != label:
                        conflicts.add(key)
                else:
                    seen[key] = (text, label)
    rows = [row for key, row in seen.items() if key not in conflicts]
    texts, labels = map(list, zip(*rows))
    lengths = sorted(len(t) for t in texts)
    return texts, labels, {"source": BASE, "sha256": hashes, "raw": distribution(raw_labels),
        "clean": distribution(labels), "missing_subject": missing_subject, "missing_body": missing_body,
        "empty": empty, "duplicates": duplicates, "conflicting_groups": len(conflicts),
        "median_chars": statistics.median(lengths), "p95_chars": lengths[int(.95 * (len(lengths)-1))]}
