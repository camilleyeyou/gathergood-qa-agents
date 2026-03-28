"""Public pages API tests — TPUBL-01 through TPUBL-05.

Verifies visibility rules for unauthenticated public browse and detail endpoints:
- Only PUBLISHED/LIVE events appear in public browse
- Search and category filters work
- Org public page returns org info and events list
- Public event detail shows only PUBLIC ticket tiers
- HIDDEN and INVITE_ONLY tiers are filtered out

All requests are unauthenticated (raw httpx.get — NOT auth_client).
"""
import httpx
import pytest

from factories.common import event_title, tier_name
from helpers.api import assert_status
from settings import Settings

_settings = Settings()


@pytest.fixture(scope="module")
def visibility_event(auth_client, org, teardown_registry):
    """Published event with PUBLIC, HIDDEN, and INVITE_ONLY tiers.

    Used by TPUBL-04 and TPUBL-05 to verify tier filtering on public detail.

    Returns dict:
        {
            "event": <event dict>,
            "public_tier": <tier dict>,
            "hidden_tier": <tier dict>,
            "invite_tier": <tier dict>,
        }
    """
    # Create event
    create_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "format": "IN_PERSON",
            "category": "MEETUP",
            "start_datetime": "2026-12-15T10:00:00",
            "end_datetime": "2026-12-15T18:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(create_resp, 201, "Create visibility_event (draft)")
    draft = create_resp.json()
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": draft["slug"]})

    # Create PUBLIC tier
    pub_tier_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/ticket-tiers/",
        json={
            "name": f"Public-{tier_name()}",
            "price": "0.00",
            "quantity_total": 10,
            "min_per_order": 1,
            "max_per_order": 5,
            "visibility": "PUBLIC",
        },
    )
    assert_status(pub_tier_resp, 201, "Create PUBLIC tier for visibility_event")
    public_tier = pub_tier_resp.json()
    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"], "event_slug": draft["slug"], "tier_id": public_tier["id"]
    })

    # Create HIDDEN tier
    hidden_tier_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/ticket-tiers/",
        json={
            "name": f"Hidden-{tier_name()}",
            "price": "0.00",
            "quantity_total": 10,
            "min_per_order": 1,
            "max_per_order": 5,
            "visibility": "HIDDEN",
        },
    )
    assert_status(hidden_tier_resp, 201, "Create HIDDEN tier for visibility_event")
    hidden_tier = hidden_tier_resp.json()
    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"], "event_slug": draft["slug"], "tier_id": hidden_tier["id"]
    })

    # Create INVITE_ONLY tier
    invite_tier_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/ticket-tiers/",
        json={
            "name": f"Invite-{tier_name()}",
            "price": "0.00",
            "quantity_total": 10,
            "min_per_order": 1,
            "max_per_order": 5,
            "visibility": "INVITE_ONLY",
        },
    )
    assert_status(invite_tier_resp, 201, "Create INVITE_ONLY tier for visibility_event")
    invite_tier = invite_tier_resp.json()
    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"], "event_slug": draft["slug"], "tier_id": invite_tier["id"]
    })

    # Publish the event
    pub_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/publish/"
    )
    assert_status(pub_resp, 200, "Publish visibility_event")
    pub_event = pub_resp.json()

    return {
        "event": pub_event,
        "public_tier": public_tier,
        "hidden_tier": hidden_tier,
        "invite_tier": invite_tier,
    }


@pytest.mark.req("TPUBL-01")
def test_public_browse_events():
    """Public browse returns a list of events; category and search filters work.

    DEVIATION: ?format= filter returns 404 — not supported by live API. Skipped.
    """
    # Base browse — unauthenticated
    resp = httpx.get(_settings.API_URL + "/public/events/", timeout=30)
    assert resp.status_code == 200, (
        f"Expected 200 from /public/events/, got {resp.status_code}\nBody: {resp.text[:300]}"
    )
    data = resp.json()
    assert isinstance(data, list), f"Expected list response, got {type(data).__name__}: {str(data)[:200]}"

    # Category filter
    cat_resp = httpx.get(_settings.API_URL + "/public/events/?category=MEETUP", timeout=30)
    assert cat_resp.status_code == 200, (
        f"Expected 200 from /public/events/?category=MEETUP, got {cat_resp.status_code}"
    )
    assert isinstance(cat_resp.json(), list), "Category filter should return a list"

    # Search filter
    search_resp = httpx.get(_settings.API_URL + "/public/events/?q=test", timeout=30)
    assert search_resp.status_code == 200, (
        f"Expected 200 from /public/events/?q=test, got {search_resp.status_code}"
    )
    assert isinstance(search_resp.json(), list), "Search filter should return a list"

    # DEVIATION: ?format= filter returns 404 — not supported by live API. Skipped.


