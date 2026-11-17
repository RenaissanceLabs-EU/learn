---
title: What "open" means for AI models
slug: what-open-means
part: After pre-training
order: 16
level: Beginner
minutes: 8
summary: "Open" can mean downloadable weights, public code, released data or a full training recipe. These are different things, with different freedoms, and few releases include all four.
films: open-models:boards, open-models:close
related: what-is-a-language-model, distillation-and-quantization, inference-and-sampling
sources:
- Llama 3 (a paper that accompanies an open-weights release) | https://arxiv.org/abs/2407.21783
- FineWeb (an open pre-training dataset and its recipe) | https://arxiv.org/abs/2406.17557
---
When a model is called "open", the word covers at least four separate things. Which one is meant changes what you are allowed to do, and what you can check for yourself.

Recall from [What a language model actually is](/lessons/what-is-a-language-model/) that a model, stored on disk, is a very large list of numbers. That is the starting point for the first kind of openness.

## Four things that can be open

:::compare
## Open weights
- The trained numbers can be downloaded
- You can run the model on your own hardware
- You can often fine-tune it
## Open code
- The code to run, and sometimes train, the model is published
- Lets others reproduce the setup
## Open data
- The training data, or exact recipes to rebuild it, is released
- Lets others inspect what the model learned from
## Open recipe
- The settings, stages and tricks of training are described
- Lets others repeat or improve the method
:::

**Open weights** is the most common meaning today. You get the finished model, not the process that made it. That is a lot: you can run it privately, change it with extra training, shrink it with the methods in [Distillation and quantization](/lessons/distillation-and-quantization/), and serve it yourself as described in [Inference and sampling](/lessons/inference-and-sampling/).

But you cannot rebuild it. Weights are like a compiled program: useful and modifiable, but they do not show you how they came to be. To reproduce a model you also need the training code, the settings and the data. A **training recipe** is the written account of how those fit together: the data mix, the stages, the optimiser settings and what went wrong along the way. Some labs publish detailed technical reports, others publish a few pages.

## Licences: what you may do

A downloadable file is not automatically free to use however you like. Each release comes with a **licence**, a legal document that sets the terms. In broad terms there are two families.

**Permissive licences** allow nearly any use, including commercial products, with few conditions, usually things like keeping a notice of the original authors. Well-known permissive licences such as MIT and Apache 2.0 appear on a number of recent open-weights models in our research notes.

**Custom or restricted licences** are written by the lab for its own model. They may allow broad use but add limits: on very large companies, on certain uses, on using the outputs to train other models, or on redistribution. Several current models carry a licence named after the lab or the model itself. The terms differ from one to the next, so read them rather than assume.

Two practical points. First, "can I download it?" and "can I build a business on it?" are different questions. Second, the licence on the weights is separate from the licence on the code, and either may differ from the terms on the data.

## Why data is the rarest part

Weights are comparatively easy to share. Data is hard, for reasons that are mostly practical and legal rather than technical.

- Training sets are drawn from web pages, books, code and other sources, each with its own owner and rules. Republishing them can create legal exposure.
- The data contains personal information and content that a lab may not want to redistribute.
- Data is a competitive advantage. A good mix of sources, filtered well, is much of what separates a strong model from a weak one.
- Some labs simply say little about it. In our open-models research, one recent large release lists its training data as not disclosed, even with Apache 2.0 weights.

Some projects do publish data. FineWeb, for example, is an open pre-training dataset released with a paper describing how it was built. These releases are valuable because they let other people check and reuse the work.

## What "open source AI" does and does not mean

In software, "open source" has a long-standing meaning: you can read the source, change it and share it. Applied to AI, the phrase gets stretched. A model with downloadable weights and a restrictive licence is often called open source in headlines, though it may not meet that bar. And a model can be inspectable in some ways and not in others.

:::callout Key idea
When you see "open", ask four questions: can I get the weights, the code, the data and the recipe, and under which licence? The answers are rarely all yes.
:::

## Why independent labs matter

If every capable model comes from a few companies, everyone else depends on their pricing, their policies and their decisions about what to keep available. Open releases change that in concrete ways: researchers can study how models work, companies can run models on their own servers with their own data, and a language or domain the big labs ignore can be served by someone who cares about it. Releasing data and recipes goes further, because it lets others check claims and build on the work instead of starting from zero.

If you want a map of who is doing this, the [Open Labs Atlas](https://labs.renaissancelabs.eu/) collects independent labs that release weights, code and data.

## Where to go next

If you want to see how strong open models are and how they are built, the open-models film chapters on the leaderboard and the closing summary go through the current picture. Then [What a language model actually is](/lessons/what-is-a-language-model/) is a good place to loop back and reread the basics with this vocabulary in mind.
