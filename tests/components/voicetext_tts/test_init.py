"""Tests for the voicetext_tts integration setup."""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.voicetext_tts.const import DOMAIN


@pytest.mark.asyncio
async def test_setup_entry_stores_api_key_and_session(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    stored = hass.data[DOMAIN][entry.entry_id]
    assert stored["api_key"] == "fake-key"
    assert stored["session"] is not None


@pytest.mark.asyncio
async def test_unload_entry_removes_stored_data(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.entry_id not in hass.data.get(DOMAIN, {})
