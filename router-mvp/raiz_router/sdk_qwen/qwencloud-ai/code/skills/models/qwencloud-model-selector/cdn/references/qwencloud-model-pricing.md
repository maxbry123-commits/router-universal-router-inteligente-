# QwenCloud Model Pricing

> Checked: 2026-09-18. Prices are in USD.
>
> This file records the billing structure published by QwenCloud. The official pricing source no longer exposes a complete model-by-model price table, so unverified model lists and inferred prices are intentionally omitted. For current model availability, use the domain catalogs and the exact Token Plan allowlists.

## PAYG billing units

| Workload | Billing unit | Source-backed rules |
|----------|--------------|---------------------|
| Text generation | Per 1 million tokens | Input and output are priced separately. Some models use input-length tiers. Thinking tokens count as output tokens. |
| Image generation | Per successfully generated output image; some editing models also charge per input image | Text-to-image has no input-image charge. Input-image billing is model-specific. Output pricing may vary by resolution. Failed images are not charged. |
| Video generation | Per second | Output video is charged by generated duration. Some models also charge input-video duration. Price may vary by resolution, mode, or aspect ratio. |
| Text to speech | Per 10,000 input characters | Output is not charged. |
| Speech to text | Per second of input audio | Output is not charged. Applies to realtime recognition and file transcription. |
| Speech to speech | Per 1 million tokens | Rates differ by modality. Conversation history is billed again as input on later turns. |
| Embedding and reranking | Per 1 million input tokens | Output is not charged. |

### Text-to-speech character counting

- One Chinese character, Japanese kanji, or Korean hanja counts as 2 characters.
- Letters, digits, punctuation, spaces, Japanese kana, and Korean letters count as 1 character.
- SSML tags are excluded; only their text content is counted.

### Discounts and optimization

- Text-generation Batch API input and output rates are 50% of realtime rates.
- Embedding and reranking models that support Batch API are billed at 50% of realtime input pricing.
- Cached input tokens may receive a model-specific discount.
- Batch and cache discounts cannot be combined on the same text-generation request.
- Failed API calls are not charged and do not consume free quota.

## Built-in tool fees

| Tool | Fee | Note |
|------|-----|------|
| Web Search | $10 per 1,000 calls | In addition to model token costs |
| Image Search | $8 per 1,000 calls | Text-to-image and image-to-image search |
| Web Extractor | Free | Limited time |
| Code Interpreter | Free | Limited time |

Function calling and MCP have no separate tool fee; their tool descriptions count as input tokens.

## Token Plan

Token Plan uses Credits rather than PAYG billing units. Credits consumed by a request are dynamic and depend on the model type, token usage, thinking mode, and tool calls. The exact supported-model catalogs are maintained in `qwencloud-token-plan-models.md`:

- Individual: 20 models.
- Team: 27 models, comprising all 20 Individual models plus 7 Team-only models.

### Individual

| Tier | Standard price | Current promotional price | 7-day limit | Concurrent agents |
|------|----------------|---------------------------|-------------|-------------------|
| Lite | $8/month | $6/month | 2,500 Credits | 1–2 |
| Essential | $16/month | $10/month | 5,625 Credits | 2–3 |
| Standard | $25/month | $18/month | 10,000 Credits | 3–4 |
| Pro | $80/month | $68/month | 40,000 Credits | 6–8 |
| Credit Pack | — | $15/pack/month | 20,000 Credits/pack; not subject to the 7-day limit | — |

### Team

| Seat or pack | Standard price | Current promotional price | Monthly quota |
|--------------|----------------|---------------------------|---------------|
| Standard Seat | $30/seat/month | $20/seat/month | 25,000 Credits/seat/month |
| Pro Seat | $100/seat/month | $75/seat/month | 100,000 Credits/seat/month |
| Max Seat | $200/seat/month | — | 250,000 Credits/seat/month |
| Credit Pack | $700/pack | — | 625,000 Credits/pack |

Promotions, free quotas, prices, and model availability can change. Verify them on the official pages before making a purchase or cost estimate, and do not assume that a user's free quota remains available.
