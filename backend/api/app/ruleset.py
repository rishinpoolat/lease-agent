from agents.rules import load_ruleset

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def rule_severities() -> dict[str, str]:
    return {rule["id"]: rule["severity"] for rule in load_ruleset()["rules"]}


def severity_sort_key(severity: str) -> int:
    return _SEVERITY_ORDER.get(severity, 99)
