"""Tests for the VoiceText TTS entity."""
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.voicetext_tts.const import DOMAIN


async def test_entity_has_required_language_properties(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("tts.voicetext_tts")
    assert state is not None


async def test_async_get_tts_audio_returns_mp3(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "custom_components.voicetext_tts.tts.synthesize",
        new=AsyncMock(return_value=b"AUDIO_BYTES"),
    ) as mock_synthesize:
        from custom_components.voicetext_tts.tts import VoiceTextTTSEntity

        ent = next(
            e
            for e in hass.data["entity_components"]["tts"].entities
            if isinstance(e, VoiceTextTTSEntity)
        )
        extension, audio = await ent.async_get_tts_audio(
            "こんにちは", "ja-JP", options={"speaker": "haruka", "emotion": "happiness"}
        )
        assert extension == "mp3"
        assert audio == b"AUDIO_BYTES"
        mock_synthesize.assert_called_once()
        _, kwargs = mock_synthesize.call_args
        assert kwargs["speaker"] == "haruka"
        assert kwargs["emotion"] == "happiness"


async def test_async_get_tts_audio_uses_entry_options_as_default(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"api_key": "fake-key"}, options={"speaker": "haruka"}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "custom_components.voicetext_tts.tts.synthesize",
        new=AsyncMock(return_value=b"AUDIO_BYTES"),
    ) as mock_synthesize:
        from custom_components.voicetext_tts.tts import VoiceTextTTSEntity

        ent = next(
            e
            for e in hass.data["entity_components"]["tts"].entities
            if isinstance(e, VoiceTextTTSEntity)
        )
        await ent.async_get_tts_audio("こんにちは", "ja-JP", options={})
        mock_synthesize.assert_called_once()
        _, kwargs = mock_synthesize.call_args
        assert kwargs["speaker"] == "haruka"


async def test_async_get_tts_audio_returns_none_on_voicetext_error(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    from custom_components.voicetext_tts.api import VoiceTextAuthError

    with patch(
        "custom_components.voicetext_tts.tts.synthesize",
        new=AsyncMock(side_effect=VoiceTextAuthError("bad key")),
    ):
        from custom_components.voicetext_tts.tts import VoiceTextTTSEntity

        ent = next(
            e
            for e in hass.data["entity_components"]["tts"].entities
            if isinstance(e, VoiceTextTTSEntity)
        )
        extension, audio = await ent.async_get_tts_audio("こんにちは", "ja-JP", options={})
        assert extension is None
        assert audio is None


async def test_async_get_supported_voices_lists_all_speakers(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"api_key": "fake-key"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    from custom_components.voicetext_tts.tts import VoiceTextTTSEntity

    ent = next(
        e
        for e in hass.data["entity_components"]["tts"].entities
        if isinstance(e, VoiceTextTTSEntity)
    )
    voices = await ent.async_get_supported_voices("ja-JP")
    assert len(voices) == 6
    assert {v.voice_id for v in voices} == {
        "show",
        "haruka",
        "hikari",
        "takeru",
        "santa",
        "bear",
    }
