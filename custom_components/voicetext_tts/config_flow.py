"""Config flow for VoiceText TTS."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VoiceTextAuthError, VoiceTextError, synthesize
from .const import (
    ATTR_EMOTION_LEVEL,
    ATTR_PITCH,
    ATTR_SPEAKER,
    ATTR_SPEED,
    ATTR_VOLUME,
    CONF_API_KEY,
    DEFAULT_EMOTION_LEVEL,
    DEFAULT_PITCH,
    DEFAULT_SPEAKER,
    DEFAULT_SPEED,
    DEFAULT_VOLUME,
    DOMAIN,
    SPEAKERS,
)

_LOGGER = logging.getLogger(__name__)


class VoiceTextConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VoiceText TTS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step: API key entry with a live connectivity test."""
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            try:
                await synthesize(
                    session=session,
                    api_key=user_input[CONF_API_KEY],
                    text="テスト",
                    speaker=DEFAULT_SPEAKER,
                )
            except VoiceTextAuthError:
                errors["base"] = "invalid_auth"
            except VoiceTextError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="VoiceText TTS", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> VoiceTextOptionsFlow:
        """Get the options flow for this handler."""
        return VoiceTextOptionsFlow()


class VoiceTextOptionsFlow(OptionsFlow):
    """Handle options for VoiceText TTS (default speaker/emotion/pitch/speed/volume)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    ATTR_SPEAKER, default=current.get(ATTR_SPEAKER, DEFAULT_SPEAKER)
                ): vol.In(SPEAKERS),
                vol.Optional(
                    ATTR_EMOTION_LEVEL,
                    default=current.get(ATTR_EMOTION_LEVEL, DEFAULT_EMOTION_LEVEL),
                ): vol.In([1, 2, 3, 4]),
                vol.Optional(
                    ATTR_PITCH, default=current.get(ATTR_PITCH, DEFAULT_PITCH)
                ): vol.All(int, vol.Range(min=50, max=200)),
                vol.Optional(
                    ATTR_SPEED, default=current.get(ATTR_SPEED, DEFAULT_SPEED)
                ): vol.All(int, vol.Range(min=50, max=400)),
                vol.Optional(
                    ATTR_VOLUME, default=current.get(ATTR_VOLUME, DEFAULT_VOLUME)
                ): vol.All(int, vol.Range(min=50, max=200)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
