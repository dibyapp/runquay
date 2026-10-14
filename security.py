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


def account_hint(value):
    """Return a bounded masked hint; never retain the full provider email."""
    if not isinstance(value, str) or len(value) > 254 or not re.fullmatch(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,24}", value):
        return ""
    local, domain = value.rsplit("@", 1)
    prefix = local[:2] if len(local) > 2 else local[:1] if len(local) > 1 else ""
    return prefix + "•••@" + domain[:1] + "•••." + domain.rsplit(".", 1)[1].lower()


def sanitize(value):
    if isinstance(value, dict):
        return {k: "[REDACTED CREDENTIAL]" if re.search(r"(?i)(?:api.?key|access.?token|refresh.?token|password|authorization)$", k) else sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return redact(value) if isinstance(value, str) else value
