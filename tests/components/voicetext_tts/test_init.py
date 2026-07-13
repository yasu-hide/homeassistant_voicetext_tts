"""Tests for the voicetext_tts integration setup."""
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.voicetext_tts.const import DOMAIN


async def test_setup_entry_stores_api_key_and_session(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    stored = hass.data[DOMAIN][entry.entry_id]
    assert stored["api_key"] == "fake-key"
    assert stored["session"] is not None


async def test_unload_entry_removes_stored_data(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_options_update_triggers_reload(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with patch.object(
        hass.config_entries, "async_reload", new=AsyncMock(return_value=True)
    ) as mock_reload:
        hass.config_entries.async_update_entry(entry, options={"speaker": "haruka"})
        await hass.async_block_till_done()

    mock_reload.assert_called_once_with(entry.entry_id)
