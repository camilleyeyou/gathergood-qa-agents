"""Event analytics API tests.

Covers:
- TANLT-01: Analytics endpoint returns registrations, attendance, revenue, refunds, and timeline fields
- TANLT-02: Analytics includes registrations.by_tier breakdown array
- TANLT-03: Analytics includes timeline series array (correct key name)
"""
import pytest

from helpers.api import assert_status


@pytest.mark.req("TANLT-01")
def test_analytics_fields(auth_client, org, checkout_event):
    """Analytics endpoint returns all expected top-level and nested fields."""
    resp = auth_client.get(
        f"/organizations/{org['slug']}/events/{checkout_event['event']['slug']}/analytics/"
    )
    assert_status(resp, 200, "GET event analytics")
    data = resp.json()

    # Top-level keys
    for key in ("registrations", "attendance", "revenue", "refunds", "timeline"):
        assert key in data, (
            f"Expected top-level key '{key}' in analytics response. Keys present: {list(data.keys())}"
        )

    # registrations nested keys
    assert "total" in data["registrations"], (
        f"Expected registrations.total. Got: {data['registrations']}"
    )

    # attendance nested keys
    for key in ("checked_in", "total", "rate"):
        assert key in data["attendance"], (
            f"Expected attendance.{key}. Got: {data['attendance']}"
        )

    # revenue nested keys
    for key in ("gross", "fees", "net", "orders"):
        assert key in data["revenue"], (
            f"Expected revenue.{key}. Got: {data['revenue']}"
        )


@pytest.mark.req("TANLT-02")
def test_analytics_by_tier(auth_client, org, checkout_event):
    """Analytics registrations object includes a by_tier breakdown list."""
    resp = auth_client.get(
        f"/organizations/{org['slug']}/events/{checkout_event['event']['slug']}/analytics/"
    )
    assert_status(resp, 200, "GET event analytics for by_tier")
    data = resp.json()

    assert "by_tier" in data["registrations"], (
        f"Expected registrations.by_tier. Got registrations keys: {list(data['registrations'].keys())}"
    )
    assert isinstance(data["registrations"]["by_tier"], list), (
        f"Expected registrations.by_tier to be a list, got {type(data['registrations']['by_tier'])}"
    )


@pytest.mark.req("TANLT-03")
def test_analytics_timeline(auth_client, org, checkout_event):
    """Analytics endpoint includes timeline series array.

    # DEVIATION: API uses "timeline" not "registrations_over_time" as TEST_SPEC suggests.
    """
    resp = auth_client.get(
        f"/organizations/{org['slug']}/events/{checkout_event['event']['slug']}/analytics/"
    )
    assert_status(resp, 200, "GET event analytics for timeline")
    data = resp.json()

    # DEVIATION: API uses "timeline" not "registrations_over_time" as TEST_SPEC suggests
    assert "timeline" in data, (
        f"Expected 'timeline' key in analytics (not 'registrations_over_time'). "
        f"Keys present: {list(data.keys())}"
    )
    assert isinstance(data["timeline"], list), (
        f"Expected timeline to be a list, got {type(data['timeline'])}"
    )
