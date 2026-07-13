"""Tests for the VoiceText TTS config flow."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries

from custom_components.voicetext_tts.api import VoiceTextAuthError, VoiceTextAPIError
from custom_components.voicetext_tts.const import DOMAIN


@pytest.mark.asyncio
async def test_user_flow_success(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    with patch(
        "custom_components.voicetext_tts.config_flow.synthesize",
        new=AsyncMock(return_value=b"AUDIO"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"api_key": "good-key"}
        )

    assert result["type"] == "create_entry"
    assert result["data"]["api_key"] == "good-key"


@pytest.mark.asyncio
async def test_user_flow_invalid_auth(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.voicetext_tts.config_flow.synthesize",
        new=AsyncMock(side_effect=VoiceTextAuthError("bad key")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"api_key": "bad-key"}
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.asyncio
async def test_user_flow_cannot_connect(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.voicetext_tts.config_flow.synthesize",
        new=AsyncMock(side_effect=VoiceTextAPIError(503, "server error")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"api_key": "some-key"}
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_options_flow_updates_defaults(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "speaker": "haruka",
            "emotion_level": 3,
            "pitch": 110,
            "speed": 90,
            "volume": 150,
        },
    )
    assert result["type"] == "create_entry"
    assert entry.options["speaker"] == "haruka"
    assert entry.options["emotion_level"] == 3
