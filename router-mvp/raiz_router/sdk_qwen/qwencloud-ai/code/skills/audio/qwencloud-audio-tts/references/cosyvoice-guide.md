# CosyVoice TTS Guide

CosyVoice models use **WebSocket API** (not HTTP REST), requiring the DashScope SDK.

## Models

Fetch and read the current [QwenCloud audio TTS model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-audio-tts-models.md) for the CosyVoice model list, defaults, instruction support, and voice compatibility. If CDN access fails, use the [local fallback](../cdn/references/qwencloud-audio-tts-models.md).

## Prerequisites

- **DashScope SDK** (venv recommended):
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate  # Windows: .venv\Scripts\activate
  pip install dashscope>=1.25.17
  ```
- **API Key**: Same as Qwen TTS (`DASHSCOPE_API_KEY` or `QWEN_API_KEY`) — must be a **standard PAYG key** (`sk-...`); Token Plan keys are rejected (see below)

## Token Plan Compatibility

Fetch and read the current [Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md) before selecting a model. If CDN access fails, use the [local fallback](../cdn/references/qwencloud-token-plan-models.md).

The bundled `tts_cosyvoice.py` currently rejects Token Plan keys (`sk-sp-...`) and exits immediately with:

```text
Error: cosyvoice models are not available on Token Plan.
Use tts.py with qwen-audio-3.0-tts-plus instead (Token Plan supported).
```

For Token Plan TTS, use `tts.py` with an exact model from the current Token Plan catalog. Never replace an explicitly requested model without the user's confirmation.

## Run Script

**Discovery:** `python3 <this-skill-dir>/scripts/tts_cosyvoice.py --help`

```bash
python3 scripts/tts_cosyvoice.py --text "Hello, world!"
```

| Argument | Description |
|----------|-------------|
| `--text`, `-t` | **Required** — text to synthesize |
| `--model`, `-m` | Model ID; fetch the CDN model catalog linked above for the current default |
| `--voice`, `-v` | Voice ID; fetch the CDN model catalog linked above for the current default |
| `--output`, `-o` | Output file (default: `output/qwencloud-audio-tts/cosyvoice.mp3`) |
| `--format`, `-f` | Audio format: mp3, wav, pcm (default: mp3) |
| `--sample-rate` | Sample rate in Hz: 8000/16000/22050/24000/44100/48000 (default: 24000) |
| `--instruction` | Free-style instruction for speech control; fetch the CDN model catalog for compatibility |
| `--language-hints` | Target language hint (e.g. `zh`, `en`) |

## Available Voices

Fetch the CDN model catalog linked above for the current verified voices, descriptions, defaults, and
model compatibility. See the [official voice list](https://docs.qwencloud.com/api-reference/speech-synthesis/voice-list)
for the authoritative full catalog.

The script validates the exact model/voice pair before connecting. When `--instruction` is supplied, it also requires that exact voice to be instruction-compatible for the selected model; model-level support alone is not sufficient.

## Examples

> Example model/voice choices below are demonstrations only. If the user explicitly specified a model or voice, use exactly their choice — do not switch to `cosyvoice-v3-plus` (or any other model) because the text "sounds like professional narration".

```bash
# Basic synthesis
python3 scripts/tts_cosyvoice.py -t "Hello, world!"

# Chinese with specific voice
python3 scripts/tts_cosyvoice.py -t "你好世界" -v longanhuan

# Explicit model example
python3 scripts/tts_cosyvoice.py -t "Professional narration" -m cosyvoice-v3-plus

# Instruction-guided style control (verify model compatibility in the CDN catalog)
python3 scripts/tts_cosyvoice.py -t "欢迎光临" --instruction "用热情洋溢的声音" --language-hints zh

# WAV output at 48 kHz
python3 scripts/tts_cosyvoice.py -t "Hello" -f wav --sample-rate 48000

# Multiple files (use --output to avoid overwriting)
python3 scripts/tts_cosyvoice.py -t "First sentence" -o output/qwencloud-audio-tts/part1.mp3
python3 scripts/tts_cosyvoice.py -t "Second sentence" -o output/qwencloud-audio-tts/part2.mp3
```

> **Tip**: Default output overwrites previous file. Use `-o` with different filenames for batch tasks.

## Error Handling

| Error Pattern | Resolution |
|---------------|------------|
| `dashscope SDK not installed` | Run `pip install dashscope>=1.25.17` |
| `cosyvoice models are not available on Token Plan` | Token Plan keys are rejected — use `tts.py` with an exact supported model from the Token Plan catalog, or a PAYG key |
| `WebSocket task failed: <code>: <message>` | Structured WebSocket error — check `error_code` / `error_message` (e.g. invalid API key, invalid voice, quota) |
| `WebSocket connection failed` | Check network; verify API key |
| `voice ... is not supported by model` | Select a voice listed for that exact CosyVoice model; Qwen TTS voices such as Cherry/Ethan are invalid here |
| `--instruction is not supported for voice` | Select an instruction-compatible voice for that exact model, or omit `--instruction` |

## Character Counting & Billing

CosyVoice models are billed per character. Fetch the [CDN model-pricing reference](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-pricing.md) for the current model list and billing units. If CDN access fails, use the [local fallback](../cdn/references/qwencloud-model-pricing.md).
