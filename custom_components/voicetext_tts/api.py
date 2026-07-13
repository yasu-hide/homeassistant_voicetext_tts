"""VoiceText WebAPI client."""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from .const import (
    API_ENDPOINT,
    API_TIMEOUT_SECONDS,
    EMOTION_CAPABLE_SPEAKERS,
    MAX_CHARS_PER_CHUNK,
    MAX_CHUNKS,
    SINGLE_CHUNK_ONLY_FORMATS,
)

_LOGGER = logging.getLogger(__name__)

_SENTENCE_END_CHARS = "。！？"


class VoiceTextError(Exception):
    """Base error for VoiceText API failures."""


class VoiceTextAuthError(VoiceTextError):
    """Raised when the API key is rejected (HTTP 401)."""


class VoiceTextAPIError(VoiceTextError):
    """Raised for any other non-2xx VoiceText API response."""

    def __init__(self, status: int, body: str) -> None:
        """Store the raw status and body without any request details."""
        super().__init__(f"VoiceText API {status}: {body}")
        self.status = status
        self.body = body


class VoiceTextTimeoutError(VoiceTextError):
    """Raised when the VoiceText API does not respond in time."""


class VoiceTextConnectionError(VoiceTextError):
    """Raised when the VoiceText API cannot be reached (DNS, connection, TLS, ...)."""


class VoiceTextTextTooLongError(VoiceTextError):
    """Raised when the input text exceeds the configured chunk limit."""


class VoiceTextFormatRequiresSingleChunkError(VoiceTextError):
    """Raised when a format in SINGLE_CHUNK_ONLY_FORMATS is requested for text that splits into multiple chunks."""


def split_text(text: str) -> list[str]:
    """Split text into chunks of at most MAX_CHARS_PER_CHUNK characters.

    Prefers to cut at the last Japanese sentence-ending punctuation mark
    found within the current MAX_CHARS_PER_CHUNK-sized window. Falls back
    to a hard cut at the limit if no such punctuation is found in the
    window. Never returns a chunk longer than MAX_CHARS_PER_CHUNK.
    """
    if not text:
        return []
    if len(text) <= MAX_CHARS_PER_CHUNK:
        return [text]

    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= MAX_CHARS_PER_CHUNK:
            chunks.append(remaining)
            break
        window = remaining[:MAX_CHARS_PER_CHUNK]
        best_index = -1
        for punctuation in _SENTENCE_END_CHARS:
            index = window.rfind(punctuation)
            if index > best_index:
                best_index = index
        cut = best_index + 1 if best_index != -1 else MAX_CHARS_PER_CHUNK
        chunks.append(remaining[:cut])
        remaining = remaining[cut:]
    return chunks


async def _post_chunk(
    session: aiohttp.ClientSession,
    api_key: str,
    text: str,
    speaker: str,
    emotion: str | None,
    emotion_level: str,
    pitch: int,
    speed: int,
    volume: int,
    audio_format: str,
) -> bytes:
    """POST a single chunk (<=MAX_CHARS_PER_CHUNK chars) to VoiceText."""
    data = {
        "text": text,
        "speaker": speaker,
        "format": audio_format,
        "pitch": str(pitch),
        "speed": str(speed),
        "volume": str(volume),
    }
    if emotion and speaker in EMOTION_CAPABLE_SPEAKERS:
        data["emotion"] = emotion
        data["emotion_level"] = str(emotion_level)

    timeout = aiohttp.ClientTimeout(total=API_TIMEOUT_SECONDS)
    headers = {"Authorization": aiohttp.encode_basic_auth(api_key, "")}
    try:
        async with session.post(
            API_ENDPOINT,
            data=data,
            headers=headers,
            timeout=timeout,
        ) as response:
            if response.status == 401:
                raise VoiceTextAuthError("VoiceText API rejected the API key (401)")
            if response.status != 200:
                body = await response.text()
                raise VoiceTextAPIError(response.status, body)
            return await response.read()
    except asyncio.TimeoutError as err:
        raise VoiceTextTimeoutError(
            f"VoiceText API did not respond within {API_TIMEOUT_SECONDS}s"
        ) from err
    except aiohttp.ClientError as err:
        raise VoiceTextConnectionError(
            f"Could not connect to VoiceText API at {API_ENDPOINT}: {err}"
        ) from err


async def synthesize(
    session: aiohttp.ClientSession,
    api_key: str,
    text: str,
    speaker: str,
    emotion: str | None = None,
    emotion_level: str = "2",
    pitch: int = 100,
    speed: int = 100,
    volume: int = 100,
    audio_format: str = "mp3",
) -> bytes:
    """Synthesize speech for arbitrary-length text, returning combined audio bytes in the requested format.

    Splits text longer than MAX_CHARS_PER_CHUNK into multiple VoiceText API
    calls and concatenates the resulting audio bytes sequentially. If any
    chunk call fails, the whole synthesis fails (no partial playback).
    """
    chunks = split_text(text)
    if audio_format in SINGLE_CHUNK_ONLY_FORMATS and len(chunks) > 1:
        raise VoiceTextFormatRequiresSingleChunkError(
            f"'{audio_format}' cannot be used with text that splits into multiple "
            f"chunks (got {len(chunks)} chunks); use mp3 or ogg for text over "
            f"{MAX_CHARS_PER_CHUNK} characters"
        )
    if len(chunks) > MAX_CHUNKS:
        raise VoiceTextTextTooLongError(
            f"Text splits into {len(chunks)} chunks, exceeding the limit of {MAX_CHUNKS}"
        )

    audio_parts = []
    for chunk in chunks:
        audio_parts.append(
            await _post_chunk(
                session,
                api_key,
                chunk,
                speaker,
                emotion,
                emotion_level,
                pitch,
                speed,
                volume,
                audio_format,
            )
        )
    return b"".join(audio_parts)
