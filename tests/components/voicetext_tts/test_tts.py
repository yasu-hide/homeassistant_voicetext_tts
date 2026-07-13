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


async def test_default_options_reflects_entry_options(hass):
    """The default_options property itself must merge in entry.options."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={"api_key": "fake-key"}, options={"speaker": "haruka"}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    from custom_components.voicetext_tts.tts import VoiceTextTTSEntity

    ent = next(
        e
        for e in hass.data["entity_components"]["tts"].entities
        if isinstance(e, VoiceTextTTSEntity)
    )
    assert ent.default_options["speaker"] == "haruka"


async def test_default_options_format_defaults_to_mp3_and_sets_preferred_format(hass):
    """Regression guard for the tts_proxy-forces-mp3 bug: our own
    default_options must always mirror the configured format into HA's
    ATTR_PREFERRED_FORMAT, or HA will silently transcode our audio.
    """
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
    assert ent.default_options["format"] == "mp3"
    assert ent.default_options["preferred_format"] == "mp3"


async def test_default_options_emotion_level_defaults_to_string(hass):
    """Regression guard: emotion_level's default must be a string, not an
    int, so ha-form's radio-group selector can pre-select it correctly.
    """
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
    assert ent.default_options["emotion_level"] == "2"


async def test_default_options_format_reflects_entry_options(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"api_key": "fake-key"}, options={"format": "ogg"}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    from custom_components.voicetext_tts.tts import VoiceTextTTSEntity

    ent = next(
        e
        for e in hass.data["entity_components"]["tts"].entities
        if isinstance(e, VoiceTextTTSEntity)
    )
    assert ent.default_options["format"] == "ogg"
    assert ent.default_options["preferred_format"] == "ogg"


async def test_async_get_tts_audio_returns_ogg_when_format_requested(hass):
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
            "こんにちは", "ja-JP", options={"format": "ogg"}
        )
        assert extension == "ogg"
        assert audio == b"AUDIO_BYTES"
        mock_synthesize.assert_called_once()
        _, kwargs = mock_synthesize.call_args
        assert kwargs["audio_format"] == "ogg"


async def test_tts_speak_pipeline_uses_entry_options_as_default(hass):
    """Exercise the real HA pipeline (SpeechManager.process_options), not a
    direct async_get_tts_audio() call, to prove the Configure UI's options
    actually reach the API when no per-call options are supplied.

    HA's tts.speak service requires a real media_player entity to render
    through, so instead we drive the same SpeechManager entry point that
    async_speak()/media_source use: async_create_result_stream(), which
    internally calls process_options() (merging entity.default_options)
    before generating audio - this is the same merge step the real
    tts.speak/media_source pipeline goes through. use_file_cache=False is
    passed because pytest-homeassistant-custom-component's test config dir
    is a fixed shared path (not a per-test tmpdir), so the disk cache would
    otherwise persist across separate test runs and mask this assertion.
    """
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
        manager = hass.data["tts_manager"]
        stream = manager.async_create_result_stream(
            engine="tts.voicetext_tts",
            language="ja-JP",
            options={},
            use_file_cache=False,
        )
        stream.async_set_message("こんにちは")
        await hass.async_block_till_done(wait_background_tasks=True)

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
