"""Venue API tests — TVENU-01 through TVENU-03.

All venue endpoints are nested under the org slug:
  /organizations/{org_slug}/venues/
  /organizations/{org_slug}/venues/{venue_id}/

Covers:
  TVENU-01: Create venue with full details returns 201 with all fields
  TVENU-02: List venues for org returns array with at least one entry
  TVENU-03: Update venue via PATCH returns updated fields
"""
import pytest

from factories.common import venue_name
from helpers.api import assert_status


@pytest.mark.req("TVENU-01")
def test_create_venue_full_details(auth_client, org, teardown_registry):
    """POST /organizations/{slug}/venues/ returns 201 with all requested fields."""
    resp = auth_client.post(
        f"/organizations/{org['slug']}/venues/",
        json={
            "name": venue_name(),
            "address": "456 Venue Ave",
            "city": "Eventsville",
            "state": "CA",
            "postal_code": "90210",
            "capacity": 200,
        },
    )
    assert_status(resp, 201, "POST venues")
    data = resp.json()

    for field in ("name", "id", "address", "city", "state", "postal_code", "capacity"):
        assert field in data, f"Response missing '{field}' field"

    assert data["capacity"] == 200, (
        f"Expected capacity 200, got {data.get('capacity')}"
    )

    teardown_registry["venue_ids"].append(
        {"org_slug": org["slug"], "venue_id": data["id"]}
    )


@pytest.mark.req("TVENU-02")
def test_list_venues_for_org(auth_client, org, venue):
    """`venue` fixture ensures at least one venue exists; list must return >= 1 items."""
    resp = auth_client.get(f"/organizations/{org['slug']}/venues/")
    assert_status(resp, 200, "GET /organizations/{slug}/venues/")
    data = resp.json()

    assert isinstance(data, list), f"Expected list, got {type(data).__name__}"
    assert len(data) >= 1, "Expected at least one venue in list"


@pytest.mark.req("TVENU-03")
def test_update_venue(auth_client, org, venue):
    """PATCH /organizations/{slug}/venues/{venue_id}/ updates capacity; URL uses venue UUID."""
    original_capacity = venue["capacity"]

    # Update capacity to 999
    resp = auth_client.patch(
        f"/organizations/{org['slug']}/venues/{venue['id']}/",
        json={"capacity": 999},
    )
    assert_status(resp, 200, "PATCH venue")
    data = resp.json()

    assert data["capacity"] == 999, (
        f"Expected capacity 999 after PATCH, got {data.get('capacity')}"
    )

    # Restore original capacity to avoid leaving unexpected state
    restore_resp = auth_client.patch(
        f"/organizations/{org['slug']}/venues/{venue['id']}/",
        json={"capacity": original_capacity},
    )
    assert_status(restore_resp, 200, "PATCH venue (restore capacity)")
