"""Promo code API tests — TPRMO-01 through TPRMO-04.

Tests cover: both discount types (PERCENTAGE and FIXED), uppercase storage,
empty applicable_tier_ids applying to all tiers, and validate endpoint checking
active status and tier scope.

CRITICAL: The validate endpoint requires authentication — always use auth_client.
Note: usage_limit exhaustion requires checkout (Phase 3); not tested here.
"""
import pytest

from factories.common import promo_code, tier_name
from helpers.api import assert_status


def _create_tier(auth_client, org, event, teardown_registry):
    """Helper: create a minimal free tier under the event and return its data."""
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event['slug']}/ticket-tiers/",
        json={
            "name": tier_name(),
            "price": "0.00",
            "quantity_total": 10,
        },
    )
    assert_status(resp, 201, "POST create helper tier for promo tests")
    data = resp.json()
    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "tier_id": data["id"],
    })
    return data


@pytest.mark.req("TPRMO-01")
def test_create_promo_percentage_and_fixed(auth_client, org, event, teardown_registry):
    """Create both PERCENTAGE and FIXED discount promo codes."""
    promo_url = f"/organizations/{org['slug']}/events/{event['slug']}/promo-codes/"

    # PERCENTAGE promo
    pct_resp = auth_client.post(
        promo_url,
        json={
            "code": promo_code(),
            "discount_type": "PERCENTAGE",
            "discount_value": "10.00",
            "usage_limit": 100,
        },
    )
    assert_status(pct_resp, 201, "POST create PERCENTAGE promo")
    pct_data = pct_resp.json()
    assert pct_data["discount_type"] == "PERCENTAGE"
    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "promo_id": pct_data["id"],
    })

    # FIXED promo
    fixed_resp = auth_client.post(
        promo_url,
        json={
            "code": promo_code(),
            "discount_type": "FIXED",
            "discount_value": "5.00",
            "usage_limit": 50,
        },
    )
    assert_status(fixed_resp, 201, "POST create FIXED promo")
    fixed_data = fixed_resp.json()
    assert fixed_data["discount_type"] == "FIXED"
    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "promo_id": fixed_data["id"],
    })


@pytest.mark.req("TPRMO-02")
def test_promo_code_stored_uppercase(auth_client, org, event, teardown_registry):
    """Promo codes submitted in lowercase are stored in uppercase by the API."""
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event['slug']}/promo-codes/",
        json={
            "code": "lowercasecode",
            "discount_type": "PERCENTAGE",
            "discount_value": "10.00",
        },
    )
    assert_status(resp, 201, "POST create lowercase promo code")
    data = resp.json()
    assert data["code"] == "LOWERCASECODE", (
        f"Expected 'LOWERCASECODE', got {data['code']!r}"
    )

    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "promo_id": data["id"],
    })


@pytest.mark.req("TPRMO-03")
def test_empty_tier_ids_applies_to_all(auth_client, org, event, teardown_registry):
    """Empty applicable_tier_ids means the code applies to all tiers (validate returns valid=True)."""
    promo_url = f"/organizations/{org['slug']}/events/{event['slug']}/promo-codes/"
    validate_url = f"/organizations/{org['slug']}/events/{event['slug']}/promo-codes/validate/"

    # Create a tier to validate against
    tier_data = _create_tier(auth_client, org, event, teardown_registry)

    # Create promo with empty applicable_tier_ids
    resp = auth_client.post(
        promo_url,
        json={
            "code": promo_code(),
            "discount_type": "PERCENTAGE",
            "discount_value": "15.00",
            "applicable_tier_ids": [],
        },
    )
    assert_status(resp, 201, "POST create promo with empty applicable_tier_ids")
    promo_data = resp.json()
    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "promo_id": promo_data["id"],
    })

    # Validate the promo against the tier — should be valid since no tier restriction
    validate_resp = auth_client.post(
        validate_url,
        json={"code": promo_data["code"], "tier_id": tier_data["id"]},
    )
    assert_status(validate_resp, 200, "POST validate promo (empty tier_ids)")
    assert validate_resp.json()["valid"] is True, (
        f"Expected valid=True for promo with empty applicable_tier_ids, "
        f"got: {validate_resp.json()}"
    )


@pytest.mark.req("TPRMO-04")
def test_validate_promo_active_expired_tier(auth_client, org, event, teardown_registry):
    """Validate endpoint checks active status and tier scope restrictions."""
    promo_url = f"/organizations/{org['slug']}/events/{event['slug']}/promo-codes/"
    validate_url = f"/organizations/{org['slug']}/events/{event['slug']}/promo-codes/validate/"

    # --- Case 1: active promo with no tier restriction --- validates as True
    active_resp = auth_client.post(
        promo_url,
        json={
            "code": promo_code(),
            "discount_type": "PERCENTAGE",
            "discount_value": "5.00",
            "applicable_tier_ids": [],
        },
    )
    assert_status(active_resp, 201, "POST create active promo")
    active_data = active_resp.json()
    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "promo_id": active_data["id"],
    })

    validate_active = auth_client.post(
        validate_url,
        json={"code": active_data["code"]},
    )
    assert_status(validate_active, 200, "POST validate active promo")
    assert validate_active.json()["valid"] is True

    # --- Case 2: deactivated promo --- validates as False (or error response)
    deact_resp = auth_client.post(
        promo_url,
        json={
            "code": promo_code(),
            "discount_type": "FIXED",
            "discount_value": "2.00",
            "applicable_tier_ids": [],
        },
    )
    assert_status(deact_resp, 201, "POST create promo to deactivate")
    deact_data = deact_resp.json()
    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "promo_id": deact_data["id"],
    })

    # Deactivate via PATCH
    patch_resp = auth_client.patch(
        f"/organizations/{org['slug']}/events/{event['slug']}/promo-codes/{deact_data['id']}/",
        json={"is_active": False},
    )
    assert_status(patch_resp, 200, "PATCH deactivate promo")

    validate_deact = auth_client.post(
        validate_url,
        json={"code": deact_data["code"]},
    )
    # Deactivated promo should not be valid (400 or valid=False)
    is_invalid = (
        validate_deact.status_code in (400, 404)
        or validate_deact.json().get("valid") is False
    )
    assert is_invalid, (
        f"Expected invalid result for deactivated promo, "
        f"got status={validate_deact.status_code} body={validate_deact.text[:300]}"
    )

    # --- Case 3: promo tied to specific tier, validated with a DIFFERENT tier --- not valid
    tier_a = _create_tier(auth_client, org, event, teardown_registry)
    tier_b = _create_tier(auth_client, org, event, teardown_registry)

    tier_specific_resp = auth_client.post(
        promo_url,
        json={
            "code": promo_code(),
            "discount_type": "PERCENTAGE",
            "discount_value": "20.00",
            "applicable_tier_ids": [tier_a["id"]],
        },
    )
    assert_status(tier_specific_resp, 201, "POST create tier-specific promo")
    tier_specific_data = tier_specific_resp.json()
    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "promo_id": tier_specific_data["id"],
    })

    # Validate with tier_b (a different tier) — should be not valid
    validate_wrong_tier = auth_client.post(
        validate_url,
        json={"code": tier_specific_data["code"], "tier_id": tier_b["id"]},
    )
    is_invalid_tier = (
        validate_wrong_tier.status_code in (400, 404)
        or validate_wrong_tier.json().get("valid") is False
    )
    assert is_invalid_tier, (
        f"Expected invalid result for promo validated against wrong tier, "
        f"got status={validate_wrong_tier.status_code} body={validate_wrong_tier.text[:300]}"
    )
