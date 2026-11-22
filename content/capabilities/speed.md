---
title: How to work it out
---
Speed is two numbers. **Time to first token** is the wait before anything appears. **Tokens per second** is how fast the answer then arrives. They have different causes, so report both.

### The time for one answer

:::example One reply
time  =  time to first token  +  output tokens / tokens per second

A 300-token answer at 50 tokens per second, after a 0.5 s wait:
0.5  +  300 / 50  =  6.5 seconds
:::

Time to first token grows with the length of the prompt, because the model reads the whole prompt before it writes. Tokens per second depends on the model and the hardware.

### A ceiling for tokens per second

To write one token, the model reads every active weight from memory once. So for a single request, memory bandwidth sets an upper limit:

:::example Ceiling for one request
tokens per second  <  memory bandwidth  /  size of the weights

A 9-billion-parameter model at 16 bits is 18 GB.
On an H100 (3,350 GB per second):   3,350 / 18  =  about 186
The same model at 4 bits is 4.5 GB:  3,350 / 4.5 =  about 744
:::

Real numbers are lower. The cache for the context is read as well, and there is work besides reading weights. The ceiling is still useful: it tells you what cannot happen, and it shows why smaller weights are faster.

| Accelerator | Memory bandwidth | Ceiling for 18 GB of weights |
| --- | --- | --- |
| NVIDIA A100, 80 GB | 2,039 GB/s | about 113 tokens/s |
| AMD MI250X | 3,200 GB/s | about 178 tokens/s |
| NVIDIA H100 | 3,350 GB/s | about 186 tokens/s |
| NVIDIA H200 | 4,800 GB/s | about 267 tokens/s |
| AMD MI300X | 5,300 GB/s | about 294 tokens/s |

### One user or many

A single request leaves most of the chip's arithmetic unused. Serving many requests in one batch reads the weights once for all of them, so the total tokens per second rises while each user sees about the same speed. The limit is memory: every request needs its own cache.

So there are two speeds to quote: **per request**, which is what a user feels, and **total throughput**, which is what the bill depends on.

### What changes it

| Lever | Effect |
| --- | --- |
| A smaller model, or fewer active parameters per token | Less to read per token |
| Fewer bits per weight | Less to read per token |
| Batching | More total throughput, same speed per request |
| Speculative decoding | Several tokens per pass of the large model, same output |
| A shorter prompt, or a cached one | Shorter wait for the first token |
| The serving engine | How well all of the above is used |

Training does not appear in the table. A fine-tuned model runs at the speed of its base.

### What to report

1. The accelerator and how many.
2. Bits per weight.
3. The serving engine and its version.
4. Prompt length and output length.
5. How many requests ran at once, with speed per request and in total.

[Inference and sampling](/lessons/inference-and-sampling/) explains why decoding waits on memory. Bandwidth figures are from the makers' datasheets, collected for the film [Where the silicon ends](/films/gpu-hardware/).
