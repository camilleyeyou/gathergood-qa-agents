"""Unique-per-run test data factories using uuid4 prefixes."""
import uuid

RUN_ID = uuid.uuid4().hex[:8]


def unique_email() -> str:
    """Return test-{run}-{token}@gathergood-test.invalid."""
    token = uuid.uuid4().hex[:6]
    return f"test-{RUN_ID}-{token}@gathergood-test.invalid"


def org_name() -> str:
    """Return test-{run}-org-{token}."""
    return f"test-{RUN_ID}-org-{uuid.uuid4().hex[:4]}"


def event_title() -> str:
    """Return test-{run}-event-{token}."""
    return f"test-{RUN_ID}-event-{uuid.uuid4().hex[:4]}"


def venue_name() -> str:
    """Return test-{run}-venue-{token}."""
    return f"test-{RUN_ID}-venue-{uuid.uuid4().hex[:4]}"


def tier_name() -> str:
    """Return test-{run}-tier-{token}."""
    return f"test-{RUN_ID}-tier-{uuid.uuid4().hex[:4]}"


def promo_code() -> str:
    """Return TEST{RUN}{TOKEN} (will be uppercased by API)."""
    return f"TEST{RUN_ID}{uuid.uuid4().hex[:4]}".upper()
