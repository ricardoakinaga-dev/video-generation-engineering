"""Shared status aggregation primitives with no media or quality imports.

Keeping this small dependency-free module below both quality and media prevents
the semantic QA module from depending back on the media implementation.
"""

QUALITY_STATUSES = (
    "PASS", "FAIL", "PARTIAL", "NOT_APPLICABLE", "NOT_OBSERVED", "NOT_RUN", "UNKNOWN", "BLOCKED"
)


def aggregate_quality(checks):
    """Aggregate exact observed statuses without treating missing evidence as PASS."""
    if not isinstance(checks, list):
        raise TypeError("checks must be a list")
    if not checks:
        return "NOT_OBSERVED"
    results = [check.get("result") for check in checks if isinstance(check, dict)]
    if len(results) != len(checks) or not all(result in QUALITY_STATUSES for result in results):
        raise ValueError("Invalid quality check result")
    if "FAIL" in results:
        return "FAIL"
    if "BLOCKED" in results:
        return "BLOCKED"
    if "PARTIAL" in results:
        return "PARTIAL"
    if any(result in ("NOT_RUN", "UNKNOWN") for result in results):
        return "PARTIAL" if any(result == "PASS" for result in results) else "NOT_OBSERVED"
    if "NOT_OBSERVED" in results:
        return "PARTIAL" if any(result == "PASS" for result in results) else "NOT_OBSERVED"
    if all(result == "NOT_APPLICABLE" for result in results):
        return "NOT_APPLICABLE"
    return "PASS" if all(result in ("PASS", "NOT_APPLICABLE") for result in results) else "PARTIAL"
