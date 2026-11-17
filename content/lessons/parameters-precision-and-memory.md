---
title: Parameters, precision and memory
slug: parameters-precision-and-memory
part: Feeding the model
order: 7
level: Intermediate
minutes: 8
summary: A parameter is a stored number, and every number costs bytes. Precision, gradients and optimizer state decide whether a model fits on one chip or needs a cluster.
films: frontier-training:parallel, gpu-hardware:fourbit, gpu-hardware:nvfp4
related: scaling-laws, gpus-and-parallelism, mixture-of-experts
widget: memory
sources:
- Frontier training dossier (GLM-5 and DeepSeek-V4 memory arithmetic) | https://arxiv.org/abs/2602.15763
- Introducing NVFP4 for efficient and accurate low-precision inference | https://developer.nvidia.com/blog/introducing-nvfp4-for-efficient-and-accurate-low-precision-inference/
- Pretraining Large Language Models with NVFP4 | https://arxiv.org/abs/2509.25149
- Adam: A Method for Stochastic Optimization | https://arxiv.org/abs/1412.6980
- ZeRO: Memory Optimizations Toward Training Trillion Parameter Models | https://arxiv.org/abs/1910.02054
---
Saying a model has 70 billion parameters sounds abstract. Physically it means 70 billion numbers sitting in memory, and each number occupies a fixed number of bytes. Multiply the two and you know whether the model fits on your hardware.

## A parameter is a stored number

A **parameter** is one adjustable number in the model, usually a weight inside a large matrix. Training changes these numbers a little at a time. Using the model only reads them. How much space each one takes depends on its **precision**, the number of bits used to write it down.

:::bars Bytes per parameter by format
FP32 | 4 | 32 bits, the traditional default
BF16 | 2 | 16 bits, common for training and serving
FP8 | 1 | 8 bits
4-bit (FP4, INT4) | 0.5 | plus a small overhead for scales
:::

**BF16** keeps the same range of values as FP32 but with fewer digits of detail. That trade works well for neural networks, which tolerate a little noise in each weight.

## Why a 70B model does not fit on one GPU

At BF16, 70 billion parameters take 70 billion times 2 bytes, or 140 GB. An H100 has 80 GB of memory. The weights alone would need two chips, before counting anything else.

The 2026 giants make the point harder. The frontier training dossier works out that GLM-5, at 744 billion parameters, needs about 1.5 TB in BF16, and DeepSeek-V4 Pro at 1.6 trillion needs more than 3 TB. Those are inference numbers, for weights only.

## Training costs far more than the weights

Training keeps several extra copies of information per parameter:

- **Gradients**: one number per parameter saying which way to nudge it.
- **Optimizer states**: the **Adam** optimizer keeps two running averages per parameter (see [Adam](https://arxiv.org/abs/1412.6980)), usually in FP32.
- A **master copy** of the weights in FP32, so that tiny updates are not lost to rounding.

A common mixed-precision rule of thumb adds this up to about 16 bytes per parameter: 2 for BF16 weights, 2 for gradients, 4 for the FP32 master weights, and 4 plus 4 for the two Adam averages. It is a rule of thumb, and real setups differ by optimizer and recipe. All three 2026 models in the frontier dossier use the Muon optimizer, which tracks less state than Adam but still adds terabytes.

:::example 70B model, rough numbers
Inference in BF16: 70B x 2 bytes = 140 GB
Inference in 4-bit: 70B x 0.5 bytes = 35 GB (plus scales)
Training with the 16-byte rule: 70B x 16 bytes = 1,120 GB, about 1.1 TB
:::

Try your own sizes in the widget.

:::widget memory

## Activations: the other bill

While a model processes a batch, it stores the intermediate results of every layer, called **activations**, so the backward pass can use them. Activation memory grows with batch size and sequence length, not just with parameter count. Techniques such as recomputing activations instead of storing them trade extra arithmetic for less memory. This is separate from the 16-byte rule, which is why a training run needs headroom beyond it.

## Four bits and block scales

Going from BF16 to 4 bits cuts weight memory by a factor of four, but only 16 distinct values can be represented. To keep accuracy, 4-bit formats store a **block scale**: a shared multiplier for each small group of values. Within the group, each number is stored as a 4-bit code and the real value is code times scale.

:::compare
## NVFP4
- Blocks of 16 values
- Scale stored in FP8 (E4M3)
- About 4.5 bits per value including the scale
## MXFP4
- Blocks of 32 values
- Scale stored as a power of two (UE8M0)
- Coarser scale, fewer scale bytes
:::

NVIDIA's NVFP4 training work reports a 12-billion-parameter model trained on 10 trillion tokens with close to FP8 quality, while MXFP4 needed about 36 percent more tokens to match. Block scales are why 4 bits is usable at all. The GPU hardware film covers how the hardware handles them.

:::callout Key idea
Memory is set by parameters times bytes per parameter, and training multiplies the bytes. Lower precision shrinks both, which is why precision is a design choice, not a detail.
:::

## Where to go next

When the bytes do not fit on one chip, the model must be split across many; that is the subject of [GPUs and parallelism](/lessons/gpus-and-parallelism/). The parallelism chapter of the frontier training film and the 4-bit chapters of the GPU hardware film show the same arithmetic on real models.
