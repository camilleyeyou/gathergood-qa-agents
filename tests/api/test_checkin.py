"""Check-in API tests — TCHKN-01 through TCHKN-06, TMCHK-01, TMCHK-02, TSTAT-01, TSTAT-02, TSRCH-01.

Covers:
  - QR scan: success, re-scan detection, invalid QR, HMAC forgery
  - TCHKN-05 skipped (no ticket-cancel API on backend)
  - Manual check-in by ticket ID (success + response shape)
  - Check-in stats (totals, percentage, per-tier breakdown)
  - Attendee search by name and confirmation code

NOTE: Tests TCHKN-01 and TCHKN-02 each scan a DIFFERENT ticket from the 2-ticket
checkin_order fixture. TCHKN-03 re-scans the same ticket as TCHKN-02 to obtain an
"already_checked_in" response. pytest runs tests in file order by default and
module-scoped fixtures persist, so this ordering is deterministic within a session.
"""
import pytest

from factories.common import unique_email
from helpers.api import assert_status


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def _checkin_base(org, checkout_event):
    """Return the base URL prefix for all check-in endpoints."""
    return (
        f"/organizations/{org['slug']}"
        f"/events/{checkout_event['event']['slug']}"
        f"/check-in"
    )


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def checkin_base_url(org, checkout_event):
    """Base URL prefix for check-in endpoints (module-scoped)."""
    return _checkin_base(org, checkout_event)


@pytest.fixture(scope="module")
def checkin_order(auth_client, org, checkout_event):
    """Complete a free order with 2 tickets for QR scan tests.

    Returns the full order dict including tickets[0] and tickets[1].
    tickets[0] is used by TCHKN-01 (first scan).
    tickets[1] is used by TCHKN-02 (fresh scan) and TCHKN-03 (re-scan).
    """
    resp = auth_client.post(
        "/checkout/",
        json={
            "action": "complete",
            "org_slug": org["slug"],
            "event_slug": checkout_event["event"]["slug"],
            "items": [{"tier_id": checkout_event["free_tier"]["id"], "quantity": 2}],
            "promo_code": "",
            "billing_name": "ScanTest Attendee",
            "billing_email": unique_email(),
            "billing_phone": "",
        },
    )
    assert_status(resp, 201, "Create 2-ticket checkin_order")
    return resp.json()


@pytest.fixture(scope="module")
def manual_checkin_order(auth_client, org, checkout_event):
    """Complete a separate free order with 1 ticket for manual check-in tests.

    Returns the full order dict.
    """
    resp = auth_client.post(
        "/checkout/",
        json={
            "action": "complete",
            "org_slug": org["slug"],
            "event_slug": checkout_event["event"]["slug"],
            "items": [{"tier_id": checkout_event["free_tier"]["id"], "quantity": 1}],
            "promo_code": "",
            "billing_name": "ManualTest User",
            "billing_email": unique_email(),
            "billing_phone": "",
        },
    )
    assert_status(resp, 201, "Create 1-ticket manual_checkin_order")
    return resp.json()


# ---------------------------------------------------------------------------
# TCHKN-01: Successful QR scan
# ---------------------------------------------------------------------------

@pytest.mark.req("TCHKN-01")
def test_scan_qr_success(auth_client, checkin_order, checkin_base_url):
    """Scan ticket[0] QR — should succeed on first scan."""
    qr = checkin_order["tickets"][0]["qr_code_data"]
    resp = auth_client.post(
        f"{checkin_base_url}/scan/",
        json={"qr_data": qr},
    )
    assert_status(resp, 200, "TCHKN-01 scan QR ticket[0]")
    data = resp.json()
    assert data["status"] == "success", (
        f"TCHKN-01: expected status='success', got '{data.get('status')}'. Full: {data}"
    )


# ---------------------------------------------------------------------------
# TCHKN-02: Successful scan response shape
# ---------------------------------------------------------------------------

