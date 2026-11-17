---
title: GPUs and parallelism
slug: gpus-and-parallelism
part: The machine room
order: 8
level: Advanced
minutes: 10
summary: A GPU is fast only when its arithmetic units stay fed. Training a large model means splitting it across thousands of GPUs in several ways at once, and paying for the communication.
films: gpu-hardware:exec, gpu-hardware:roofline, frontier-training:hardware, frontier-training:parallel
related: parameters-precision-and-memory, mixture-of-experts, when-training-breaks
sources:
- Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism | https://arxiv.org/abs/1909.08053
- ZeRO: Memory Optimizations Toward Training Trillion Parameter Models | https://arxiv.org/abs/1910.02054
- FlashAttention | https://arxiv.org/abs/2205.14135
- NVIDIA H100 datasheet | https://www.nvidia.com/en-us/data-center/h100/
- Roofline: An Insightful Visual Performance Model (Berkeley EECS-2008-134) | https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.pdf
- Training LLMs with Fault Tolerant HSDP on 100,000 GPUs | https://arxiv.org/abs/2602.00277
---
A modern training run uses thousands of GPUs working as one machine. To see why, and why that is hard, start with a single chip.

## How a GPU runs work

A **GPU** is built from many small processors that run the same instruction on different data. NVIDIA's H100 has 132 **streaming multiprocessors**, and each one runs threads in groups of 32 called **warps**. Each multiprocessor has its own fast on-chip memory (228 KB of shared memory usable on the H100), while the large main memory, **HBM**, sits off to the side. The H100 SXM has 80 GB of HBM at 3.35 TB/s.

For matrix multiplication, the part that dominates language models, GPUs have special **tensor cores**. On the H100, dense BF16 math on tensor cores peaks at about 989 TFLOPS, roughly 15 times the 67 TFLOPS of its ordinary FP32 units. Those peak figures are for dense math; NVIDIA's headline numbers are often doubled by counting sparsity.

## Compute-bound or memory-bound

A chip can only multiply numbers it has already fetched. The **roofline** idea says attainable speed is the lower of two limits: the chip's peak arithmetic, or its memory bandwidth times how much arithmetic you do per byte moved.

Dividing the H100's BF16 peak by its bandwidth gives about 295 floating-point operations per byte. Work that does fewer than that per byte is **memory-bound**: the arithmetic units wait for data. Work above it is **compute-bound**.

:::example Generating one token
At batch size 1, each BF16 weight is read once (2 bytes) and used for 2 operations, about 1 operation per byte. That is far below 295, so generating text is memory-bound. A 4-bit weight is about 4 operations per byte, still far below. Training uses large batches and reuses each weight many times, which moves it much closer to compute-bound.
:::

This is why FlashAttention-style kernels, which avoid round trips to HBM, matter so much, and why lower precision speeds up inference: fewer bytes to move.

## Why one GPU is not enough

Two limits show up at once. Memory: as [the previous lesson](/lessons/parameters-precision-and-memory/) showed, a large model's weights, gradients and optimizer state need terabytes against 80 GB per chip. Time: the 2026 compute estimates in the frontier dossier are on the order of 10^24 to 10^25 operations, which no single chip can finish in a lifetime. So training splits the work.

## Four ways to split a model

:::compare
## Data parallel
- Every GPU holds a full copy
- Each processes a different slice of the batch
- Gradients are averaged across GPUs each step
## Tensor parallel
- Each large matrix is cut across GPUs
- Needs very fast links, so stays inside one server
- Used in Megatron-LM
## Pipeline parallel
- Different layers live on different GPUs
- Micro-batches flow through like an assembly line
- Idle gaps called bubbles waste time
:::

A fourth kind, **expert parallel**, places different experts of a mixture-of-experts model on different GPUs and sends each token to wherever its expert lives (see [Mixture of experts](/lessons/mixture-of-experts/)). Long sequences can also be split, which GLM-5 uses as context parallelism.

Real runs combine them. Kimi K2.5 reports 16-way pipeline parallelism, 16-way expert parallelism and data parallelism with ZeRO-1, on H800 GPUs linked by 8 x 400 Gb/s RoCE networking.

## Sharding the state

Plain data parallelism wastes memory, because every GPU stores identical optimizer state. **ZeRO** and its relative **FSDP** shard that state: each GPU keeps only a slice of the optimizer state, and in higher stages of the gradients and weights too, gathering pieces when needed. ZeRO-1 shards only the optimizer state. Each stage trades memory for extra communication.

## Communication is the tax

Every split creates traffic. Data parallel needs gradient averaging, tensor parallel needs exchanges inside every layer, expert parallel needs all-to-all token shuffles. Inside a server, GPUs talk over NVLink (900 GB/s on the H100, 1.8 TB/s on Blackwell). Between servers the network is slower, so designers keep chatty parallelism inside the server and quieter kinds across servers.

:::callout Key idea
Parallelism does not remove cost, it moves it. The aim is to overlap communication with computing so no chip sits idle. DeepSeek-V4 uses one fused kernel that overlaps computing, communication and memory access for exactly this reason.
:::

Scale also brings failure. A fault-tolerance study of a 100,000-GPU job estimates a failure about every 18 minutes, which is why [When training breaks](/lessons/when-training-breaks/) is its own lesson.

## Where to go next

[Mixture of experts](/lessons/mixture-of-experts/) explains the architecture that expert parallelism serves, and [When training breaks](/lessons/when-training-breaks/) covers what happens when thousands of chips run for months. The GPU hardware film (how a GPU runs work, compute versus memory bound) and the frontier training film (chips and power, parallelism) show these ideas on real hardware.
