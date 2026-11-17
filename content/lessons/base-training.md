---
title: How a base model is trained, end to end
slug: base-training
part: End to end
order: 17
level: Intermediate
minutes: 18
summary: Every step from raw text to a base model, followed through one real model, the OpenEuroLLM 9B that sits under Agora, with interactive demos of the loss, the optimizer, the schedule and long context.
films: frontier-training:recipe, frontier-training:data, frontier-training:scaling, frontier-training:parallel
related: post-training, pretraining-data, scaling-laws, gpus-and-parallelism, how-a-model-learns
sources:
- OpenEuroLLM 9B 256K base model card (Prelude anneal300b) | https://huggingface.co/openeurollm/oellm-9b-256k-theta64m-prelude-anneal300b
- Agora 9B and its post-training record | https://huggingface.co/birgermoell/agora-9b-GGUF
- Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism | https://arxiv.org/abs/1909.08053
- Adam: A Method for Stochastic Optimization | https://arxiv.org/abs/1412.6980
- Training Compute-Optimal Large Language Models (Chinchilla) | https://arxiv.org/abs/2203.15556
- FlashAttention | https://arxiv.org/abs/2205.14135
- GQA: Training Generalized Multi-Query Transformer Models | https://arxiv.org/abs/2305.13245
---
A **base model** is what you get when a network has read an enormous amount of text and learned to predict what comes next. It is not yet an assistant. Ask it a question and it may continue with another question, because lists of questions are common in text. Everything that makes a model useful comes later, in [post-training](/lessons/post-training/). But the base model decides what is possible, so most of the cost, risk and engineering sits here.

