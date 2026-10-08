"""Best-effort log redaction; release exclusion is the primary privacy boundary."""
import re

PATTERNS = [
    re.compile(r"\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{25,})\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r'(?i)(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password)[\s"\x27]*[:=][\s"\x27]*(?:bearer\s+)?[^\s,"\x27}]{8,}'),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def redact(value):
    text = str(value)
    for pattern in PATTERNS:
        text = pattern.sub("[REDACTED CREDENTIAL]", text)
    return text


def sanitize(value):
    if isinstance(value, dict):
        return {k: "[REDACTED CREDENTIAL]" if re.search(r"(?i)(?:api.?key|access.?token|refresh.?token|password|authorization)$", k) else sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return redact(value) if isinstance(value, str) else value
