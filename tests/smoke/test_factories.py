"""Tests for data factory uniqueness and format."""
import pytest
from factories.common import RUN_ID, unique_email, org_name, event_title, venue_name


@pytest.mark.req("INFR-04")
def test_run_id_is_8_hex_chars():
    """RUN_ID is exactly 8 hex characters."""
    assert len(RUN_ID) == 8
    assert all(c in "0123456789abcdef" for c in RUN_ID)


@pytest.mark.req("INFR-04")
def test_unique_email_format():
    """unique_email() returns test-{run}-{token}@gathergood-test.invalid."""
    email = unique_email()
    assert email.startswith(f"test-{RUN_ID}-")
    assert email.endswith("@gathergood-test.invalid")


@pytest.mark.req("INFR-04")
def test_unique_email_no_collision():
    """Two calls to unique_email() return different values."""
    e1 = unique_email()
    e2 = unique_email()
    assert e1 != e2


@pytest.mark.req("INFR-04")
def test_org_name_format():
    """org_name() returns test-{run}-org-{token}."""
    name = org_name()
    assert name.startswith(f"test-{RUN_ID}-org-")


@pytest.mark.req("INFR-04")
def test_event_title_format():
    """event_title() returns test-{run}-event-{token}."""
    title = event_title()
    assert title.startswith(f"test-{RUN_ID}-event-")


@pytest.mark.req("INFR-04")
def test_venue_name_format():
    """venue_name() returns test-{run}-venue-{token}."""
    name = venue_name()
    assert name.startswith(f"test-{RUN_ID}-venue-")
