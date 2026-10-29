# QwenCloud Audio TTS Models

> Catalog checked: 2026-09-18. Only model families released on or after 2025-08-01 are included.

## Defaults

| Scope | Runtime default | Configured default voice | Protocol and availability |
|-------|-----------------|--------------------------|---------------------------|
| Overall | `qwen-audio-3.0-tts-plus` | `longanlingxin` after WebSocket voice mapping | WebSocket; Token Plan + PAYG |
| Qwen-Audio Flash | `qwen-audio-3.0-tts-flash` | `longanfengyue` after WebSocket voice mapping | WebSocket; PAYG-only |
| Qwen3-TTS HTTP | `qwen3-tts-flash` | `Cherry` | API: HTTP with optional SSE; bundled `tts.py`: non-streaming HTTP; PAYG-only |
| CosyVoice | `cosyvoice-v3-flash` | `longanyang` | WebSocket; PAYG-only |

The generic CLI default voice is `Cherry`. When the voice is omitted for a Qwen-Audio WebSocket model, the runtime selects that model's configured default voice. An explicitly supplied voice—including explicit `Cherry`—is passed through unchanged. Explicit model and voice selections are not replaced.

## Runtime model catalog

| Model | Use | Protocol | Plan scope |
|-------|-----|----------|------------|
| `qwen-audio-3.0-tts-plus` | **Default.** Quality-oriented speech synthesis | WebSocket | Token Plan + PAYG |
| `qwen-audio-3.0-tts-flash` | Low-latency speech synthesis | WebSocket | PAYG-only |
| `qwen3-tts-flash` | Multilingual synthesis | API: HTTP with optional SSE; bundled `tts.py`: non-streaming HTTP | PAYG-only |
| `qwen3-tts-instruct-flash` | Instruction-controlled tone, emotion, pace, and character | API: HTTP with optional SSE; bundled `tts.py`: non-streaming HTTP | PAYG-only |
| `qwen3-tts-vd-2026-01-26` | Voice Design from a text description, followed by synthesis | Customization + HTTP | PAYG-only |
| `qwen3-tts-vc-2026-01-22` | Voice Cloning from an audio sample, followed by synthesis | Customization + HTTP | PAYG-only |
| `cosyvoice-v3-flash` | Fast CosyVoice synthesis | WebSocket through DashScope SDK | PAYG-only |
| `cosyvoice-v3-plus` | Quality-oriented CosyVoice synthesis | WebSocket through DashScope SDK | PAYG-only |

The Qwen3-TTS voice reference also documents real-time aliases and dated snapshots released after the cutoff. They are not listed as runtime models here because the bundled runtime uses the HTTP Qwen3-TTS path rather than the real-time Qwen3-TTS WebSocket protocol.

Qwen3-TTS's HTTP API supports optional SSE streaming, but the bundled `scripts/tts.py` HTTP path currently makes a non-streaming request and returns/downloads the resulting audio URL. Use the direct SSE example in `references/execution-guide.md` when streaming chunks are required.

## Limits and request compatibility

- Qwen3-TTS HTTP models accept at most 600 characters of synthesis text per request.
- `qwen3-tts-instruct-flash` accepts `instructions` of at most 1,600 tokens, in Chinese or English only.
- Qwen3-TTS non-streaming output URLs expire after 24 hours.
- `language_type` applies to the Qwen3-TTS HTTP path. WebSocket models use their own model-specific parameters and voices.
- A cloned or designed voice must be synthesized with the same target model used to create it.

## Qwen-Audio system voices

Voices are model-specific and cannot be interchanged without verification.

| Model | Supported system voices |
|-------|-------------------------|
| `qwen-audio-3.0-tts-plus` | `longanlingxin`, `longanlufeng` |
| `qwen-audio-3.0-tts-flash` | `longanfengyue`, `longanyuanfei`, `longanlingxi`, `longanxiaoxin`, `longanhuan_v3.6`, `longjielidou_v3.6`, `longpaopao_v3.6`, `longhuohuo_v3.6`, `longchuanshu_v3.6`, `loongmary`, `loongeva_v3.6`, `loongjohn` |

Both Qwen-Audio models also provide model-specific base voices generated through voice cloning. Use the exact model prefix documented in the official voice list.

## Qwen3-TTS system voices

The unversioned aliases expose the following current voice sets. Language support is voice-specific, especially for dialect voices.

### `qwen3-tts-instruct-flash` (24)

`Cherry`, `Serena`, `Ethan`, `Chelsie`, `Momo`, `Vivian`, `Moon`, `Maia`, `Kai`, `Nofish`, `Bella`, `Eldric Sage`, `Mia`, `Mochi`, `Bellona`, `Vincent`, `Bunny`, `Neil`, `Elias`, `Arthur`, `Nini`, `Seren`, `Pip`, `Stella`

### `qwen3-tts-flash` (48)

All 24 voices above, plus `Jennifer`, `Ryan`, `Katerina`, `Aiden`, `Bodega`, `Sonrisa`, `Alek`, `Dolce`, `Sohee`, `Ono Anna`, `Lenn`, `Emilien`, `Andre`, `Radio Gol`, `Jada`, `Dylan`, `Li`, `Marcus`, `Roy`, `Peter`, `Sunny`, `Eric`, `Rocky`, and `Kiki`.

## CosyVoice system voices

| Model | Supported system voices |
|-------|-------------------------|
| `cosyvoice-v3-plus` | `longanyang`, `longanhuan` |
| `cosyvoice-v3-flash` | `longanyang`, `longanhuan`, `longhuhu_v3`, `longjielidou_v3`, `longshanshan_v3`, `longniuniu_v3`, `longanyue_v3`, `longshange_v3`, `longanmin_v3`, `longyingxiao_v3`, `longyingxun_v3`, `longyingtao_v3`, `longanyun_v3`, `longanwen_v3`, `longanli_v3`, `longanlang_v3`, `longyingmu_v3`, `longhua_v3`, `longwan_v3`, `longanzhi_v3`, `longanya_v3`, `longanqin_v3`, `longwanjun_v3`, `longyichen_v3`, `longlaobo_v3`, `longlaoyi_v3`, `longjiqi_v3`, `longhouge_v3`, `longdaiyu_v3`, `longanxuan_v3` |

All listed CosyVoice voices support SSML and timestamps. Instruction support is voice-specific:

- `cosyvoice-v3-plus`: `longanyang`, `longanhuan`.
- `cosyvoice-v3-flash`: `longanyang`, `longanhuan`, `longhuhu_v3`.

## Billing and Token Plan compatibility

- PAYG text-to-speech is billed per **10,000 input characters**; output is not charged.
- A Chinese character, Japanese kanji, or Korean hanja counts as 2 characters. Letters, digits, punctuation, spaces, Japanese kana, and Korean letters count as 1 character. SSML tags are excluded.
- The official `qwen-audio-3.0-tts-plus` model page currently lists **$0.20 per 10,000 characters** and an RPM limit of **180**.
- `qwen-audio-3.0-tts-plus` is the only speech-synthesis model in the current Token Plan Individual and Team exact allowlists.
- `qwen-audio-3.0-tts-flash`, Qwen3-TTS, and CosyVoice models require PAYG.
