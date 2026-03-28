"""Shared session-scoped fixtures for all Phase 2+ API tests.

Creates the org → venue → event hierarchy once per test session.
All resources are registered in teardown_registry for cleanup.
"""
import pytest

from factories.common import org_name, event_title, venue_name, tier_name, promo_code
from helpers.api import assert_status


@pytest.fixture(scope="session")
def org(auth_client, teardown_registry):
    """Create a test organization once for the entire test session.

    Returns the full response dict: {id, slug, name, role, ...}
    """
    resp = auth_client.post(
        "/organizations/",
        json={
            "name": org_name(),
            "description": "Phase 2 test org",
        },
    )
    assert_status(resp, 201, "Create org")
    data = resp.json()
    teardown_registry["org_ids"].append({"slug": data["slug"]})
    return data


@pytest.fixture(scope="session")
def venue(auth_client, org, teardown_registry):
    """Create a test venue under the session org.

    Returns the full response dict: {id, name, address, city, ...}
    """
    resp = auth_client.post(
        f"/organizations/{org['slug']}/venues/",
        json={
            "name": venue_name(),
            "address": "123 Test St",
            "city": "Testville",
            "state": "TS",
            "postal_code": "12345",
            "capacity": 500,
        },
    )
    assert_status(resp, 201, "Create venue")
    data = resp.json()
    teardown_registry["venue_ids"].append({"org_slug": org["slug"], "venue_id": data["id"]})
    return data


@pytest.fixture(scope="session")
def event(auth_client, org, teardown_registry):
    """Create a DRAFT test event under the session org.

    Returns the full response dict: {id, slug, title, status="DRAFT", ...}
    """
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "format": "IN_PERSON",
            "category": "MEETUP",
            "start_datetime": "2026-12-01T09:00:00",
            "end_datetime": "2026-12-01T17:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(resp, 201, "Create event")
    data = resp.json()
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": data["slug"]})
    return data


@pytest.fixture(scope="session")
def published_event(auth_client, org, teardown_registry):
    """Create and publish a separate test event under the session org.

    Returns the full published event dict: {id, slug, title, status="PUBLISHED", ...}
    """
    # Create a separate event (distinct from the `event` fixture)
    create_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "format": "IN_PERSON",
            "category": "MEETUP",
            "start_datetime": "2026-12-01T09:00:00",
            "end_datetime": "2026-12-01T17:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(create_resp, 201, "Create published_event (draft)")
    draft = create_resp.json()

    # Register for teardown before publishing in case publish fails
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": draft["slug"]})

    # Publish the event
    publish_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/publish/",
    )
    assert_status(publish_resp, 200, "Publish event")
    data = publish_resp.json()
    return data


@pytest.fixture(scope="session")
def checkout_event(auth_client, org, teardown_registry):
    """Published event with free tier, paid tier, and promo code for checkout tests.

    Returns dict with keys: event (full dict), free_tier (full dict),
    paid_tier (full dict), promo (full dict).
    """
    # Create event
    create_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "format": "IN_PERSON",
            "category": "MEETUP",
            "start_datetime": "2026-12-01T09:00:00",
            "end_datetime": "2026-12-01T17:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(create_resp, 201, "Create checkout event (draft)")
    draft = create_resp.json()
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": draft["slug"]})

    # Create free tier
    free_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/ticket-tiers/",
        json={
            "name": tier_name(),
            "price": "0.00",
            "quantity_total": 100,
            "min_per_order": 1,
            "max_per_order": 10,
            "visibility": "PUBLIC",
        },
    )
    assert_status(free_resp, 201, "Create free tier for checkout_event")
    free_tier = free_resp.json()
    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"], "event_slug": draft["slug"], "tier_id": free_tier["id"]
    })

    # Create paid tier
    paid_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/ticket-tiers/",
        json={
            "name": tier_name(),
            "price": "25.00",
            "quantity_total": 50,
            "min_per_order": 1,
            "max_per_order": 5,
            "visibility": "PUBLIC",
        },
    )
    assert_status(paid_resp, 201, "Create paid tier for checkout_event")
    paid_tier = paid_resp.json()
    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"], "event_slug": draft["slug"], "tier_id": paid_tier["id"]
    })

    # Create a PERCENTAGE promo code (10% discount, all tiers)
    promo_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/promo-codes/",
        json={
            "code": promo_code(),
            "discount_type": "PERCENTAGE",
            "discount_value": 10,
            "applicable_tier_ids": [],
            "is_active": True,
            "usage_limit": 100,
        },
    )
    assert_status(promo_resp, 201, "Create promo code for checkout_event")
    promo_data = promo_resp.json()
    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"], "event_slug": draft["slug"], "promo_id": promo_data["id"]
    })

    # Publish the event
    pub_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/publish/"
    )
    assert_status(pub_resp, 200, "Publish checkout event")
    event = pub_resp.json()

    return {
        "event": event,
        "free_tier": free_tier,
        "paid_tier": paid_tier,
        "promo": promo_data,
    }


@pytest.fixture(scope="session")
def expired_promo(auth_client, org, checkout_event, teardown_registry):
    """Create a promo with valid_until in the past for TCHKT-10.

    Returns the promo dict.
    """
    event_slug = checkout_event["event"]["slug"]
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event_slug}/promo-codes/",
        json={
            "code": promo_code(),
            "discount_type": "PERCENTAGE",
            "discount_value": 20,
            "applicable_tier_ids": [],
            "is_active": True,
            "usage_limit": 100,
            "valid_until": "2020-01-01T00:00:00Z",
        },
    )
    assert_status(resp, 201, "Create expired promo for checkout_event")
    data = resp.json()
    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"], "event_slug": event_slug, "promo_id": data["id"]
    })
    return data


@pytest.fixture(scope="session")
def exhausted_promo(auth_client, org, checkout_event, teardown_registry):
    """Create a promo with usage_limit=0 (exhausted) for TCHKT-11.

    Returns the promo dict.
    """
    event_slug = checkout_event["event"]["slug"]
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event_slug}/promo-codes/",
        json={
            "code": promo_code(),
            "discount_type": "PERCENTAGE",
            "discount_value": 15,
            "applicable_tier_ids": [],
            "is_active": True,
            "usage_limit": 0,
        },
    )
    assert_status(resp, 201, "Create exhausted promo for checkout_event")
    data = resp.json()
    teardown_registry["promo_code_ids"].append({
        "org_slug": org["slug"], "event_slug": event_slug, "promo_id": data["id"]
    })
    return data