@pytest.mark.req("TCHKN-02")
def test_scan_success_response_shape(auth_client, checkin_order, checkin_base_url):
    """Scan ticket[1] (fresh) — verify response has all required fields."""
    qr = checkin_order["tickets"][1]["qr_code_data"]
    resp = auth_client.post(
        f"{checkin_base_url}/scan/",
        json={"qr_data": qr},
    )
    assert_status(resp, 200, "TCHKN-02 scan QR ticket[1]")
    data = resp.json()

    assert data["status"] == "success", (
        f"TCHKN-02: expected status='success', got '{data.get('status')}'. Full: {data}"
    )
    assert data.get("message") == "Checked in successfully!", (
        f"TCHKN-02: unexpected message: '{data.get('message')}'"
    )
    assert "attendee_name" in data, f"TCHKN-02: missing 'attendee_name' in {data}"
    assert "attendee_email" in data, f"TCHKN-02: missing 'attendee_email' in {data}"
    assert "tier_name" in data, f"TCHKN-02: missing 'tier_name' in {data}"
    assert "checked_in_at" in data, f"TCHKN-02: missing 'checked_in_at' in {data}"


# ---------------------------------------------------------------------------
# TCHKN-03: Re-scan returns already_checked_in
# ---------------------------------------------------------------------------

@pytest.mark.req("TCHKN-03")
def test_rescan_returns_already_checked_in(auth_client, checkin_order, checkin_base_url):
    """Re-scan ticket[1] (already scanned by TCHKN-02) — returns already_checked_in."""
    qr = checkin_order["tickets"][1]["qr_code_data"]
    resp = auth_client.post(
        f"{checkin_base_url}/scan/",
        json={"qr_data": qr},
    )
    assert_status(resp, 200, "TCHKN-03 re-scan ticket[1]")
    data = resp.json()

    assert data["status"] == "already_checked_in", (
        f"TCHKN-03: expected status='already_checked_in', got '{data.get('status')}'. Full: {data}"
    )
    assert "Already checked in" in data.get("message", ""), (
        f"TCHKN-03: expected 'Already checked in' in message, got: '{data.get('message')}'"
    )
    assert "checked_in_at" in data, f"TCHKN-03: missing 'checked_in_at' in {data}"


# ---------------------------------------------------------------------------
# TCHKN-04: Invalid QR returns status invalid
# ---------------------------------------------------------------------------

@pytest.mark.req("TCHKN-04")
def test_scan_invalid_qr_returns_invalid(auth_client, checkin_base_url):
    """Scanning a malformed QR string returns status invalid."""
    resp = auth_client.post(
        f"{checkin_base_url}/scan/",
        json={"qr_data": "not-a-valid-qr-string"},
    )
    assert_status(resp, 200, "TCHKN-04 scan invalid QR")
    data = resp.json()

    assert data["status"] == "invalid", (
        f"TCHKN-04: expected status='invalid', got '{data.get('status')}'. Full: {data}"
    )
    msg = data.get("message", "")
    assert "Invalid QR code" in msg or "Signature verification failed" in msg, (
        f"TCHKN-04: expected 'Invalid QR code' or 'Signature verification failed' in message, "
        f"got: '{msg}'"
    )


# ---------------------------------------------------------------------------
# TCHKN-05: Cancelled ticket — SKIPPED (no cancel API on backend)
# ---------------------------------------------------------------------------

@pytest.mark.req("TCHKN-05")
@pytest.mark.skip(
    reason=(
        "Cannot test: no API endpoint exists to cancel individual tickets. "
        "Event cancellation does not invalidate tickets for check-in (empirically verified). "
        "This is a backend limitation."
    )
)
def test_cancelled_ticket_scan_returns_invalid():
    """Placeholder — skipped until backend provides a ticket cancel endpoint."""
    pass


# ---------------------------------------------------------------------------
# TCHKN-06: Forged HMAC returns status invalid
# ---------------------------------------------------------------------------

