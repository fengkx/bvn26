"""Shared process predicate for the move and saved-parity runners."""


def process_succeeded(returncode: int, log: str, *, required_marker: str) -> bool:
    """Preserve these runners' policy; trace completeness is checked separately."""
    return returncode == 0 and 'SCRIPT ERROR' not in log and required_marker in log
