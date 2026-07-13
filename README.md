# VoiceText TTS for Home Assistant

Home Assistant custom_component that exposes [HOYA's VoiceText WebAPI](https://cloud.voicetext.jp/webapi/docs/api)
as a native `tts` platform entity, so any automation, script, or Assist
pipeline that calls `tts.speak` can use VoiceText's Japanese voices.

## Installation

This component is not published to HACS. Install by copying the
`custom_components/voicetext_tts/` directory to your Home Assistant
`config/custom_components/` directory (e.g. via `scp` to a Home Assistant OS
device), then restart Home Assistant.

## API key

You need a VoiceText WebAPI key from https://cloud.voicetext.jp/webapi.
New free registration has ended as of 2026; if you already have a key from
an existing VoiceText integration (e.g. a `google-home-voicetext-server`
deployment), reuse that key here — copy the value of `VOICETEXT_API_KEY`
from its `.env` file directly into the config flow's API key field. Do not
commit or log this value anywhere.

## Setup

1. Go to **Settings → Devices & Services → Add Integration**, search for
   "VoiceText TTS".
2. Enter your API key. The integration performs a small real API call to
   confirm the key works before saving.
3. Optionally, click **Configure** on the integration to change the default
   speaker, emotion level, pitch, speed, volume, and audio format
   (`mp3`/`ogg`/`wav`, default `mp3`). `wav` only supports messages under
   200 characters (VoiceText responses can't be chunk-concatenated for wav
   the way mp3/ogg can) — use `mp3` or `ogg` for longer text.

## Usage

Call the `tts.speak` service, targeting the `tts.voicetext_tts` entity (or
whichever entity_id Home Assistant assigned) and any `media_player` entity
(e.g. one exposed by the Google Cast integration):

```yaml
action: tts.speak
target:
  entity_id: tts.voicetext_tts
data:
  media_player_entity_id: media_player.speaker_googlenest_livingroom
  message: "こんにちは"
  options:
    speaker: haruka
    emotion: happiness
```

Available `speaker` values: `show`, `haruka`, `hikari`, `takeru`, `santa`,
`bear`. `emotion` (`happiness`/`anger`/`sadness`) only takes effect for
speakers other than `show`.

Text longer than 200 characters is automatically split into multiple
VoiceText API calls (up to 10 chunks / ~2000 characters) and the resulting
audio is concatenated into a single utterance.

## Scope

This component's only job is calling the VoiceText API and returning audio
bytes. Casting to a Google Home / Nest speaker is handled entirely by Home
Assistant's built-in Google Cast integration — no separate casting logic is
implemented here.