@pytest.mark.req("TCHKN-06")
def test_hmac_verification_on_scan(auth_client, checkin_order, checkin_base_url):
    """Scanning a valid QR with a forged HMAC returns status invalid.

    QR format: order_uuid:tier_uuid:ticket_uuid:hmac_16hex
    Replace last segment with 16 'a's to forge the signature.
    """
    qr = checkin_order["tickets"][0]["qr_code_data"]
    parts = qr.split(":")
    # QR is 4 colon-separated parts; replace last (HMAC) with a fake
    parts[3] = "aaaaaaaaaaaaaaaa"
    forged = ":".join(parts)

    resp = auth_client.post(
        f"{checkin_base_url}/scan/",
        json={"qr_data": forged},
    )
    assert_status(resp, 200, "TCHKN-06 scan forged HMAC")
    data = resp.json()

    assert data["status"] == "invalid", (
        f"TCHKN-06: expected status='invalid' for forged HMAC, "
        f"got '{data.get('status')}'. Full: {data}"
    )
    assert "Signature verification failed" in data.get("message", ""), (
        f"TCHKN-06: expected 'Signature verification failed' in message, "
        f"got: '{data.get('message')}'"
    )


# ---------------------------------------------------------------------------
# TMCHK-01: Manual check-in by ticket ID
# ---------------------------------------------------------------------------

@pytest.mark.req("TMCHK-01")
def test_manual_checkin_by_ticket_id(auth_client, manual_checkin_order, checkin_base_url):
    """POST check-in/{ticket_id}/manual/ returns status success with attendee_name."""
    ticket_id = manual_checkin_order["tickets"][0]["id"]
    resp = auth_client.post(f"{checkin_base_url}/{ticket_id}/manual/")
    assert_status(resp, 200, "TMCHK-01 manual check-in")
    data = resp.json()

    assert data["status"] == "success", (
        f"TMCHK-01: expected status='success', got '{data.get('status')}'. Full: {data}"
    )
    assert data.get("message") == "Checked in successfully!", (
        f"TMCHK-01: unexpected message: '{data.get('message')}'"
    )
    assert "attendee_name" in data, f"TMCHK-01: missing 'attendee_name' in {data}"


# ---------------------------------------------------------------------------
# TMCHK-02: Manual check-in response format (re-check same ticket)
# ---------------------------------------------------------------------------

@pytest.mark.req("TMCHK-02")
def test_manual_checkin_response_format(auth_client, manual_checkin_order, checkin_base_url):
    """Re-checking an already-checked-in ticket via manual/ shares status/message keys with QR.

    Manual success response does NOT include attendee_email or checked_in_at (Pitfall 6).
    After TMCHK-01 checked the ticket in, this call gets already_checked_in,
    confirming the common {status, message} shape between manual and QR scan endpoints.
    """
    ticket_id = manual_checkin_order["tickets"][0]["id"]
    resp = auth_client.post(f"{checkin_base_url}/{ticket_id}/manual/")
    assert_status(resp, 200, "TMCHK-02 manual re-check")
    data = resp.json()

    # Common fields present in both QR and manual responses
    assert "status" in data, f"TMCHK-02: missing 'status' in {data}"
    assert "message" in data, f"TMCHK-02: missing 'message' in {data}"
    # Ticket already checked in from TMCHK-01
    assert data["status"] == "already_checked_in", (
        f"TMCHK-02: expected status='already_checked_in' on re-check, "
        f"got '{data.get('status')}'. Full: {data}"
    )


# ---------------------------------------------------------------------------
# TSTAT-01: Check-in stats fields
# ---------------------------------------------------------------------------

@pytest.mark.req("TSTAT-01")
def test_checkin_stats_fields(auth_client, checkin_base_url):
    """GET check-in/stats/ returns all required top-level fields."""
    resp = auth_client.get(f"{checkin_base_url}/stats/")
    assert_status(resp, 200, "TSTAT-01 check-in stats")
    data = resp.json()

    assert "total_registered" in data, f"TSTAT-01: missing 'total_registered' in {data}"
    assert isinstance(data["total_registered"], int), (
        f"TSTAT-01: total_registered should be int, got {type(data['total_registered'])}"
    )
    assert "checked_in" in data, f"TSTAT-01: missing 'checked_in' in {data}"
    assert isinstance(data["checked_in"], int), (
        f"TSTAT-01: checked_in should be int, got {type(data['checked_in'])}"
    )
    assert "not_checked_in" in data, f"TSTAT-01: missing 'not_checked_in' in {data}"
    assert isinstance(data["not_checked_in"], int), (
        f"TSTAT-01: not_checked_in should be int, got {type(data['not_checked_in'])}"
    )
    assert "percentage" in data, f"TSTAT-01: missing 'percentage' in {data}"
    assert isinstance(data["percentage"], (int, float)), (
        f"TSTAT-01: percentage should be numeric, got {type(data['percentage'])}"
    )
    assert "by_tier" in data, f"TSTAT-01: missing 'by_tier' in {data}"
    assert data["total_registered"] == data["checked_in"] + data["not_checked_in"], (
        f"TSTAT-01: total_registered ({data['total_registered']}) != "
        f"checked_in ({data['checked_in']}) + not_checked_in ({data['not_checked_in']})"
    )


