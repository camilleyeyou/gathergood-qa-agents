"""Playwright browser test fixtures for UI tests."""
import pytest
from settings import Settings

_settings = Settings()


@pytest.fixture(scope="session")
def base_url():
    """Frontend base URL from settings."""
    return _settings.BASE_URL


@pytest.fixture(scope="session")
def api_url():
    """API base URL from settings."""
    return _settings.API_URL
