"""Event lifecycle API tests — TEVNT-01 through TEVNT-07.

Tests cover: full field creation, DRAFT default status, slug auto-generation
with dedup, publish action, cancel from any status, and rejection cases for
publishing cancelled and already-published events.

Each status-transition test creates its own independent event to avoid ordering
dependencies between tests.
"""
import pytest

from factories.common import event_title
from helpers.api import assert_status


def _create_minimal_event(auth_client, org):
    """Helper: create a minimal DRAFT event and return its data dict."""
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "format": "IN_PERSON",
            "category": "MEETUP",
            "start_datetime": "2026-12-15T09:00:00",
            "end_datetime": "2026-12-15T17:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(resp, 201, "POST create minimal event")
    return resp.json()


@pytest.mark.req("TEVNT-01")
def test_create_event_all_fields(auth_client, org, venue, teardown_registry):
    """Create an event with all fields and verify the response shape."""
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "description": "Full field test event",
            "format": "IN_PERSON",
            "category": "FUNDRAISER",
            "start_datetime": "2026-12-15T09:00:00",
            "end_datetime": "2026-12-15T17:00:00",
            "timezone": "America/New_York",
            "venue": venue["id"],
            "tags": ["test", "phase2"],
        },
    )
    assert_status(resp, 201, "POST create event with all fields")
    data = resp.json()

    # Verify required fields are present
    for field in ("title", "slug", "status", "format", "category", "start_datetime", "end_datetime"):
        assert field in data, f"Missing field '{field}' in response"

    assert data["format"] == "IN_PERSON"
    assert data["category"] == "FUNDRAISER"

    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": data["slug"]})


@pytest.mark.req("TEVNT-02")
def test_event_defaults_to_draft(auth_client, org, teardown_registry):
    """A newly created event must have status DRAFT."""
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "format": "VIRTUAL",
            "category": "WORKSHOP",
            "start_datetime": "2026-12-20T10:00:00",
            "end_datetime": "2026-12-20T12:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(resp, 201, "POST create minimal event")
    data = resp.json()
    assert data["status"] == "DRAFT", f"Expected DRAFT, got {data['status']!r}"

    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": data["slug"]})


@pytest.mark.req("TEVNT-03")
def test_event_slug_auto_generated(auth_client, org, teardown_registry):
    """Slug is auto-generated from title; duplicate titles get a dedup suffix."""
    title = event_title()

    # First event
    resp1 = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": title,
            "format": "IN_PERSON",
            "category": "SOCIAL",
            "start_datetime": "2026-12-10T14:00:00",
            "end_datetime": "2026-12-10T18:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(resp1, 201, "POST create first event")
    data1 = resp1.json()
    slug1 = data1["slug"]
    assert slug1, "Slug should be non-empty"
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": slug1})

    # Second event with SAME title — should produce a different slug
    resp2 = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": title,
            "format": "IN_PERSON",
            "category": "SOCIAL",
            "start_datetime": "2026-12-11T14:00:00",
            "end_datetime": "2026-12-11T18:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(resp2, 201, "POST create second event with same title")
    data2 = resp2.json()
    slug2 = data2["slug"]
    assert slug2 != slug1, f"Duplicate title should produce different slug; both got {slug1!r}"
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": slug2})


@pytest.mark.req("TEVNT-04")
def test_publish_draft_event(auth_client, org, teardown_registry):
    """Publishing a DRAFT event changes its status to PUBLISHED."""
    data = _create_minimal_event(auth_client, org)
    event_slug = data["slug"]
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": event_slug})

    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event_slug}/publish/"
    )
    assert_status(resp, 200, "POST publish event")
    published = resp.json()
    assert published["status"] == "PUBLISHED", f"Expected PUBLISHED, got {published['status']!r}"


@pytest.mark.req("TEVNT-05")
def test_cancel_event_from_any_status(auth_client, org, teardown_registry):
    """Cancel works from both DRAFT and PUBLISHED status."""
    # Cancel from DRAFT
    draft = _create_minimal_event(auth_client, org)
    draft_slug = draft["slug"]
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": draft_slug})

    resp_cancel_draft = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft_slug}/cancel/"
    )
    assert_status(resp_cancel_draft, 200, "POST cancel DRAFT event")
    assert resp_cancel_draft.json()["status"] == "CANCELLED"

    # Cancel from PUBLISHED
    draft2 = _create_minimal_event(auth_client, org)
    draft2_slug = draft2["slug"]
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": draft2_slug})

    # Publish first
    pub_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft2_slug}/publish/"
    )
    assert_status(pub_resp, 200, "POST publish event before cancel")

    resp_cancel_pub = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft2_slug}/cancel/"
    )
    assert_status(resp_cancel_pub, 200, "POST cancel PUBLISHED event")
    assert resp_cancel_pub.json()["status"] == "CANCELLED"


@pytest.mark.req("TEVNT-06")
def test_cannot_publish_cancelled_event(auth_client, org, teardown_registry):
    """Publishing a CANCELLED event returns 400 with a clear error message."""
    data = _create_minimal_event(auth_client, org)
    event_slug = data["slug"]
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": event_slug})

    # Cancel it first
    cancel_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event_slug}/cancel/"
    )
    assert_status(cancel_resp, 200, "POST cancel event")

    # Attempt to publish the cancelled event
    publish_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event_slug}/publish/"
    )
    assert publish_resp.status_code == 400, (
        f"Expected 400, got {publish_resp.status_code}\nBody: {publish_resp.text[:300]}"
    )
    assert "Only draft events can be published" in publish_resp.text


@pytest.mark.req("TEVNT-07")
def test_cannot_publish_already_published_event(auth_client, org, teardown_registry):
    """Publishing an already-PUBLISHED event returns 400 with a clear error message."""
    data = _create_minimal_event(auth_client, org)
    event_slug = data["slug"]
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": event_slug})

    # Publish it once
    first_pub = auth_client.post(
        f"/organizations/{org['slug']}/events/{event_slug}/publish/"
    )
    assert_status(first_pub, 200, "POST publish event (first time)")

    # Attempt to publish again
    second_pub = auth_client.post(
        f"/organizations/{org['slug']}/events/{event_slug}/publish/"
    )
    assert second_pub.status_code == 400, (
        f"Expected 400, got {second_pub.status_code}\nBody: {second_pub.text[:300]}"
    )
    assert "Only draft events can be published" in second_pub.text
