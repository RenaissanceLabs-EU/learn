---
title: Inference and sampling
slug: inference-and-sampling
part: After pre-training
order: 15
level: Intermediate
minutes: 9
summary: How a trained model produces text: a fast reading phase, a slow one-token-at-a-time writing phase, a memory called the KV cache, and the sampling rules that pick each token.
films: open-models:kv, gpu-hardware-video:roofline
related: attention-and-the-transformer, distillation-and-quantization, parameters-precision-and-memory
widget: temperature
sources:
- Attention Is All You Need | https://arxiv.org/abs/1706.03762
- GQA: Training Generalized Multi-Query Transformer Models | https://arxiv.org/abs/2305.13245
- Efficient Memory Management for LLM Serving with PagedAttention | https://arxiv.org/abs/2309.06180
- FlashAttention | https://arxiv.org/abs/2205.14135
---
**Inference** means using a trained model to produce output. Training happens once, at great expense. Inference happens every time anyone sends a prompt, so its cost adds up, and the way it works shapes everything from response speed to price.

## Two phases: prefill and decode

Every request has two stages.

In **prefill**, the model reads your whole prompt at once. All the prompt's tokens can be processed in parallel, so the chip does large matrix multiplications and stays busy.

In **decode**, the model writes its answer one token at a time. Each new token needs a full pass through the network, and it cannot start until the previous token exists.

:::flow
Prompt arrives | Thousands of tokens at once
Prefill | Parallel, compute-heavy
Decode | One token per pass, repeated
Stop | End token or length limit
:::

## Why decoding is limited by memory bandwidth

During decode, each pass reads essentially every active weight from memory to produce a single token. That is a lot of data moved for very little arithmetic. In BF16, each weight takes two bytes and contributes roughly one multiply and one add, so you get about one operation per byte moved.

Compare that with what a chip can do. Our GPU research lists the H100 at about 3.35 TB/s of memory bandwidth and about 989 TFLOPS of dense BF16 compute, which is several hundred operations available per byte. A single stream of decoding uses a tiny fraction of that. The chip is waiting for memory, not for arithmetic. This is the idea of the **roofline** in the GPU hardware film: for decoding, the memory roof is the one you hit first.

It also explains why [Distillation and quantization](/lessons/distillation-and-quantization/) help speed as well as size. Fewer bytes per weight means less to read per token.

## The KV cache

Attention (see [Attention and the transformer](/lessons/attention-and-the-transformer/)) compares each new token against every earlier token. Recomputing the keys and values for all earlier tokens at each step would waste enormous effort. So the model stores them: a **KV cache** holds the key and value vectors of every token already processed.

The cache grows by one entry per token, in every layer. A rough size per token is:

`2 × layers × KV heads × head size × bytes per number`

:::example A rough illustration
Take a model with 62 layers and 16 KV heads (the shape our research lists for one large open model), and assume a head size of 64 and BF16 storage. That gives about 250 KB per token, so a 1-million-token context would need on the order of 250 GB for one conversation.
This is an estimate from an assumed head size, but it shows why long context is a memory problem.
:::

The cache is also why designs differ. Grouping query heads so they share KV heads (GQA) shrinks it. Our open-models research describes DeepSeek V4 compressing the cache further: at 1 million tokens it needs about 10% of the cache of its predecessor, and one later variant stores about 890 bytes per token in fast memory.

:::stats
2 | numbers stored per token per layer: a key and a value
10% | of the previous model's cache, DeepSeek V4 Pro at 1M tokens
890 B | per token in fast memory for V4.1 Flash
:::

## Batching and speculation

Since decoding wastes compute, servers run many requests together. With **batching**, one read of the weights serves every request in the batch, so the cost per token falls. The limit is the KV cache: each request needs its own, and memory fills up. Serving systems such as vLLM, built around the PagedAttention paper, manage that memory in blocks to fit more requests.

**Speculative decoding** uses a small, fast model to guess several tokens ahead, then lets the large model check all of them in one pass. If the guesses are right, several tokens arrive for the price of one large pass; if not, the wrong ones are discarded, and the output is the same as the large model alone would have produced.

## Sampling: choosing the next token

The model's output is a probability for every token. A **sampling** rule turns that into a choice.

- **Greedy** always takes the most likely token. It is predictable and can be repetitive.
- **Temperature** rescales the probabilities before choosing. Below 1 the distribution sharpens toward the top choice. Above 1 it flattens, so unlikely tokens get a real chance. Temperature near 0 behaves like greedy.
- **Top-k** keeps only the k most likely tokens and samples among them.
- **Top-p** (nucleus sampling) keeps the smallest set of tokens whose probabilities add up to p, then samples among them. The set is small when the model is confident and larger when it is unsure.

Try it below. The numbers are made up for illustration: a single invented next-token distribution for one prompt.

:::widget temperature

:::callout Key idea
Sampling does not change what the model knows. It changes how willing the model is to say something other than its first choice.
:::

## Where to go next

Next, [What open means](/lessons/what-open-means/) looks at who is allowed to download and run these models themselves. For the memory side of the story, the open-models film chapter on the KV cache and the GPU film's roofline chapter cover the same ideas on screen.