# ---------------------------------------------------------------------------
# TSTAT-02: Per-tier breakdown in stats
# ---------------------------------------------------------------------------

@pytest.mark.req("TSTAT-02")
def test_checkin_stats_by_tier_breakdown(auth_client, checkin_base_url):
    """GET check-in/stats/ by_tier contains objects with tier_name, total, checked_in."""
    resp = auth_client.get(f"{checkin_base_url}/stats/")
    assert_status(resp, 200, "TSTAT-02 check-in stats by_tier")
    data = resp.json()

    tiers = data.get("by_tier", [])
    assert isinstance(tiers, list), f"TSTAT-02: by_tier should be a list, got {type(tiers)}"
    assert len(tiers) >= 1, f"TSTAT-02: expected at least 1 tier in by_tier, got: {tiers}"

    for tier in tiers:
        assert "tier_name" in tier, f"TSTAT-02: missing 'tier_name' in tier object: {tier}"
        assert "total" in tier, f"TSTAT-02: missing 'total' in tier object: {tier}"
        assert "checked_in" in tier, f"TSTAT-02: missing 'checked_in' in tier object: {tier}"


# ---------------------------------------------------------------------------
# TSRCH-01: Attendee search by name and confirmation code
# ---------------------------------------------------------------------------

@pytest.mark.req("TSRCH-01")
def test_search_attendees(auth_client, checkin_order, checkin_base_url):
    """GET check-in/search/?q= returns attendees matching name and confirmation code.

    Sub-tests:
      a) Search by partial billing_name 'ScanTest' — matches checkin_order attendee
      b) Search by confirmation_code — matches order directly
      c) Verify search result shape: ticket_id, attendee_name, attendee_email,
         tier_name, confirmation_code, checked_in fields
    """
    # (a) Search by name
    resp_name = auth_client.get(f"{checkin_base_url}/search/", params={"q": "ScanTest"})
    assert_status(resp_name, 200, "TSRCH-01 search by name")
    name_results = resp_name.json()
    assert isinstance(name_results, list), (
        f"TSRCH-01: search results should be a list, got {type(name_results)}"
    )
    assert len(name_results) >= 1, (
        f"TSRCH-01: expected >= 1 result for 'ScanTest', got {len(name_results)}"
    )
    assert any("ScanTest" in r.get("attendee_name", "") for r in name_results), (
        f"TSRCH-01: no result with 'ScanTest' in attendee_name. Results: {name_results}"
    )

    # (b) Search by confirmation code
    confirmation_code = checkin_order.get("confirmation_code", "")
    assert confirmation_code, f"TSRCH-01: checkin_order has no confirmation_code: {checkin_order}"

    resp_code = auth_client.get(
        f"{checkin_base_url}/search/", params={"q": confirmation_code}
    )
    assert_status(resp_code, 200, "TSRCH-01 search by confirmation_code")
    code_results = resp_code.json()
    assert isinstance(code_results, list), (
        f"TSRCH-01: search by code results should be a list, got {type(code_results)}"
    )
    assert len(code_results) >= 1, (
        f"TSRCH-01: expected >= 1 result for code '{confirmation_code}', "
        f"got {len(code_results)}"
    )

    # (c) Verify result object shape using the name-search results
    result = name_results[0]
    for field in ("ticket_id", "attendee_name", "attendee_email", "tier_name",
                  "confirmation_code", "checked_in"):
        assert field in result, (
            f"TSRCH-01: missing field '{field}' in search result: {result}"
        )
