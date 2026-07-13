"""Tests for the VoiceText API client."""
import asyncio

import pytest

from custom_components.voicetext_tts.api import split_text
from custom_components.voicetext_tts.const import MAX_CHARS_PER_CHUNK


def test_split_text_short_text_returns_single_chunk():
    text = "こんにちは"
    assert split_text(text) == [text]


def test_split_text_empty_string_returns_empty_list():
    assert split_text("") == []


def test_split_text_splits_long_text_without_exceeding_limit():
    text = "あ" * 500
    chunks = split_text(text)
    assert len(chunks) == 3
    assert all(len(chunk) <= MAX_CHARS_PER_CHUNK for chunk in chunks)
    assert "".join(chunks) == text


def test_split_text_prefers_sentence_boundary():
    # Two sentences that together exceed the limit; each sentence alone fits.
    first_sentence = "あ" * 150 + "。"
    second_sentence = "い" * 100 + "。"
    text = first_sentence + second_sentence
    chunks = split_text(text)
    assert chunks[0] == first_sentence
    assert chunks[1] == second_sentence
    assert all(len(chunk) <= MAX_CHARS_PER_CHUNK for chunk in chunks)


def test_split_text_hard_cuts_when_no_punctuation_found():
    text = "あ" * 250  # no punctuation anywhere
    chunks = split_text(text)
    assert len(chunks) == 2
    assert len(chunks[0]) == MAX_CHARS_PER_CHUNK
    assert len(chunks[1]) == 50


from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.voicetext_tts.api import (
    VoiceTextAPIError,
    VoiceTextAuthError,
    VoiceTextTextTooLongError,
    VoiceTextTimeoutError,
    synthesize,
)
from custom_components.voicetext_tts.const import MAX_CHARS_PER_CHUNK, MAX_CHUNKS


def _mock_session(status: int = 200, body: bytes = b"AUDIO", text: str = "error body"):
    response = MagicMock()
    response.status = status
    response.read = AsyncMock(return_value=body)
    response.text = AsyncMock(return_value=text)

    class _CtxMgr:
        async def __aenter__(self_inner):
            return response

        async def __aexit__(self_inner, *args):
            return False

    session = MagicMock()
    session.post = MagicMock(return_value=_CtxMgr())
    return session, response


@pytest.mark.asyncio
async def test_synthesize_short_text_makes_one_call():
    session, response = _mock_session(status=200, body=b"AUDIO_BYTES")
    result = await synthesize(session, "fake-key", "こんにちは", "hikari")
    assert result == b"AUDIO_BYTES"
    assert session.post.call_count == 1


@pytest.mark.asyncio
async def test_synthesize_long_text_concatenates_chunks():
    session, response = _mock_session(status=200, body=b"CHUNK")
    text = "あ" * 300
    result = await synthesize(session, "fake-key", text, "hikari")
    assert session.post.call_count == 2
    assert result == b"CHUNKCHUNK"


@pytest.mark.asyncio
async def test_synthesize_raises_auth_error_on_401():
    session, response = _mock_session(status=401)
    with pytest.raises(VoiceTextAuthError):
        await synthesize(session, "bad-key", "こんにちは", "hikari")


@pytest.mark.asyncio
async def test_synthesize_raises_api_error_on_403_with_raw_body():
    session, response = _mock_session(status=403, text="plan limit exceeded")
    with pytest.raises(VoiceTextAPIError) as exc_info:
        await synthesize(session, "fake-key", "こんにちは", "hikari")
    assert exc_info.value.status == 403
    assert "plan limit exceeded" in str(exc_info.value)
    assert "fake-key" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_synthesize_raises_timeout_error():
    session = MagicMock()

    class _RaisingCtxMgr:
        async def __aenter__(self_inner):
            raise asyncio.TimeoutError()

        async def __aexit__(self_inner, *args):
            return False

    session.post = MagicMock(return_value=_RaisingCtxMgr())
    with pytest.raises(VoiceTextTimeoutError):
        await synthesize(session, "fake-key", "こんにちは", "hikari")


@pytest.mark.asyncio
async def test_synthesize_raises_text_too_long_error():
    session, response = _mock_session(status=200, body=b"CHUNK")
    text = "あ" * (MAX_CHARS_PER_CHUNK * (MAX_CHUNKS + 1))
    with pytest.raises(VoiceTextTextTooLongError):
        await synthesize(session, "fake-key", text, "hikari")
    assert session.post.call_count == 0


@pytest.mark.asyncio
async def test_synthesize_show_speaker_drops_emotion_silently():
    session, response = _mock_session(status=200, body=b"AUDIO")
    await synthesize(session, "fake-key", "こんにちは", "show", emotion="happiness")
    _, kwargs = session.post.call_args
    assert "emotion" not in kwargs["data"]


@pytest.mark.asyncio
async def test_synthesize_haruka_speaker_includes_emotion():
    session, response = _mock_session(status=200, body=b"AUDIO")
    await synthesize(session, "fake-key", "こんにちは", "haruka", emotion="happiness")
    _, kwargs = session.post.call_args
    assert kwargs["data"]["emotion"] == "happiness"
