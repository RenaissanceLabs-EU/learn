---
title: Mixture of experts
slug: mixture-of-experts
part: The machine room
order: 9
level: Intermediate
minutes: 8
summary: A mixture-of-experts model stores many specialist sub-networks but sends each token to only a few. It gets the capacity of a huge model at the arithmetic cost of a much smaller one.
films: frontier-training:moe, open-models:moe
related: scaling-laws, gpus-and-parallelism, parameters-precision-and-memory
sources:
- Switch Transformers | https://arxiv.org/abs/2101.03961
- Mixtral of Experts | https://arxiv.org/abs/2401.04088
- Frontier training dossier (GLM-5, DeepSeek-V4, Kimi K2.5, 2026) | https://arxiv.org/abs/2602.15763
- Inkling 2 Small announcement, Thinking Machines | https://thinkingmachines.ai/news/inkling-2-small/
---
Most of the largest 2026 models share one design choice. They are **mixtures of experts**, or MoE. Understanding it explains why their parameter counts come in two numbers.

## Dense and sparse

In a **dense** model, every parameter takes part in processing every token. Doubling the parameters roughly doubles the arithmetic per token.

In a **sparse** MoE model, the feed-forward part of each layer is replaced by many parallel sub-networks called **experts**. For each token, only a few experts run. The rest sit idle for that token. The attention layers stay shared, as in [the transformer](/lessons/attention-and-the-transformer/).

:::flow
Token arrives | One piece of text in a layer
Router | Scores every expert
Top experts | A few are chosen, such as 8
Combine | Their outputs are mixed by score
:::

## The router

The **router** is a small learned layer. It takes the token's representation and produces a score for each expert. The highest scores win, and the token is processed by those experts only. Some designs add **shared experts** that every token uses, alongside the routed ones. Nobody assigns topics to experts by hand; whatever specialisation appears emerges during training.

## Total and active parameters

Because only some experts run, MoE models quote two numbers. **Total parameters** count everything stored. **Active parameters** count what a single token actually uses.

:::stats
744B | GLM-5 total parameters, 40B active
1.6T | DeepSeek-V4 Pro total, 49B active
1.04T | Kimi K2.5 total, 32B active
594B | Inkling 2 Small total, 17B active
:::

Kimi K2.5 has 384 experts with 8 active per token. Inkling 2 Small also routes each token to 8 of 384 experts. Compute per token follows the active count, which is why training compute is estimated as about 6 times active parameters times tokens (see [Scaling laws](/lessons/scaling-laws/)).

## Why this gives more capability for the compute

A model's capacity to store knowledge grows with total parameters, while the cost of running it per token grows with active parameters. MoE separates the two. A model with 40 billion active parameters can hold 744 billion in total. A dense model that stored as much would cost many times more per token.

The Switch Transformer and Mixtral papers made this case early on: for a fixed compute budget per token, adding experts improved quality.

## The memory cost

The saving is in arithmetic, not storage. Every expert must be kept in memory, because any token may need any of them. GLM-5's 744 billion parameters still take about 1.5 TB in BF16, as covered in [Parameters, precision and memory](/lessons/parameters-precision-and-memory/). Lower precision helps: DeepSeek-V4 applies 4-bit quantization-aware training to its expert weights in post-training to cut serving memory.

:::compare
## Dense model
- All parameters active per token
- Memory and compute grow together
- Simple to balance across chips
## MoE model
- A few experts active per token
- Memory follows total, compute follows active
- Needs routing and load balancing
:::

## Load balancing and communication

If the router sends most tokens to a few favourite experts, those chips become bottlenecks and the other experts learn little. Training therefore includes **load balancing**. DeepSeek-V4 uses a balancing method without a classic auxiliary loss, plus a very small balance loss per sequence, according to the open models dossier.

Fragility is real. In one open-model study the dossier records, a trainable router let expert load collapse within about 20 steps during RL, and freezing the router kept the load flat. DeepSeek reports that loss spikes traced back to outliers in MoE layers, and that its stabilising tricks (anticipatory routing and clamping) work, though the principles are "insufficiently understood".

Then there is traffic. Experts live on different GPUs, so tokens must be shuffled to the right chip and back, an all-to-all exchange in every MoE layer. This is why expert parallelism, described in [GPUs and parallelism](/lessons/gpus-and-parallelism/), is a main design constraint for these models.

:::callout Key idea
MoE trades memory and communication for arithmetic. You pay to store and move more, and you get more capability per operation.
:::

## Where to go next

[Scaling laws](/lessons/scaling-laws/) explains how active parameters enter the compute budget, and [GPUs and parallelism](/lessons/gpus-and-parallelism/) shows how experts are spread across chips. The mixture-of-experts chapters of the frontier training film and the open models film show real configurations side by side.
