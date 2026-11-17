---
title: Attention and the transformer
slug: attention-and-the-transformer
part: The basics
order: 3
level: Intermediate
minutes: 9
summary: Attention lets each token look back at earlier tokens and decide which ones matter. Stacked many times, it is the core of every modern language model.
films: open-models:kv, frontier-training:recipe
related: tokens, how-a-model-learns
widget: attention
sources:
- Attention Is All You Need | https://arxiv.org/abs/1706.03762
- FlashAttention | https://arxiv.org/abs/2205.14135
- GQA: Training Generalized Multi-Query Transformer Models | https://arxiv.org/abs/2305.13245
---
After [tokenization](/lessons/tokens/), a model holds a row of integer IDs. The **transformer**, introduced in the paper [Attention Is All You Need](https://arxiv.org/abs/1706.03762), is the machine that turns that row into a prediction for the next token. Its central idea is **attention**.

## Embeddings: a list of numbers per token

Each token ID is looked up in a table and replaced by a list of numbers called an **embedding**. These lists are learned during training. Tokens that are used in similar ways end up with similar lists. At this point each token still knows nothing about its neighbours: "bank" has the same embedding in "river bank" and "bank loan".

## Attention: which earlier words matter

Meaning depends on context. In "The trophy did not fit in the suitcase because it was too big", the word "it" refers to the trophy. To process "it", the model needs to look back and find "trophy".

Attention does exactly that. For each token, it scores every earlier token for relevance, turns the scores into weights that add up to one, and mixes the earlier tokens' information according to those weights. A token with a high weight contributes a lot; one with a low weight is nearly ignored.

Try it below. The sentence is fixed, and the weights are illustrative: they show the kind of pattern attention can learn, not numbers from a real model.

:::widget attention

## Query, key and value

The scoring uses three vectors made from each token's current representation, by three learned transformations.

- The **query** says what this token is looking for.
- The **key** says what this token offers to others.
- The **value** is the information it passes on if it is chosen.

A token's query is compared with the keys of earlier tokens. A good match gives a high score. The softmax function converts all the scores into weights, and the output is the weighted sum of the values. Nothing here is hand-written. The three transformations are learned like every other parameter.

:::callout Key idea
Attention is a learned, soft lookup. Each token asks a question, every earlier token advertises what it holds, and the best matches contribute most.
:::

## Many heads, many layers

One attention pattern is not enough. A sentence has grammar, reference, position and topic all at once. So the model runs many attention calculations side by side, called **heads**, each with its own learned transformations. One head might track the subject of a verb, another the closest noun. Their outputs are combined.

The whole block, attention followed by a small feed-forward network, is then **stacked** many times. The open models in our films have between 43 and 93 layers. Early layers tend to capture local patterns, later ones more abstract relationships. After the last layer, the final token's representation is turned into a probability for every token in the vocabulary.

:::flow
Tokens | Integer IDs from the tokenizer
Embeddings | A learned list of numbers each
Attention + feed-forward | Repeated in every layer
Output | A probability for each possible next token
:::

## Why attention replaced recurrence

Earlier language models, called recurrent networks, read a sentence one token at a time and carried a running summary forward. That has two problems. Training cannot be parallelised across positions, because step ten needs step nine. And information from far back gets squeezed through the summary and tends to fade.

Attention lets every position look at every earlier position directly, and all positions can be computed at the same moment. During training, when the whole text is known in advance, that suits GPUs well. This parallelism is a large part of why transformers could be scaled up so far.

:::compare
## Recurrent
- One token after another
- Past is compressed into a running summary
- Hard to use many chips at once
## Attention
- All positions at once during training
- Direct access to any earlier token
- Cost grows with context length
:::

## The cost of long context

Because every token attends to all earlier tokens, the work for a full sequence grows roughly with the square of its length in standard attention. Double the context and the attention work roughly quadruples. At generation time, the model also keeps the keys and values of every earlier token so it does not recompute them. This store is the **KV cache**, and at a million tokens it becomes a memory bottleneck.

Much recent engineering targets this. [FlashAttention](https://arxiv.org/abs/2205.14135) makes exact attention faster by organising memory access. Grouped-query attention ([GQA](https://arxiv.org/abs/2305.13245)) shares keys and values across heads to shrink the cache. Sliding windows limit how far back a layer looks: MiMo-V2.6-Pro uses a 128-token window in most layers. DeepSeek-V4 compresses its keys and values, and reports that at one million tokens its Pro model needs 27% of the compute and 10% of the cache of its predecessor.

:::stats
27% | of single-token compute, DeepSeek-V4-Pro vs V3.2 at 1M context
10% | of the KV cache, same comparison
:::

The open models film covers these variants in its KV cache chapter; the details are beyond this lesson.

## Where to go next

Next, [How a model learns](/lessons/how-a-model-learns/) explains how the learned transformations in every layer get their values. For attention variants and the KV cache at scale, watch the KV cache chapter of the open models film, and for the overall recipe, the second chapter of the frontier training film.
