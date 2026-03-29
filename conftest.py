"""Root conftest: markers, health check, teardown registry, session-scoped auth client."""
import base64
import json
import time
import uuid

pytest_plugins = ["conftest_report"]

import httpx
import pytest

from factories.common import RUN_ID
from settings import Settings

settings = Settings()


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "req(id): TEST_SPEC.md requirement ID this test verifies"
    )


def pytest_sessionstart(session):
    import httpx as _httpx
    from settings import Settings as _Settings
    s = _Settings()
    try:
        r = _httpx.get(s.API_URL.rstrip("/") + "/", timeout=30)
        if r.status_code >= 500:
            raise RuntimeError(f"Backend health check returned {r.status_code}. Aborting.")
    except _httpx.ConnectError as e:
        raise RuntimeError(f"Cannot connect to backend at {s.API_URL}: {e}")


def _cleanup(client, registry):
    """Clean up all registered test resources in reverse dependency order."""
    print("\n[teardown] Cleaning up test resources...")

    # 1. DELETE ticket tiers
    for entry in registry.get("ticket_tier_ids", []):
        try:
            org_slug = entry["org_slug"]
            event_slug = entry["event_slug"]
            tier_id = entry["tier_id"]
            url = f"/organizations/{org_slug}/events/{event_slug}/ticket-tiers/{tier_id}/"
            resp = client.delete(url)
            print(f"[teardown] DELETE ticket-tier {tier_id}: {resp.status_code}")
        except Exception as e:
            print(f"[teardown] WARNING: Failed to delete ticket tier {entry}: {e}")

    # 2. PATCH promo codes to deactivate
    for entry in registry.get("promo_code_ids", []):
        try:
            org_slug = entry["org_slug"]
            event_slug = entry["event_slug"]
            promo_id = entry["promo_id"]
            url = f"/organizations/{org_slug}/events/{event_slug}/promo-codes/{promo_id}/"
            resp = client.patch(url, json={"is_active": False})
            print(f"[teardown] PATCH promo-code {promo_id} is_active=False: {resp.status_code}")
        except Exception as e:
            print(f"[teardown] WARNING: Failed to deactivate promo code {entry}: {e}")

    # 3. POST cancel events
    for entry in registry.get("event_ids", []):
        try:
            org_slug = entry["org_slug"]
            event_slug = entry["event_slug"]
            url = f"/organizations/{org_slug}/events/{event_slug}/cancel/"
            resp = client.post(url)
            print(f"[teardown] POST cancel event {event_slug}: {resp.status_code}")
        except Exception as e:
            print(f"[teardown] WARNING: Failed to cancel event {entry}: {e}")

    # 4. DELETE venues
    for entry in registry.get("venue_ids", []):
        try:
            org_slug = entry["org_slug"]
            venue_id = entry["venue_id"]
            url = f"/organizations/{org_slug}/venues/{venue_id}/"
            resp = client.delete(url)
            print(f"[teardown] DELETE venue {venue_id}: {resp.status_code}")
        except Exception as e:
            print(f"[teardown] WARNING: Failed to delete venue {entry}: {e}")

    # 5. Orgs and users cannot be deleted (405) -- skip, naming prefix is isolation
    for entry in registry.get("org_ids", []):
        print(f"[teardown] Skipping org delete (not supported): {entry.get('slug', entry)}")

    print("[teardown] Cleanup complete.")


@pytest.fixture(scope="session")
def teardown_registry():
    registry = {
        "user_ids": [],
        "org_ids": [],
        "venue_ids": [],
        "event_ids": [],
        "ticket_tier_ids": [],
        "promo_code_ids": [],
        "order_ids": [],
    }
    yield registry


@pytest.fixture(scope="session")
def auth_client(teardown_registry):
    email = f"test-{RUN_ID}@gathergood-test.invalid"
    password = "TestPass123!"

    client = httpx.Client(base_url=settings.API_URL, timeout=30)

    # Register test user
    reg_resp = client.post(
        "/auth/register/",
        json={
            "email": email,
            "password": password,
            "password_confirm": password,
            "first_name": "Test",
            "last_name": f"User-{RUN_ID}",
        },
    )
    assert reg_resp.status_code == 201, (
        f"Registration failed: expected 201, got {reg_resp.status_code}\n"
        f"URL: {reg_resp.url}\n"
        f"Body: {reg_resp.text[:500]}"
    )

    # Login
    login_resp = client.post(
        "/auth/login/",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, (
        f"Login failed: expected 200, got {login_resp.status_code}\n"
        f"URL: {login_resp.url}\n"
        f"Body: {login_resp.text[:500]}"
    )

    tokens = login_resp.json()
    access_token = tokens["access"]
    refresh_token = tokens["refresh"]

    # Decode JWT exp without PyJWT
    def _decode_exp(token: str) -> float:
        try:
            parts = token.split(".")
            payload_b64 = parts[1]
            # Add padding
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            return float(payload["exp"])
        except Exception:
            return time.time() + 300

    exp = _decode_exp(access_token)
    ttl = exp - time.time()
    print(f"\n[auth_client] JWT TTL: {ttl:.0f}s")

    teardown_registry["test_user_email"] = email

    class _Client:
        def __init__(self):
            self._access = access_token
            self._refresh = refresh_token
            self._exp = exp
            self._http = httpx.Client(
                base_url=settings.API_URL,
                headers={"Authorization": f"Bearer {self._access}"},
                timeout=30,
            )

        def _maybe_refresh(self):
            remaining = self._exp - time.time()
            margin = max(60, ttl * 0.15)
            if remaining < margin:
                resp = self._http.post(
                    "/auth/token/refresh/",
                    json={"refresh": self._refresh},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self._access = data["access"]
                    if "refresh" in data:
                        self._refresh = data["refresh"]
                    self._exp = _decode_exp(self._access)
                    self._http.headers["Authorization"] = f"Bearer {self._access}"

        def get(self, url, **kwargs):
            self._maybe_refresh()
            return self._http.get(url, **kwargs)

        def post(self, url, **kwargs):
            self._maybe_refresh()
            return self._http.post(url, **kwargs)

        def patch(self, url, **kwargs):
            self._maybe_refresh()
            return self._http.patch(url, **kwargs)

        def put(self, url, **kwargs):
            self._maybe_refresh()
            return self._http.put(url, **kwargs)

        def delete(self, url, **kwargs):
            self._maybe_refresh()
            return self._http.delete(url, **kwargs)

        def close(self):
            self._http.close()

    instance = _Client()
    yield instance

    # --- Phase 2 teardown cleanup ---
    _cleanup(instance, teardown_registry)
    instance.close()
