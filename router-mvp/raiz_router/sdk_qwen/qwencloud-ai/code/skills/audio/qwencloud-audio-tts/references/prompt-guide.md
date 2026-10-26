# Audio TTS — Prompt Guide

Techniques for optimizing TTS text input and voice instructions.

> **🚫 Never override user-specified parameters.** If the user specified a model, voice, or text, use them exactly as given. The instruction templates below are only for a model currently marked instruction-compatible in the CDN model catalog, and only when the user asks for style control. NEVER switch models or inject instructions on your own initiative.

## Text Formatting for Natural Speech

TTS quality is highly sensitive to punctuation and structure:

| Technique | Effect | Example |
|-----------|--------|---------|
| Commas | Short pause | `Hello, welcome to our event.` |
| Periods | Full stop | `Thank you. Let's begin.` |
| Ellipsis | Dramatic pause | `And the winner is... Team Alpha!` |
| Exclamation | Energy / emphasis | `This is incredible!` |
| Question mark | Rising intonation | `Are you ready?` |
| Short sentences | Clearer delivery | Break 100+ word paragraphs into 1–2 sentence chunks |

For mixed-language text, set `language_type: "Auto"`.

## Instruction Templates

> These templates apply ONLY when: (1) the user did NOT specify a model, AND (2) the user explicitly asks for a specific style/tone. Otherwise, do not add instructions.

Fetch and read the current [QwenCloud audio TTS model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-audio-tts-models.md) before choosing a model or instruction field. If CDN access fails, use the [local fallback](../cdn/references/qwencloud-audio-tts-models.md).

Use the instruction field documented for the selected model; do not interchange `instructions` and `instruction`.

| Scenario | Instructions |
|----------|-------------|
| News anchor | `Professional, authoritative tone. Clear enunciation, moderate pacing.` |
| Audiobook | `Warm, engaging narration. Varied pacing — slow for drama, faster for action.` |
| Children's story | `Cheerful, animated voice. Exaggerated intonation. Slow and playful.` |
| Product ad | `Confident enthusiasm. Dynamic pacing — measured start, building momentum. Emphasize product name.` |
| Meditation | `Very slow, soft, calm. Long pauses between sentences. Almost whispered.` |
| Tutorial | `Clear, patient, instructional. Moderate pace with brief pauses between steps.` |

General pattern:

```
Speak in a [emotion] tone with [speed] pacing. Use a [quality] voice,
as if [character/scenario]. [Additional: emphasis, pauses, accent].
```

## Voice Selection

Fetch the CDN model catalog linked above for the current voice list and model compatibility, then choose
a voice that matches the user's requested tone. Do not infer support for a voice that is absent from the catalog.
