---
title: Distillation and quantization
slug: distillation-and-quantization
part: After pre-training
order: 14
level: Intermediate
minutes: 8
summary: Two ways to make a model cheaper to run: teach a small model to imitate a big one, or store the same weights in fewer bits. What each one keeps, and what it costs.
films: gpu-hardware-video:fourbit, gpu-hardware-video:nvfp4, gpu-hardware-video:blockscale, inkling-video:format, open-models:post
related: parameters-precision-and-memory, inference-and-sampling, supervised-fine-tuning
sources:
- Distilling the Knowledge in a Neural Network | https://arxiv.org/abs/1503.02531
- LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale | https://arxiv.org/abs/2208.07339
- QLoRA | https://arxiv.org/abs/2305.14314
- Pretraining Large Language Models with NVFP4 (NVIDIA) | https://arxiv.org/abs/2509.25149
---
A trained model is expensive to run mostly because it is big. There are two direct ways to shrink the bill. You can build a smaller model that behaves like the large one, which is **distillation**. Or you can keep the model as it is and store each number with fewer bits, which is **quantization**. They attack different things, and modern models often use both.

## Distillation: a student that imitates a teacher

In distillation, a large, strong **teacher** model is used to train a smaller **student**. The idea comes from Hinton and colleagues in 2015.

The key observation is about what the teacher's output contains. When a model predicts the next token, it produces a full probability distribution, not just a winner. If the right answer is "cat", a good teacher may give "dog" a small but real probability and "carburettor" almost none. That pattern of near-misses says something about how the world is organised. A plain training label ("the answer was cat") throws it away. The teacher's probabilities, called **soft targets**, keep it.

So the student is trained to match the teacher's distribution, not only the single correct token. Each example then carries more information, and a small model can learn a surprising amount from it.

:::flow
Teacher | Large model, already trained
Soft targets | Its probabilities for every next token
Student | Smaller model trained to match them
Result | Cheaper model, close but not equal
:::

There is also a practical variant that is now common in language models. In **on-policy distillation**, the student writes its own answers and the teacher scores them, instead of the student only reading text the teacher wrote. Our open-models research notes that several recent open models use it to merge skills from several specialist teachers (for example math, code and agent behaviour) into one student. It is a post-training step, covered alongside [Supervised fine-tuning](/lessons/supervised-fine-tuning/).

:::callout Key idea
Distillation changes the model. The student is a different, smaller network that has learned to behave like the teacher. It will not match the teacher everywhere.
:::

## Quantization: same model, fewer bits

Recall from [Parameters, precision and memory](/lessons/parameters-precision-and-memory/) that every weight is a number stored in some format. Quantization stores each weight in a coarser format. The network is the same; its numbers are just rounded.

The saving is direct. Going from 16 bits to 8 halves the bytes per weight, and going to 4 bits quarters them. Because generating text is mostly limited by how fast weights can be read from memory (see [Inference and sampling](/lessons/inference-and-sampling/)), fewer bytes often means faster tokens as well as a smaller footprint.

:::compare
## Post-training quantization
- Take a finished model and convert its weights
- Cheap: no further training, or very little
- Works well at 8 bits; harder as bits drop
## Quantization-aware training
- Simulate low precision while training
- The model learns to work around the rounding
- Costs training compute, but holds up better at 4 bits
:::

**Post-training quantization** is the easy route, and 8-bit conversion of weights has been shown to work with little loss when a few unusually large outlier values are handled carefully (the LLM.int8 paper). **Quantization-aware training** builds the rounding into training so the model adapts. Our research notes record this in current open models: some use FP4 quantization-aware training for their expert layers, and one trains with MXFP4 or MXFP8 quantization-aware training from the start of fine-tuning.

## Formats and block scales

The common formats are INT8 (8-bit integers), FP8 (8-bit floating point) and 4-bit floating point. A 4-bit float has only sixteen possible values, so on its own it is far too coarse. The fix is a **block scale**: a group of values shares one scale factor, which stretches the tiny set of values to fit that group's range.

In NVIDIA's NVFP4 format, each value has a sign, two exponent bits and one mantissa bit. Every block of sixteen values shares an 8-bit floating-point scale, and the whole tensor has one extra scale on top.

:::stats
16 | values per block scale in NVFP4
4 bits | per value, a quarter of 16-bit
8 bits | per block scale, in floating point
:::

## What is lost, and what is not

Rounding adds error. Usually the error is small enough that benchmark scores barely move, but it is not zero, and it tends to show up first in rare cases: unusual inputs, long chains of reasoning, and layers with large outlier values. That is why careful recipes keep some parts in higher precision. NVIDIA's NVFP4 training recipe, for example, keeps the first two and last eight blocks of its 12-billion-parameter model in BF16.

What quantization does not touch is the architecture, the knowledge layout, and (for weight-only schemes) the way the model is used. What distillation does not preserve is the teacher's full capability; the student is smaller, so something is given up.

## Why Hopper and Blackwell differ

Hardware decides which of these are fast. According to our GPU research, Hopper's matrix instructions accept 16-bit formats, FP8 and 8-bit integers, but not 4-bit values and not block scales. So on Hopper, 4-bit is a storage and bandwidth format: weights are unpacked to 16 bits in registers before the multiply. That still helps when decoding is memory-bound. Blackwell data-centre chips add native 4-bit and block-scaled formats, and NVIDIA reports 4-bit peak throughput of 2x FP8 on GB200 and 3x on GB300 (dense).

:::example The four-bit trap on Hopper
A 4-bit weight stored as NVFP4 can be unpacked into BF16 without any loss.
But the product of a 4-bit value and its block scale can need more significant bits than FP8 can hold.
So you cannot simply feed NVFP4 into Hopper's 8-bit units and stay exact.
:::

## Where to go next

[Inference and sampling](/lessons/inference-and-sampling/) explains why cheaper weights speed up generation. For the hardware side, the GPU hardware film chapters on 4-bit, NVFP4 and block scales go through the formats in detail, and the Inkling chapter on number format shows a lab training natively in 4-bit.
