"""Order and ticket API tests — TORDR-01 through TORDR-07."""
import re

import httpx
import pytest

from factories.common import unique_email
from helpers.api import assert_status
from settings import Settings


@pytest.fixture(scope="module")
def completed_order(auth_client, org, checkout_event):
    """Complete a free order once per module for order and ticket tests.

    Returns the full order dict from POST /checkout/ action=complete (201).
    """
    resp = auth_client.post(
        "/checkout/",
        json={
            "action": "complete",
            "org_slug": org["slug"],
            "event_slug": checkout_event["event"]["slug"],
            "items": [{"tier_id": checkout_event["free_tier"]["id"], "quantity": 1}],
            "promo_code": "",
            "billing_name": "Order Test Attendee",
            "billing_email": unique_email(),
            "billing_phone": "",
        },
    )
    assert_status(resp, 201, "Complete free order for order tests")
    return resp.json()


@pytest.mark.req("TORDR-01")
def test_list_own_orders(auth_client, completed_order):
    """GET /orders/ returns a list of orders including the completed order."""
    resp = auth_client.get("/orders/")
    assert_status(resp, 200)
    orders = resp.json()
    assert isinstance(orders, list), f"Expected list, got: {type(orders)}"
    assert len(orders) >= 1, f"Expected at least 1 order, got: {orders}"
    found = any(o["id"] == completed_order["id"] for o in orders)
    assert found, (
        f"completed_order id={completed_order['id']} not found in /orders/ list. "
        f"IDs returned: {[o['id'] for o in orders]}"
    )


@pytest.mark.req("TORDR-02")
def test_view_order_detail(auth_client, completed_order):
    """GET /orders/{id}/ returns full order detail for own order."""
    resp = auth_client.get(f"/orders/{completed_order['id']}/")
    assert_status(resp, 200)
    data = resp.json()
    assert data["id"] == completed_order["id"], (
        f"Order id mismatch: expected {completed_order['id']}, got {data.get('id')}"
    )
    assert "confirmation_code" in data, f"Missing 'confirmation_code' in detail: {data}"
    assert "tickets" in data, f"Missing 'tickets' in detail: {data}"
    assert "line_items" in data, f"Missing 'line_items' in detail: {data}"


@pytest.mark.req("TORDR-03")
def test_lookup_by_confirmation_code_no_auth(completed_order):
    """GET /orders/lookup/{code}/ returns order without authentication.

    Also verifies 404 is returned for an unknown confirmation code.
    """
    plain_client = httpx.Client(
        base_url=Settings().API_URL,
        timeout=30,
    )
    try:
        code = completed_order["confirmation_code"]
        resp = plain_client.get(f"/orders/lookup/{code}/")
        assert_status(resp, 200, f"Unauthenticated lookup of confirmation_code={code}")
        data = resp.json()
        assert data["confirmation_code"] == code, (
            f"Expected confirmation_code='{code}', got '{data.get('confirmation_code')}'"
        )

        # 404 for a bogus code
        bogus_resp = plain_client.get("/orders/lookup/ZZZZZZZZZZ/")
        assert bogus_resp.status_code == 404, (
            f"Expected 404 for bogus code, got {bogus_resp.status_code}. "
            f"Body: {bogus_resp.text}"
        )
    finally:
        plain_client.close()


@pytest.mark.req("TORDR-04")
def test_confirmation_code_format(completed_order):
    """Confirmation code matches ^[A-Z0-9]{10}$ (uppercase letters and digits, exactly 10 chars)."""
    code = completed_order["confirmation_code"]
    assert re.match(r'^[A-Z0-9]{10}$', code), (
        f"Confirmation code format invalid: '{code}' "
        f"(expected uppercase alphanumeric, exactly 10 chars)"
    )


@pytest.mark.req("TORDR-05")
def test_list_own_tickets(auth_client, completed_order):
    """GET /tickets/ returns list of own tickets including the ticket from completed_order."""
    resp = auth_client.get("/tickets/")
    assert_status(resp, 200)
    tickets = resp.json()
    assert isinstance(tickets, list), f"Expected list, got: {type(tickets)}"
    assert len(tickets) >= 1, f"Expected at least 1 ticket, got: {tickets}"

    order_ticket_id = completed_order["tickets"][0]["id"]
    found = any(t["id"] == order_ticket_id for t in tickets)
    assert found, (
        f"Ticket id={order_ticket_id} from completed_order not found in /tickets/ list. "
        f"IDs returned: {[t['id'] for t in tickets]}"
    )

    # Verify qr_code_data present on the matched ticket
    ticket = next(t for t in tickets if t["id"] == order_ticket_id)
    assert ticket.get("qr_code_data"), (
        f"Expected non-empty qr_code_data on ticket {order_ticket_id}, got: '{ticket.get('qr_code_data')}'"
    )


@pytest.mark.req("TORDR-06")
def test_qr_code_data_format(completed_order):
    """QR code data matches {order_uuid}:{tier_uuid}:{ticket_uuid}:{16_hex_chars} format."""
    qr = completed_order["tickets"][0]["qr_code_data"]
    UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    QR_RE = f'^({UUID}):({UUID}):({UUID}):([0-9a-f]{{16}})$'
    m = re.match(QR_RE, qr)
    assert m, (
        f"QR format invalid: '{qr}' "
        f"(expected UUID:UUID:UUID:16hexchars)"
    )
    assert len(m.group(4)) == 16, (
        f"HMAC segment should be 16 hex chars, got {len(m.group(4))}: '{m.group(4)}'"
    )


@pytest.mark.req("TORDR-07")
def test_qr_hmac_structure(completed_order):
    """QR code has exactly 4 colon-separated parts; last part is 16 lowercase hex chars.

    UUIDs use dashes (not colons) as separators, so qr.split(':') yields exactly 4 items:
    [order_uuid, tier_uuid, ticket_uuid, hmac_16hex].
    """
    qr = completed_order["tickets"][0]["qr_code_data"]
    parts = qr.split(":")
    assert len(parts) == 4, (
        f"Expected 4 colon-separated parts in QR data, got {len(parts)}: '{qr}'"
    )

    hmac_seg = parts[3]
    assert re.match(r'^[0-9a-f]{16}$', hmac_seg), (
        f"HMAC segment is not 16 lowercase hex chars: '{hmac_seg}'"
    )

    # Verify first 3 parts are valid UUIDs
    UUID_RE = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    for i, part in enumerate(parts[:3]):
        assert re.match(UUID_RE, part), (
            f"QR part {i} is not a valid UUID: '{part}'"
        )
