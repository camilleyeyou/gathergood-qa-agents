"""Smoke tests: verify all dependencies are importable and config loads."""
import pytest


@pytest.mark.req("INFR-01")
def test_imports():
    """All core dependencies are importable."""
    import pytest as _pytest
    import httpx
    import playwright
    import pydantic_settings
    import faker
    assert _pytest is not None
    assert httpx is not None
    assert playwright is not None


@pytest.mark.req("INFR-02")
def test_settings_loads():
    """Settings class loads with default values (no .env required)."""
    from settings import Settings
    s = Settings()
    assert s.API_URL.startswith("https://")
    assert "railway.app" in s.API_URL
    assert s.BASE_URL.startswith("https://")


@pytest.mark.req("INFR-06")
def test_req_marker_registered():
    """The @pytest.mark.req marker is registered and usable without warnings."""
    # This test itself uses the marker; if pytest runs with -W error::PytestUnknownMarkWarning
    # and this test is collected, the marker is registered.
    pass


@pytest.mark.req("INFR-07")
def test_pytest_collects_tests():
    """pytest can collect tests from the tests/ directory without errors."""
    # If this test runs, collection succeeded.
    pass
