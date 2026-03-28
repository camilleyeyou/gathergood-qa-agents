"""Guest list and email settings API tests.

Covers:
- TGUST-01: OWNER/MANAGER can view guest list
- TGUST-02: OWNER/MANAGER can export guest list as CSV
- TEMAL-01: View email config from event GET
- TEMAL-02: Update email config toggles via event PATCH
- TEMAL-03: Send bulk email to all event attendees
- TEMAL-04: View email log
"""
import pytest

from factories.common import event_title, tier_name, unique_email
from helpers.api import assert_status


@pytest.fixture(scope="module")
def email_test_event(auth_client, org, teardown_registry):
    """Published event with at least one attendee (via completed free checkout).

    TEMAL-03 (bulk email) requires an event with at least one attendee.
    Creates its own event + free tier + completed order to be self-contained.

    Returns dict with keys: event, free_tier.
    """
    # 1. Create event
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
    assert_status(create_resp, 201, "Create email_test_event (draft)")
    draft = create_resp.json()

    # 2. Register event for teardown
    teardown_registry["event_ids"].append(
        {"org_slug": org["slug"], "event_slug": draft["slug"]}
    )

    # 3. Create a free tier
    free_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/ticket-tiers/",
        json={
            "name": tier_name(),
            "price": "0.00",
            "quantity_total": 50,
            "min_per_order": 1,
            "max_per_order": 5,
            "visibility": "PUBLIC",
        },
    )
    assert_status(free_resp, 201, "Create free tier for email_test_event")
    free_tier = free_resp.json()

    # 4. Register tier for teardown
    teardown_registry["ticket_tier_ids"].append(
        {
            "org_slug": org["slug"],
            "event_slug": draft["slug"],
            "tier_id": free_tier["id"],
        }
    )

    # 5. Publish the event
    pub_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/publish/"
    )
    assert_status(pub_resp, 200, "Publish email_test_event")
    event = pub_resp.json()

    # 6. Complete a free checkout to create at least one attendee
    # NOTE: checkout API requires org_slug + event_slug + items (not tickets)
    checkout_resp = auth_client.post(
        "/checkout/",
        json={
            "action": "complete",
            "org_slug": org["slug"],
            "event_slug": event["slug"],
            "items": [{"tier_id": free_tier["id"], "quantity": 1}],
            "promo_code": "",
            "billing_name": "Email Test",
            "billing_email": unique_email(),
            "billing_phone": "",
        },
    )
    assert_status(checkout_resp, 201, "Complete free checkout for email_test_event")

    return {"event": event, "free_tier": free_tier}


@pytest.mark.req("TGUST-01")
def test_guest_list_view(auth_client, org, email_test_event):
    """OWNER can view guest list as JSON array with at least one attendee."""
    resp = auth_client.get(
        f"/organizations/{org['slug']}/events/{email_test_event['event']['slug']}/guests/"
    )
    assert_status(resp, 200, "GET guest list")
    data = resp.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    assert len(data) >= 1, (
        f"Expected at least 1 attendee (from fixture checkout), got {len(data)}"
    )


@pytest.mark.req("TGUST-02")
def test_guest_list_csv(auth_client, org, email_test_event):
    """OWNER can export guest list as CSV with correct header columns."""
    resp = auth_client.get(
        f"/organizations/{org['slug']}/events/{email_test_event['event']['slug']}/guests/csv/"
    )
    assert_status(resp, 200, "GET guest list CSV")
    text = resp.text
    assert "Name" in text, f"Expected 'Name' in CSV headers, got: {text[:200]}"
    assert "Email" in text, f"Expected 'Email' in CSV headers, got: {text[:200]}"
    assert "Ticket Tier" in text, (
        f"Expected 'Ticket Tier' in CSV headers, got: {text[:200]}"
    )
    assert "Confirmation Code" in text, (
        f"Expected 'Confirmation Code' in CSV headers, got: {text[:200]}"
    )
    assert "Checked In" in text, (
        f"Expected 'Checked In' in CSV headers, got: {text[:200]}"
    )


@pytest.mark.req("TEMAL-01")
def test_view_email_config(auth_client, org, event):
    """Event GET response includes email_config field (DRAFT event is sufficient)."""
    resp = auth_client.get(f"/organizations/{org['slug']}/events/{event['slug']}/")
    assert_status(resp, 200, "GET event for email_config")
    data = resp.json()
    assert "email_config" in data, (
        f"Expected 'email_config' key in event response. Keys present: {list(data.keys())}"
    )
    # email_config may be {} by default — we only verify the field exists


@pytest.mark.req("TEMAL-02")
def test_update_email_config(auth_client, org, event):
    """PATCH event with email_config toggles persists the values."""
    resp = auth_client.patch(
        f"/organizations/{org['slug']}/events/{event['slug']}/",
        json={
            "email_config": {
                "send_confirmation": True,
                "send_reminder": False,
                "send_notification": True,
            }
        },
    )
    assert_status(resp, 200, "PATCH event email_config")
    updated = resp.json()
    assert updated["email_config"]["send_confirmation"] is True, (
        f"Expected send_confirmation=True, got {updated['email_config']}"
    )
    assert updated["email_config"]["send_reminder"] is False, (
        f"Expected send_reminder=False, got {updated['email_config']}"
    )
    assert updated["email_config"]["send_notification"] is True, (
        f"Expected send_notification=True, got {updated['email_config']}"
    )


@pytest.mark.req("TEMAL-03")
def test_bulk_email_send(auth_client, org, email_test_event):
    """POST bulk email to event attendees succeeds when attendees exist."""
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{email_test_event['event']['slug']}/emails/bulk/",
        json={
            "subject": "Test Bulk Email",
            "body": "This is an automated test email.",
        },
    )
    if resp.status_code == 400:
        body = resp.text
        if "No attendees" in body:
            pytest.fail(
                f"Bulk email returned 400 'No attendees' — fixture did not create an attendee. Body: {body}"
            )
    assert resp.status_code in (200, 201), (
        f"Expected 200 or 201 for bulk email, got {resp.status_code}. Body: {resp.text[:500]}"
    )


@pytest.mark.req("TEMAL-04")
def test_email_log(auth_client, org, email_test_event):
    """GET email log returns a list (may be empty or populated after bulk send)."""
    resp = auth_client.get(
        f"/organizations/{org['slug']}/events/{email_test_event['event']['slug']}/emails/log/"
    )
    assert_status(resp, 200, "GET email log")
    data = resp.json()
    assert isinstance(data, list), (
        f"Expected email log to be a list, got {type(data)}"
    )
    # list may be empty or contain the bulk email from TEMAL-03 — assert type only
