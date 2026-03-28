"""Ticket tier API tests — TTICK-01 through TTICK-04.

Tests cover: full option creation with response shape verification,
quantity_remaining calculation, all three visibility options, and soft-delete
via PATCH is_active=false.

All tiers are created under the session `event` fixture (a DRAFT event).
"""
import pytest

from factories.common import tier_name
from helpers.api import assert_status


@pytest.mark.req("TTICK-01")
def test_create_tier_all_options(auth_client, org, event, teardown_registry):
    """Create a ticket tier with all options and verify the full response shape."""
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event['slug']}/ticket-tiers/",
        json={
            "name": tier_name(),
            "price": "25.00",
            "quantity_total": 100,
            "min_per_order": 1,
            "max_per_order": 5,
            "visibility": "PUBLIC",
        },
    )
    assert_status(resp, 201, "POST create ticket tier with all options")
    data = resp.json()

    # Verify required fields are present
    for field in ("name", "price", "quantity_total", "quantity_remaining",
                  "quantity_sold", "min_per_order", "max_per_order",
                  "visibility", "is_active", "id"):
        assert field in data, f"Missing field '{field}' in tier response"

    assert data["visibility"] == "PUBLIC"
    assert data["is_active"] is True

    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "tier_id": data["id"],
    })


@pytest.mark.req("TTICK-02")
def test_quantity_remaining_calculated(auth_client, org, event, teardown_registry):
    """quantity_remaining is computed as quantity_total - quantity_sold on creation."""
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event['slug']}/ticket-tiers/",
        json={
            "name": tier_name(),
            "price": "10.00",
            "quantity_total": 50,
        },
    )
    assert_status(resp, 201, "POST create tier for quantity check")
    data = resp.json()

    assert data["quantity_total"] == 50
    assert data["quantity_sold"] == 0
    assert data["quantity_remaining"] == 50, (
        f"Expected quantity_remaining=50, got {data['quantity_remaining']}"
    )

    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "tier_id": data["id"],
    })


@pytest.mark.req("TTICK-03")
def test_visibility_options(auth_client, org, event, teardown_registry):
    """All three visibility options (PUBLIC, HIDDEN, INVITE_ONLY) are accepted."""
    for visibility in ("PUBLIC", "HIDDEN", "INVITE_ONLY"):
        resp = auth_client.post(
            f"/organizations/{org['slug']}/events/{event['slug']}/ticket-tiers/",
            json={
                "name": tier_name(),
                "price": "0.00",
                "quantity_total": 20,
                "visibility": visibility,
            },
        )
        assert_status(resp, 201, f"POST create tier with visibility={visibility}")
        data = resp.json()
        assert data["visibility"] == visibility, (
            f"Expected visibility={visibility!r}, got {data['visibility']!r}"
        )

        teardown_registry["ticket_tier_ids"].append({
            "org_slug": org["slug"],
            "event_slug": event["slug"],
            "tier_id": data["id"],
        })


@pytest.mark.req("TTICK-04")
def test_soft_delete_tier(auth_client, org, event, teardown_registry):
    """PATCH is_active=false soft-deletes a tier without hard-deleting it."""
    # Create a tier to deactivate
    create_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event['slug']}/ticket-tiers/",
        json={
            "name": tier_name(),
            "price": "5.00",
            "quantity_total": 30,
        },
    )
    assert_status(create_resp, 201, "POST create tier for soft-delete test")
    tier_id = create_resp.json()["id"]

    # Soft-delete via PATCH
    patch_resp = auth_client.patch(
        f"/organizations/{org['slug']}/events/{event['slug']}/ticket-tiers/{tier_id}/",
        json={"is_active": False},
    )
    assert_status(patch_resp, 200, "PATCH soft-delete tier")
    data = patch_resp.json()
    assert data["is_active"] is False, (
        f"Expected is_active=False after PATCH, got {data['is_active']!r}"
    )

    # Register even though deactivated (teardown will attempt DELETE)
    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "tier_id": tier_id,
    })
