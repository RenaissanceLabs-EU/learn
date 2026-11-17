---
title: Scaling laws: how big, how long
slug: scaling-laws
part: Feeding the model
order: 6
level: Intermediate
minutes: 9
summary: Loss falls smoothly as parameters, data and compute grow. Scaling laws turn that into a budgeting tool, and also show where the tool stops working.
films: frontier-training:scaling, inkling:compute
related: pretraining-data, parameters-precision-and-memory, mixture-of-experts
widget: scaling
sources:
- Scaling Laws for Neural Language Models (Kaplan et al.) | https://arxiv.org/abs/2001.08361
- Training Compute-Optimal Large Language Models (Chinchilla) | https://arxiv.org/abs/2203.15556
- Scaling Data-Constrained Language Models | https://arxiv.org/abs/2305.16264
- Frontier training dossier (GLM-5, DeepSeek-V4 reports, 2026) | https://arxiv.org/abs/2602.15763
- Inkling 2 Small announcement, Thinking Machines | https://thinkingmachines.ai/news/inkling-2-small/
---
Before a lab spends months and tens of millions of dollars on a training run, it has to answer two questions. How many parameters should the model have? And how much text should it read? Guessing wrong in either direction wastes money. **Scaling laws** are the empirical rules that make the guess an informed one.

## Loss falls on a smooth curve

During training a model is scored by its **loss**, a number that measures how badly it predicts the next token (lower is better). In 2020, [Kaplan and colleagues](https://arxiv.org/abs/2001.08361) trained many models of different sizes and found something tidy. Loss followed a **power law** in three quantities: the number of parameters, the amount of training data, and the amount of compute. Plotted on log axes, the results fell close to a straight line over many orders of magnitude.

The practical meaning is that progress is predictable. Train a few small models, fit the line, and you can forecast the loss of a model a hundred times larger before you build it.

:::callout Key idea
Scaling laws predict loss, a smooth number. They do not predict which abilities appear at a given loss. That gap is where most of the surprises, and most of the misuse, live.
:::

## Kaplan versus Chinchilla

Given a fixed compute budget, you can spend it on a bigger model trained briefly or a smaller model trained longer. Kaplan's analysis leaned toward bigger models. In 2022 the [Chinchilla paper](https://arxiv.org/abs/2203.15556) re-ran the experiment more carefully and reached a different answer: parameters and tokens should grow together. Their 70-billion-parameter model, trained on about 1.4 trillion tokens, beat much larger models that had seen less data.

Two rules of thumb come out of that work:

- Training compute **C** is roughly 6 times the parameters **N** times the tokens **D**, so C is about 6ND.
- The compute-optimal choice is roughly 20 tokens per parameter, so D is about 20N.

Both are rough. The factor 6 counts the arithmetic of a forward and backward pass, and the 20 is a fitted result, not a law of nature.

:::example A worked budget
Suppose you have C = 10^24 floating-point operations.
D = 20N, so C = 6 x N x 20N = 120 N^2.
N = square root of (10^24 / 120), about 91 billion parameters.
D = 20 x N, about 1.8 trillion tokens.
:::

The widget below lets you move the budget and watch both numbers change.

:::widget scaling

## Why real models break the rule

Modern models are trained far beyond 20 tokens per parameter. The reason is that training is paid once, while a model is used for months by many people. A smaller model trained on more data reaches the same quality at a lower cost per answer, so labs accept extra training compute to save inference compute. This is called **over-training**.

The 2026 reports show how far it goes. Using the 6ND rule on active parameters, the frontier training dossier derives these ratios:

:::bars Tokens seen per active parameter (derived)
GLM-5 | 710 | 28.5T tokens, 40B active
DeepSeek-V4 Pro | 670 | about 33T tokens, 49B active
DeepSeek-V4 Flash | 2460 | about 32T tokens, 13B active
Chinchilla rule | 20 | compute-optimal for training alone
:::

Applied the same way, GLM-5 comes to roughly 7 x 10^24 operations and V4 Pro close to 10^25. The Inkling 2 Small announcement reports 8.4 trillion tokens for its first pre-training phase and more than 4 x 10^23 operations for its joint RL run. Those are reported figures, not rules.

## Active versus total parameters

For a **mixture of experts** model, only some parameters run for each token (see [Mixture of experts](/lessons/mixture-of-experts/)). The 6ND rule should then use **active** parameters, because those set the arithmetic per token. GLM-5 has 744 billion parameters in total but 40 billion active. DeepSeek-V4 Pro has 1.6 trillion in total and 49 billion active. Total parameters still matter for memory and for how much the model can store, which is why the two numbers are always quoted together.

## Data is a limit too

Chinchilla-style budgets assume there is enough fresh text. There may not be. The paper on [data-constrained scaling](https://arxiv.org/abs/2305.16264) studied what happens when data is repeated across several passes. Repeating text a few times is nearly as good as new text, but returns fade as repetition grows. That pushes labs toward better filtering, synthetic data and code, as covered in [Pretraining data](/lessons/pretraining-data/).

## What scaling laws do not tell you

Three honest limits:

1. They fit loss on a given data mix. Change the data or the architecture and the curve moves.
2. Loss on text is not the same as skill at a task. A small drop in loss can coincide with a large jump in one ability and none in another.
3. They are extrapolations. The further you extend a fitted line past the models you trained, the less you should trust it.

Labs therefore use scaling laws to pick a size and then check the result on real benchmarks, not to promise a capability.

## Where to go next

[Parameters, precision and memory](/lessons/parameters-precision-and-memory/) turns parameter counts into bytes, and [Mixture of experts](/lessons/mixture-of-experts/) explains why active and total counts differ. The scaling chapter of the frontier training film walks through the same GLM-5 and DeepSeek-V4 numbers.
