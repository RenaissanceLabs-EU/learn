---
title: How to work it out
---
Three things take memory: the weights, the cache for the context, and, in training, everything the optimizer keeps. Each one is a multiplication.

### The weights

:::example Weights
memory  =  parameters  x  bytes per parameter

A 9-billion-parameter model:
32-bit    4 bytes      36 GB
16-bit    2 bytes      18 GB
8-bit     1 byte        9 GB
4-bit     0.5 byte      4.5 GB, plus a little for the block scales
:::

### The cache for the context

While it writes, the model keeps a key and a value for every earlier token, in every layer. A rough size per token:

:::example Context cache
bytes per token  =  2  x  layers  x  KV heads  x  head size  x  bytes per number

Assume 36 layers, 8 KV heads, a head size of 128 and 16-bit numbers:
2 x 36 x 8 x 128 x 2  =  about 147 KB per token

A 32,768-token context:  about 4.8 GB, for one conversation
:::

The head count and head size here are assumptions for the example. Read the real ones from the model's config file. Every request served at the same time needs its own cache, so this number is multiplied by the number of users.

### Training

Training keeps much more per weight: the gradient, the optimizer's running averages, and often a full-precision copy of the weights. A common rule of thumb for mixed-precision training with Adam is about 16 bytes per parameter.

:::example Full fine-tuning
9 billion  x  16 bytes  =  144 GB, before activations
:::

That does not fit on one accelerator, which is why full-weight fine-tuning of a 9B model runs across several GPUs. Activations come on top and grow with batch size and sequence length. The rule is rough: real setups differ by optimizer and recipe.

### What fits where

| Accelerator | Memory |
| --- | --- |
| NVIDIA A100 | 40 or 80 GB |
| NVIDIA H100 | 80 GB |
| NVIDIA H200 | 141 GB |
| NVIDIA B200 | Up to 192 GB |
| AMD MI250X | 128 GB, as two dies of 64 GB |
| AMD MI300X | 192 GB |
| AMD MI325X | 256 GB |

A 9B model at 16 bits, with a 32K context, needs about 23 GB and fits on any of these. At 4 bits it fits in under 10 GB.

### How to shrink it

| Lever | What it shrinks | What it costs |
| --- | --- | --- |
| Fewer bits per weight | Weights | A small loss of accuracy, most at 4 bits |
| A distilled, smaller model | Weights and cache | The student does not match the teacher everywhere |
| Shared key and value heads | Cache | Decided in the design |
| Low-rank adapters | Training memory | Only a small set of added weights is trained |

### What to report

1. Parameters and bits per weight.
2. Context length used, and how many requests at once.
3. Peak memory measured, not only the calculated one.
4. Benchmark scores before and after any change in precision.

[Parameters, precision and memory](/lessons/parameters-precision-and-memory/) goes through the formats, and [Distillation and quantization](/lessons/distillation-and-quantization/) covers the two ways to shrink a model.