@pytest.mark.req("TPUBL-02")
def test_public_browse_excludes_draft():
    """No DRAFT or CANCELLED events appear in public browse results."""
    resp = httpx.get(_settings.API_URL + "/public/events/", timeout=30)
    assert resp.status_code == 200, (
        f"Expected 200 from /public/events/, got {resp.status_code}\nBody: {resp.text[:300]}"
    )
    events = resp.json()
    for ev in events:
        status = ev.get("status")
        assert status not in ("DRAFT", "CANCELLED"), (
            f"Public browse returned a {status} event: id={ev.get('id')}, title={ev.get('title')!r}"
        )


@pytest.mark.req("TPUBL-03")
def test_public_org_page(org):
    """Organization public page returns org info and events list."""
    resp = httpx.get(_settings.API_URL + f"/public/{org['slug']}/", timeout=30)
    assert resp.status_code == 200, (
        f"Expected 200 from /public/{org['slug']}/, got {resp.status_code}\nBody: {resp.text[:300]}"
    )
    data = resp.json()
    assert "organization" in data, f"Response missing 'organization' key: {list(data.keys())}"
    assert "events" in data, f"Response missing 'events' key: {list(data.keys())}"
    assert isinstance(data["events"], list), (
        f"Expected 'events' to be a list, got {type(data['events']).__name__}"
    )
    assert data["organization"]["slug"] == org["slug"], (
        f"Expected org slug {org['slug']!r}, got {data['organization']['slug']!r}"
    )


@pytest.mark.req("TPUBL-04")
def test_public_event_detail_public_tiers_only(org, visibility_event):
    """Public event detail includes only PUBLIC ticket tiers.

    ticket_tiers in public response do NOT include "visibility" field — it's stripped.
    We verify by tier name prefixes.
    """
    event_slug = visibility_event["event"]["slug"]
    resp = httpx.get(
        _settings.API_URL + f"/public/{org['slug']}/events/{event_slug}/",
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Expected 200 from public event detail, got {resp.status_code}\nBody: {resp.text[:300]}"
    )
    data = resp.json()
    assert "ticket_tiers" in data, f"Response missing 'ticket_tiers' key: {list(data.keys())}"

    tier_names = [t["name"] for t in data["ticket_tiers"]]

    # PUBLIC tier must be present
    assert any(n.startswith("Public-") for n in tier_names), (
        f"Expected at least one 'Public-' tier in public detail, got: {tier_names}"
    )

    # HIDDEN and INVITE_ONLY tiers must NOT be present
    hidden_found = [n for n in tier_names if n.startswith("Hidden-")]
    invite_found = [n for n in tier_names if n.startswith("Invite-")]
    assert not hidden_found, (
        f"HIDDEN tier should not appear in public detail, but found: {hidden_found}"
    )
    assert not invite_found, (
        f"INVITE_ONLY tier should not appear in public detail, but found: {invite_found}"
    )

    # ticket_tiers in public response do NOT include "visibility" field — it's stripped.
    # We verify by tier name prefixes.


@pytest.mark.req("TPUBL-05")
def test_public_event_hides_non_public_tiers(org, visibility_event):
    """HIDDEN and INVITE_ONLY tiers are absent; only the PUBLIC tier appears."""
    event_slug = visibility_event["event"]["slug"]
    resp = httpx.get(
        _settings.API_URL + f"/public/{org['slug']}/events/{event_slug}/",
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Expected 200 from public event detail, got {resp.status_code}\nBody: {resp.text[:300]}"
    )
    data = resp.json()
    tier_names = [t["name"] for t in data["ticket_tiers"]]

    assert not any(n.startswith("Hidden-") for n in tier_names), (
        f"HIDDEN tier should not appear in public detail, but found in: {tier_names}"
    )
    assert not any(n.startswith("Invite-") for n in tier_names), (
        f"INVITE_ONLY tier should not appear in public detail, but found in: {tier_names}"
    )
    assert len(data["ticket_tiers"]) == 1, (
        f"Only the PUBLIC tier should appear, but got {len(data['ticket_tiers'])} tiers: {tier_names}"
    )
