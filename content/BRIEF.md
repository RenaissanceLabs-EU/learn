# Learn · content brief

Site: **Renaissance Labs · Learn** (learn.renaissancelabs.eu). A calm, beautiful library that combines our explainer films
with written lessons on how large language models are trained, plus a section on human minds (psychology).
Audience: curious adults and builders, no prior knowledge assumed, but never talked down to.

## Voice
- Plain, concrete, warm. Short sentences mixed with longer ones. Explain a term the first time you use it.
- No hype, no marketing words, no emojis, no exclamation marks. Do not use: delve, crucial, pivotal, landscape, tapestry, "it's important to note", "in today's world", "game-changer".
- Avoid em dashes. Use commas, periods or parentheses. Avoid lists of exactly three adjectives, and avoid "not just X, but Y" constructions.
- Prefer one good concrete example or number over three vague claims. Use analogies sparingly and only when they are exact.
- Psychology films: person-first, practical, light on citations, no disclaimers, no diagnosing the reader.

## Facts and numbers (strict)
- Use only numbers and claims that appear in the source files you are given (script.json, research/DOSSIER.md, research/*.md) or that are textbook-stable.
- If something is an estimate or rule of thumb, say so in the sentence ("roughly", "a common rule of thumb").
- Never invent a paper, URL, person, quote or statistic. If unsure, leave it out.
- URLs in `sources` must come from the source files, or be one of these arXiv papers (IDs are verified):
  1706.03762 Attention Is All You Need; 2001.08361 Scaling Laws for Neural Language Models (Kaplan); 2203.15556 Chinchilla (Hoffmann);
  2005.14165 GPT-3; 2203.02155 InstructGPT; 2305.18290 DPO; 2106.09685 LoRA; 1508.07909 BPE (Sennrich); 2101.03961 Switch Transformer;
  2401.04088 Mixtral; 1909.08053 Megatron-LM; 1910.02054 ZeRO; 2205.14135 FlashAttention; 2501.12948 DeepSeek-R1; 2402.03300 DeepSeekMath (GRPO);
  2407.21783 Llama 3; 1503.02531 Distilling the Knowledge in a Neural Network; 1412.6980 Adam; 2305.13245 GQA; 2208.07339 LLM.int8();
  2110.14168 Training Verifiers to Solve Math Word Problems; 2406.17557 FineWeb; 2305.16264 Scaling Data-Constrained Language Models;
  2109.01652 FLAN; 2212.08073 Constitutional AI; 2306.05685 Judging LLM-as-a-Judge (MT-Bench); 2009.03300 MMLU; 2305.14314 QLoRA; 2309.06180 PagedAttention (vLLM);
  1706.03741 Deep RL from Human Preferences
  Format: `https://arxiv.org/abs/<id>`.

## Lesson file format  (content/lessons/<slug>.md)

Front matter, then Markdown-like body. Keep to 700 to 1100 words in the body. Start straight in; no title heading (the title is in front matter).

```
---
title: Tokens: how text becomes numbers
slug: tokens
part: The basics          # one of: The basics | Feeding the model | The machine room | After pre-training
order: 2                  # position within the whole course, 1 to 16
level: Beginner           # Beginner | Intermediate | Advanced
minutes: 7
summary: One or two sentences (max 200 characters) shown on cards and in search results.
films: frontier-training:data, open-models:data      # film-id:scene-id pairs from the film's script.json; optional
related: what-is-a-language-model, pretraining-data  # lesson slugs; optional
widget: tokenizer                                     # optional, see below; also place it in the body with :::widget
sources:
- Attention Is All You Need | https://arxiv.org/abs/1706.03762
---
Body…
```

Body syntax (everything else is plain paragraphs):
- `## Heading` and `### Heading`. Use 3 to 6 `##` sections. Section headings are short and concrete, not clever.
- Paragraphs, `- ` bullet lists, `1. ` numbered lists.
- Inline: `**bold**`, `*italic*`, `` `code` ``, `[text](url)`. Link other lessons as `[Tokens](/lessons/tokens/)`.
- Callout (use at most 2 per lesson): 
  ```
  :::callout Key idea
  One or two sentences.
  :::
  ```
- Flow diagram (steps left to right, wraps on small screens): one step per line `Title | short caption`.
  ```
  :::flow
  Raw text | Pages, books and code
  Tokenizer | Splits text into pieces
  :::
  ```
- Big numbers: `:::stats` with lines `value | label`.
- Bars: `:::bars Title` with lines `label | number | note` (numbers are compared on one scale, same unit).
- Compare two or three options side by side:
  ```
  :::compare
  ## Data parallel
  - Every GPU holds a full copy
  - Splits the batch
  ## Tensor parallel
  - Splits each matrix
  :::
  ```
- Worked example in a fixed-width box: `:::example Title` then plain lines.
- Widget placeholder (interactive, built by us): `:::widget tokenizer` with names: `tokenizer`, `attention`, `scaling`, `memory`, `temperature`. Only use the one named in your assignment.
- Terms: the first time you define a term, write it as **term**. These feed a glossary.

Every lesson ends with a short `## Where to go next` section (2 to 3 sentences) pointing to the related lessons and, where relevant, the film chapters (just name them; links are generated from `films:`).

## Film file format  (content/films/<id>.json)

One JSON file per film, written from the film's `script.json`, `research/*.md` and `research/YOUTUBE_DESCRIPTION.md` under /Users/birger/RenaissanceLabs/<folder>/.

```
{
  "id": "frontier-training",                   // folder name without "-video"
  "title": "What it takes to train a frontier model",   // clean title case-sentence, no clickbait, max 60 chars
  "kicker": "Data, chips, failures and cost",  // max 50 chars, shown under title on cards
  "track": "machines",                         // machines | minds | bridge
  "theme": "training",                         // see lists below
  "blurb": "One sentence, max 150 characters, for cards.",
  "description": "Two or three sentences, max 70 words, for the film page.",
  "takeaways": ["3 to 5 short takeaways, max 24 words each, each a full sentence"],
  "chapters": [{"scene": "hook", "title": "Intro"}, …],  // exactly one entry per scene id, in script order, titles max 5 words
  "lessons": ["tokens", "pretraining-data"],   // machines/bridge only: lesson slugs from the course list below; may be empty
  "sources": [{"title": "…", "url": "…"}],     // only what the source files contain; may be empty for psychology films
  "level": "Beginner"                          // Beginner | Intermediate | Advanced
}
```
Themes. machines: `training`, `hardware`, `open-ecosystem`, `safety`. minds: `memory-time`, `fear-shame`, `connection`, `recovery`. bridge: `mind-machine`.
The final scene is usually `sources` or `close`; title it "Sources" or "Closing" accordingly.

## Course list (lesson slugs)
1 what-is-a-language-model · 2 tokens · 3 attention-and-the-transformer · 4 how-a-model-learns ·
5 pretraining-data · 6 scaling-laws · 7 parameters-precision-and-memory ·
8 gpus-and-parallelism · 9 mixture-of-experts · 10 when-training-breaks ·
11 supervised-fine-tuning · 12 preference-tuning-and-rl · 13 evaluation · 14 distillation-and-quantization · 15 inference-and-sampling · 16 what-open-means

## Source material for LLM lessons
Our own films and their verified research, under /Users/birger/RenaissanceLabs/:
- frontier-training-video/research/DOSSIER.md (data, scaling, chips, parallelism, failures, MoE, post-training, eval, cost; 2026 sources)
- gpu-hardware-video/research/*.md (GPU execution, roofline, precision formats, FP8, NVFP4, block scales)
- open-models-video/research/DOSSIER.md (strongest open models, MoE, KV cache, attention variants, RL)
- inkling-video/research/DOSSIER.md and TRAINING_PLAN.md (a concrete large training run, 4-bit training, RL, cost)
- cluster-agents-video/research/DOSSIER.md (RL rollouts, sandboxes)
- each film's script.json (the narration text, scene by scene)
Do not copy sentences from them verbatim; rewrite for reading. Textbook material you know well (what a gradient is, what softmax does) is fine.