This guide follows one real model all the way through: the **OpenEuroLLM 9B** base that [Agora 9B](https://huggingface.co/birgermoell/agora-9b-GGUF) was built on. We use it because its model card publishes the architecture, the training stages, the optimizer settings and the run's health in unusual detail. A caveat up front: the card documents the long-context continuation of the model in full, but describes the earlier pre-training only by name and size. Where we explain the general recipe, we say so. Where a number comes from the card, we say that too.

:::flow
Data | Choose and clean the text
Tokenizer | Text becomes numbers
Architecture | The shape of the network
Training loop | Predict, measure, adjust
Schedule | How fast to learn, and when
Scale-out | Spread it over many GPUs
Long context | Stretch the window
Check | Is the run healthy?
:::

:::stats
9B | parameters, 36 layers
262,144 | tokens in the vocabulary
~7.98B | tokens of long-context training
128 | AMD GPU dies on the LUMI supercomputer
:::

## Step 1: the data

A base model learns from whatever it reads, so the mix of text is the first and largest design decision. Quality, language balance and duplication all matter, and the [pretraining data lesson](/lessons/pretraining-data/) covers how that text is filtered.

For the long-context stages of this model, the card lists a frozen, token-proportional blend of 152 source prefixes (157 for the final stage), drawn from FinePDFs, DCLM, HPLT3, multilingual synthetic text, Nemotron material, MegaMath, StarCoder, PeS2o, arXiv and Wikipedia. It covers many European languages plus code and scientific text, and it is not uniform by language. The text is sorted into length-aware tiers so that very long documents are available when the context grows.

Two habits are worth copying. The mix is **frozen** before the run, so a result can be traced to a recipe. And it is described by proportion of tokens, not number of files, because a model feels the data in tokens.

## Step 2: tokens and architecture

The model cannot read letters. A **tokenizer** cuts text into pieces and maps each to a number (see [Tokens](/lessons/tokens/)). This model has a vocabulary of 262,144 pieces, large because it must cover dozens of languages efficiently. The two published cards give slightly different sizes for the later chat model (263,168); neither explains the difference.

The network is a Qwen3-compatible decoder-only transformer. The card gives the full shape:

:::compare
## The shape
- 36 layers, hidden size 4,096
- 32 attention heads, sharing 8 key-value groups (grouped-query attention)
- Head size 128; feed-forward size 12,288 with SwiGLU
## The details
- RMSNorm, with normalisation of queries and keys
- Input and output embeddings are separate (untied)
- BF16 weights, a 262,144-token position limit
:::

You can check that this adds up to about 9 billion parameters with arithmetic any reader can do:

:::example Counting parameters
embeddings: 262,144 × 4,096 = 1.07B, twice (input and output) = 2.15B
attention per layer: 4,096² (queries) + 2 × 4,096 × 1,024 (keys, values) + 4,096² (output) = 42M
feed-forward per layer: 3 × 4,096 × 12,288 = 151M
36 layers × (42M + 151M) = 6.95B
total = 6.95B + 2.15B = about 9.1B
:::

Because the vocabulary is so large, over a fifth of the parameters sit in the two embedding tables. That is a design trade: more tokens per word saved, in exchange for memory. The [attention lesson](/lessons/attention-and-the-transformer/) explains the layers themselves.

## Step 3: the training loop

Training is the same small cycle repeated for months of GPU time. Take a batch of text, run it forward through the network, measure how wrong the predictions were, and nudge every parameter slightly to be less wrong.

The measure of wrong is the **loss**: for each position, minus the logarithm of the probability the model gave to the token that actually came next. Try it:

:::widget nexttoken

A model that has learned nothing scores 12.48 on every token for this vocabulary. The last logged loss of this model's final run was 1.427. The card is careful to say that this is a run-health number, not a benchmark, because loss depends on the data mix and cannot be compared across models.

The nudge comes from the **gradient**, which says which direction in the model's billions of dimensions lowers the loss. The step is then scaled by the **learning rate**. The optimizer for this model is **Adam**, with the settings the card lists: beta1 0.9, beta2 0.95, weight decay 0.1, gradient clipping at 1.0. Clipping keeps one freak batch from throwing the model far off course. Below is a two-parameter version of the same process; try a learning rate that is too large.

:::widget gradient

The batch itself is concrete: a global batch of 64 sequences, each as long as the stage's context. At the 16K stage that is 64 × 16,384 = 1,048,576 tokens per step, and 953 steps gives 999,292,928 tokens, exactly the figure in the card.

## Step 4: the schedule

The learning rate is not constant. It starts at zero and rises over a **warm-up**, because early updates are noisy and large steps can wreck the network. Then it falls, smoothly, to a small final value. The long-context stage of this model used a cosine decay from 8e-6 to 8e-7 with about 5 percent warm-up.

:::widget schedule

The last part of training has a special role. When the learning rate is already small, the model settles into a good region, and many labs feed it their cleanest, highest-quality data at that point. This is called **annealing**. The checkpoint this model was derived from is named for it, `anneal300b`, and the card describes it as the annealed checkpoint at about 300B tokens, in contrast to the roughly 1T-token base of the earlier release. Annealing is a small share of the full run's compute, and labs often find it moves results more than its size suggests.

## Step 5: spreading the work over many GPUs

A 9B model trained in BF16 with Adam needs on the order of 16 bytes per parameter before activations (see [Parameters, precision and memory](/lessons/parameters-precision-and-memory/)), far more than one GPU holds. So the work is split. This run used 16 nodes with 128 AMD MI250X GPU dies at every production stage, with:

- **tensor parallelism** of 8: each big matrix is cut across 8 GPUs;
- **sequence parallelism**, which splits the activations of the layers that tensor parallelism leaves whole;
- **context parallelism** that grows with the context, to 16 at 256K: each GPU holds only a slice of the very long sequence;
- a micro-batch of 1 per step, **FlashAttention** to avoid materialising the full attention matrix, and selective recomputation to trade a little compute for a lot of memory.

The software is Megatron-Core, the descendant of the Megatron-LM paper. [GPUs and parallelism](/lessons/gpus-and-parallelism/) explains what each form of parallelism costs in communication.

## Step 6: stretching the context

A model trained on short text cannot use long text unless it is taught to. Doing it from the start would be wasteful, because attention cost grows steeply with length. So the usual route is a staged extension: finish most of the training short, then continue at longer lengths.

This model went through five stages, each longer than the last:

| Stage | Sequence length | RoPE theta | Tokens |
|---|---|---|---|
| 16K | 16,384 | 500,000 | 0.999B |
| 32K | 32,768 | 1,000,000 | 0.998B |
| 64K | 65,536 | 2,000,000 | 2.999B |
| 128K | 131,072 | 32,000,000 | 1.996B |
| 256K | 262,144 | 64,000,000 | 0.990B |

Position is encoded by **rotary embeddings**, which turn each pair of query and key dimensions by an angle proportional to the token's position. Each pair turns at its own speed, from fast ones that separate neighbours to slow ones that track distance. Raising the base value theta slows the rotations, so that at 256K tokens the slow pairs still carry usable information. Explore how the stages differ:

:::widget rope

The numbers matter less than the principle: the context window is not a property of the architecture alone. It is a trained skill, and each doubling needs both a new theta and data that actually contains long-range structure.

## Step 7: checking the run is healthy

Pre-training runs fail, and the best protection is to watch them closely. The card reports the 256K stage in the way an operator would: all 59 of 59 planned steps completed, the final checkpoint saved, zero skipped steps and zero NaN steps. It also reports that the first launch attempt died during cold startup with a communication timeout between GPUs, and that a fresh second start then ran the whole stage cleanly. That small detail is a good illustration of why [running on a cluster is a skill](/notes/theory-and-practice/): the model was never the problem.

To check that the long context really works, the card runs a deliberately small needle-in-a-haystack test in English and Swedish at every length from 16K to 256K, with control conditions. All 12 of 12 trials passed at each length. The card itself calls this a check of export and retrieval, not a stable estimate of quality, and that is the right way to read it.

Few-shot benchmarks tell you what the base model knows before any tuning. For this base, the post-training card lists Belebele reading comprehension at 0.737, Global-MMLU at 0.547, INCLUDE regional knowledge at 0.422 and MultiBLiMP grammar at 0.935. They are the starting line against which the next lesson's improvements are measured.

## What you have at the end, and what you do not

You have a network with a great deal of knowledge about language, code and the world, a long window, and no manners. It does not follow instructions reliably, it has no safety training, and it will continue any text in the style it finds. The card says so plainly: this is a base completion model, not instruction-tuned and not safety-aligned.

:::callout Key idea
Pre-training builds capability. It is expensive, mostly fixed once done, and shaped by the data, the architecture and the run's stability. Everything after it shapes behaviour, and costs a tiny fraction as much.
:::

## Where to go next

[Post-training, end to end](/lessons/post-training/) follows the same model through seven more steps, from a text predictor to Agora 9B, with about 1,250 GPU-hours in total. For the economics of choosing model and data size, read [Scaling laws](/lessons/scaling-laws/). The film chapters on the recipe, the data and parallelism show the same ideas at frontier scale.
