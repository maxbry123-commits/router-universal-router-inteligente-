# Qwen Audio TTS — API Supplementary Guide

> **Content validity**: 2026-03 | **Sources**: [TTS API](https://docs.qwencloud.com/api-reference/speech-synthesis/qwen-tts) · [TTS Guide](https://docs.qwencloud.com/developer-guides/speech/tts) · [Voice List](https://docs.qwencloud.com/api-reference/speech-synthesis/voice-list)

---

## Definition

Text-to-speech synthesis service that produces natural, human-like voices. Supports system voices, multiple languages, streaming real-time playback, **natural language instruction control** for tone and emotion, and custom voices via **voice cloning** (from audio samples) and **voice design** (from text descriptions). Instruction-control availability and limits are model-specific; check the CDN model catalog before using `instructions`.

---

## Use Cases

> **🚫 CRITICAL — Never override user-specified parameters.** If the user explicitly specifies a model (e.g. `qwen-audio-3.0-tts-plus`), voice, or any parameter, you MUST use it exactly as given. Do NOT:
> - Replace the model with a "better suited" one (e.g. switching to `qwen3-tts-instruct-flash` for audiobooks/poetic/stylized text)
> - Add `instructions`, `optimize_instructions`, or `language_type` the user did not ask for
> - Rewrite the user's `text` (beyond necessary URL/file reference conversion)
>
> The model guidance below applies **only when the user has NOT specified a model**.

Fetch and read the current [QwenCloud audio TTS model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-audio-tts-models.md) for scenario recommendations, defaults, compatibility, and basic model information. If CDN access fails, use the [local fallback](../cdn/references/qwencloud-audio-tts-models.md).

---

## Key Usage

### Non-streaming Synthesis

```python
import os, dashscope

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

resp = dashscope.MultiModalConversation.call(
    model="qwen3-tts-flash",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    text="Today is a wonderful day to build something people love!",
    voice="Cherry",
    language_type="English",
)
print(resp.output.audio.url)  # Audio URL, valid for 24 hours
```

### Streaming Synthesis (real-time playback)

The Qwen3-TTS API supports this SSE mode. The bundled `scripts/tts.py` HTTP path is non-streaming, so use this direct API/SDK pattern (or the curl example in `execution-guide.md`) when streaming chunks are required.

```python
resp = dashscope.MultiModalConversation.call(
    model="qwen3-tts-flash",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    text="Today is a wonderful day to build something people love!",
    voice="Cherry",
    language_type="English",
    stream=True,
)
for chunk in resp:  # Each chunk contains Base64-encoded audio data
    print(chunk)
```

### Instruction Control

Use natural language to describe the desired speech style. Before using the following API shape, verify `instructions` compatibility for the selected model in the CDN catalog linked above:

```python
resp = dashscope.MultiModalConversation.call(
    model="qwen3-tts-instruct-flash",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    text="Welcome to our grand opening! We have amazing deals waiting for you!",
    voice="Cherry",
    instructions="Fast speech rate, with a clear rising intonation, suitable for introducing fashion products.",
    optimize_instructions=True,
)
```

### System Voice List

Fetch the CDN model catalog linked above for the current voice list, descriptions, language support,
and model compatibility.

### Voice Cloning (quick example)

```python
import requests

# Step 1: Upload audio sample and create a voice
url = "https://dashscope-intl.aliyuncs.com/api/v1/services/audio/tts/customization"
resp = requests.post(url,
    headers={"Authorization": f"Bearer {os.getenv('DASHSCOPE_API_KEY')}"},
    files={"file": open("voice_sample.mp3", "rb")},
    data={"model": "qwen-voice-enrollment", "target_model": "qwen3-tts-vc-2026-01-22",
          "action": "create", "preferred_name": "my_brand_voice"})
custom_voice = resp.json()["output"]["voice"]

# Step 2: Use the cloned voice for synthesis
resp = dashscope.MultiModalConversation.call(
    model="qwen3-tts-vc-2026-01-22",  # Must match target_model
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    text="Hello, this is a test with a cloned voice.",
    voice=custom_voice,
)
```

### Key Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `model` | Yes | Model ID. |
| `text` | Yes | Text to synthesize; fetch the CDN model catalog linked above for model-specific limits. |
| `voice` | Yes | System voice ID, or cloned/designed voice name. |
| `language_type` | No | Default: `Auto`. Specifying the exact language significantly improves synthesis quality over `Auto`. Supported: `Chinese`, `English`, `Japanese`, `Korean`, `French`, `German`, `Russian`, `Italian`, `Spanish`, `Portuguese`. **Do not add it on the user's behalf** — if the user didn't set it, either omit it or suggest setting it and let them decide. |
| `instructions` | No | Natural language instructions for speech control; fetch the CDN model catalog linked above for current model compatibility and limits. |
| `optimize_instructions` | No | When true, the system semantically enhances `instructions` for better naturalness. Requires `instructions` to be set. |
| `stream` | No | `false` = returns audio URL. `true` = streams Base64-encoded audio chunks. |

---

## Important Notes

1. **Audio URLs are valid for only 24 hours.** Download immediately after generation.
2. **Specifying `language_type` significantly outperforms `Auto`.** When the text is in a single language, setting the exact language improves pronunciation accuracy and naturalness. However, only set it when the user requested it — otherwise omit it or suggest it to the user.
3. **`instructions` support is model-specific.** Fetch the CDN model catalog linked above before using it.
4. **Voice cloning `target_model` must match the synthesis `model`.** Otherwise synthesis fails.
5. **`SpeechSynthesizer` has been unified to `MultiModalConversation`.** In the DashScope Python SDK, the old `SpeechSynthesizer` interface has been replaced by `MultiModalConversation`. Parameters are fully compatible; only the interface name needs to change.
6. **Model availability is region-specific.** The CDN catalog does not provide region coverage; verify it with `qwencloud models info <model>` or the official model documentation.
7. **Streaming via HTTP** requires the header `X-DashScope-SSE: enable`. The Java SDK uses the `streamCall` interface.
8. **Bundled-script boundary:** `scripts/tts.py` does not currently expose Qwen3-TTS SSE streaming; its HTTP path requests the non-streaming audio URL.

---

## FAQ

**Q: How do I choose between qwen3-tts-flash and qwen3-tts-instruct-flash?**
A: Fetch and read the current CDN model catalog linked above for recommendations and capability differences. If the user already specified a model, keep it regardless of what the text looks like.

**Q: How do I make synthesized speech sound more natural?**
A: (1) Set `language_type` to match the text language only if the user wants it; otherwise suggest it. (2) If the user explicitly asks for style control, check the CDN catalog and use `instructions` only with a compatible model. Do NOT switch the user's model just to apply these tips. (3) Enable `optimize_instructions=True` only when `instructions` is set and the selected model supports it.

**Q: What is the difference between voice cloning and voice design?**
A: Cloning (VC) replicates a voice from an audio sample — suitable for reproducing an existing voice. Design (VD) creates a new voice from a text description — suitable for designing brand voices from scratch.

**Q: What is the maximum text length per synthesis call?**
A: Model limits are listed in the CDN model catalog linked above. For longer text, split it into segments and concatenate the audio files.

**Q: How do I achieve real-time audio playback?**
A: Set `stream=True`. The Python SDK returns a generator; iterate over it to receive Base64-encoded audio chunks for decoding and playback.
