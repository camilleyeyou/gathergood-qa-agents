"""HTTP response assertion helpers."""
import httpx


def assert_status(response: httpx.Response, expected: int, context: str = "") -> None:
    """Assert HTTP status code with a meaningful error on mismatch."""
    if response.status_code != expected:
        body = response.text[:500]
        raise AssertionError(
            f"{context}\n"
            f"Expected {expected}, got {response.status_code}\n"
            f"URL: {response.url}\n"
            f"Body: {body}"
        )
