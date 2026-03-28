"""Shared session-scoped fixtures for all Phase 2 API tests.

Creates the org → venue → event hierarchy once per test session.
All resources are registered in teardown_registry for cleanup.
"""
import pytest

from factories.common import org_name, event_title, venue_name
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
