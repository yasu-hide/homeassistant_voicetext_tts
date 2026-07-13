"""VoiceText TTS platform."""
from __future__ import annotations

import logging

from homeassistant.components.tts import TextToSpeechEntity, TtsAudioType, Voice
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import VoiceTextError, synthesize
from .const import (
    ATTR_EMOTION,
    ATTR_EMOTION_LEVEL,
    ATTR_PITCH,
    ATTR_SPEAKER,
    ATTR_SPEED,
    ATTR_VOLUME,
    DEFAULT_EMOTION_LEVEL,
    DEFAULT_PITCH,
    DEFAULT_SPEAKER,
    DEFAULT_SPEED,
    DEFAULT_VOLUME,
    DOMAIN,
    SPEAKERS,
    SUPPORTED_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VoiceText TTS entity from a config entry."""
    async_add_entities([VoiceTextTTSEntity(hass, entry)])


class VoiceTextTTSEntity(TextToSpeechEntity):
    """VoiceText TTS entity."""

    _attr_supported_languages = ["ja-JP"]
    _attr_default_language = "ja-JP"
    _attr_supported_options = SUPPORTED_OPTIONS
    _attr_default_options = {
        ATTR_SPEAKER: DEFAULT_SPEAKER,
        ATTR_EMOTION_LEVEL: DEFAULT_EMOTION_LEVEL,
        ATTR_PITCH: DEFAULT_PITCH,
        ATTR_SPEED: DEFAULT_SPEED,
        ATTR_VOLUME: DEFAULT_VOLUME,
    }

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = "VoiceText TTS"

    async def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return the list of VoiceText speakers as supported voices."""
        return [Voice(speaker, speaker) for speaker in SPEAKERS]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict | None = None
    ) -> TtsAudioType:
        """Load TTS audio from VoiceText."""
        options = options or {}
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        try:
            entry_options = self._entry.options
            audio = await synthesize(
                session=data["session"],
                api_key=data["api_key"],
                text=message,
                speaker=options.get(
                    ATTR_SPEAKER, entry_options.get(ATTR_SPEAKER, DEFAULT_SPEAKER)
                ),
                emotion=options.get(ATTR_EMOTION),
                emotion_level=options.get(
                    ATTR_EMOTION_LEVEL,
                    entry_options.get(ATTR_EMOTION_LEVEL, DEFAULT_EMOTION_LEVEL),
                ),
                pitch=options.get(
                    ATTR_PITCH, entry_options.get(ATTR_PITCH, DEFAULT_PITCH)
                ),
                speed=options.get(
                    ATTR_SPEED, entry_options.get(ATTR_SPEED, DEFAULT_SPEED)
                ),
                volume=options.get(
                    ATTR_VOLUME, entry_options.get(ATTR_VOLUME, DEFAULT_VOLUME)
                ),
            )
        except VoiceTextError:
            _LOGGER.exception("VoiceText TTS synthesis failed")
            return None, None
        return "mp3", audio
