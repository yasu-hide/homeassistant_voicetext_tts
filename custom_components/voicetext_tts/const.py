"""Constants for the VoiceText TTS integration."""

DOMAIN = "voicetext_tts"

CONF_API_KEY = "api_key"

SPEAKERS = ["show", "haruka", "hikari", "takeru", "santa", "bear"]
DEFAULT_SPEAKER = "hikari"

EMOTIONS = ["happiness", "anger", "sadness"]
EMOTION_CAPABLE_SPEAKERS = ["haruka", "hikari", "takeru", "santa", "bear"]

EMOTION_LEVELS = ["1", "2", "3", "4"]
DEFAULT_EMOTION_LEVEL = "2"
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
ATTR_FORMAT = "format"

AUDIO_FORMATS = ["mp3", "ogg", "wav"]
DEFAULT_AUDIO_FORMAT = "mp3"

# WAV's RIFF container isn't designed for sequential concatenation like mp3
# frames or Ogg's chained bitstreams are, so it can only be used for text
# that fits in a single VoiceText API call (no multi-chunk splitting).
SINGLE_CHUNK_ONLY_FORMATS = ["wav"]

SUPPORTED_OPTIONS = [
    ATTR_SPEAKER,
    ATTR_EMOTION,
    ATTR_EMOTION_LEVEL,
    ATTR_PITCH,
    ATTR_SPEED,
    ATTR_VOLUME,
]
