"""Constants for the VoiceText TTS integration."""

DOMAIN = "voicetext_tts"

CONF_API_KEY = "api_key"

SPEAKERS = ["show", "haruka", "hikari", "takeru", "santa", "bear"]
DEFAULT_SPEAKER = "hikari"

EMOTIONS = ["happiness", "anger", "sadness"]
EMOTION_CAPABLE_SPEAKERS = ["haruka", "hikari", "takeru", "santa", "bear"]

DEFAULT_EMOTION_LEVEL = 2
DEFAULT_PITCH = 100
DEFAULT_SPEED = 100
DEFAULT_VOLUME = 100

MAX_CHARS_PER_CHUNK = 200
MAX_CHUNKS = 10

API_ENDPOINT = "https://api.voicetext.jp/v1/tts"
API_TIMEOUT_SECONDS = 15

ATTR_SPEAKER = "speaker"
ATTR_EMOTION = "emotion"
ATTR_EMOTION_LEVEL = "emotion_level"
ATTR_PITCH = "pitch"
ATTR_SPEED = "speed"
ATTR_VOLUME = "volume"

SUPPORTED_OPTIONS = [
    ATTR_SPEAKER,
    ATTR_EMOTION,
    ATTR_EMOTION_LEVEL,
    ATTR_PITCH,
    ATTR_SPEED,
    ATTR_VOLUME,
]
