"""Tests for teardown registry fixture."""
import pytest


@pytest.mark.req("INFR-05")
def test_teardown_registry_has_expected_keys(teardown_registry):
    """Teardown registry contains all resource category keys."""
    expected_keys = {
        "user_ids", "org_ids", "venue_ids", "event_ids",
        "ticket_tier_ids", "promo_code_ids", "order_ids",
    }
    assert expected_keys.issubset(set(teardown_registry.keys()))


@pytest.mark.req("INFR-05")
def test_teardown_registry_accumulates(teardown_registry):
    """Resources can be appended to the teardown registry."""
    teardown_registry["org_ids"].append("test-org-123")
    assert "test-org-123" in teardown_registry["org_ids"]
    # Clean up to not affect other tests
    teardown_registry["org_ids"].remove("test-org-123")


@pytest.mark.req("INFR-05")
def test_teardown_registry_values_are_lists(teardown_registry):
    """All list-typed registry values are lists (appendable)."""
    list_keys = {"user_ids", "org_ids", "venue_ids", "event_ids",
                 "ticket_tier_ids", "promo_code_ids", "order_ids"}
    for key in list_keys:
        value = teardown_registry[key]
        assert isinstance(value, list), f"registry['{key}'] should be a list, got {type(value)}"
