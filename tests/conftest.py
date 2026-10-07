"""Shared fixtures for custom integration tests."""

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow tests to load integrations from the local custom_components folder."""
    return enable_custom_integrations
