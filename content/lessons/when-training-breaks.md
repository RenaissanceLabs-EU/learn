---
title: When training breaks
slug: when-training-breaks
part: The machine room
order: 10
level: Advanced
minutes: 8
summary: At frontier scale something is always failing. How labs survive broken chips, loss spikes, silent wrong answers and fragile low-precision numbers.
films: frontier-training:failures, open-models:stab
related: gpus-and-parallelism, parameters-precision-and-memory, mixture-of-experts
sources:
- Training LLMs with Fault Tolerant HSDP on 100,000 GPUs | https://arxiv.org/abs/2602.00277
- Exploring Silent Data Corruption as a Reliability Challenge in LLM Training | https://arxiv.org/abs/2604.00726
- DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence | https://arxiv.org/abs/2606.19348
- Pretraining Large Language Models with NVFP4 | https://arxiv.org/abs/2509.25149
- Adam: A Method for Stochastic Optimization | https://arxiv.org/abs/1412.6980
---
A training run for a frontier model keeps thousands of chips busy for weeks or months. Each chip, cable, memory module and software library has some small chance of failing on any given day. Multiply a small chance by a very large number of parts and failure stops being an exception. It becomes a routine event that the whole system has to be designed around.

## Hardware fails all the time

A January 2026 paper from Meta and partners measured this on a job with 32,000 GPUs. They saw 2.3 interruptions per 1,000 servers per day, and 78% of them were hardware related. Even so, the job spent 95 to 97% of its time making real progress. That number is the **effective training time**: the share of wall-clock time that actually moves the model forward, rather than waiting, restarting or redoing lost work.

Scale changes the picture quickly. For a job on 100,000 GPUs, the same paper estimates a failure roughly every 18 minutes, which is about 80 a day. If every failure halts the whole job for up to ten minutes, the paper's own model puts effective training time at about 44%. More than half of a very expensive cluster would be idle.

:::stats
2.3 | interruptions per 1,000 servers per day (32K GPUs)
18 min | estimated time between failures at 100K GPUs
44% | modelled effective time if each failure stops everything
~3 min | stall in a real test on 98K H100s with the fix below
:::

## Checkpoints and restarts

The basic defence is the **checkpoint**: a saved copy of everything needed to continue, meaning the weights, the optimizer's running statistics and the position in the data. When something dies, the job restarts from the last checkpoint and repeats only the work done since.

There is a trade-off. Saving a checkpoint of a very large model takes time and storage, so you cannot save every minute. Save rarely and a failure throws away hours of work. Save often and you spend your time writing files. Labs tune this interval against how often they expect failures.

## Fault-tolerant training

The Meta paper goes further than restarting everything. Training uses **data parallelism**, where several replicas of the model each process a different slice of the batch (see [GPUs and parallelism](/lessons/gpus-and-parallelism/)). The authors treat one replica as the unit of failure. When a chip in one replica dies, only that replica is rebuilt while the others keep training. In a test on 98,000 H100 GPUs, a failure stalled training for about three minutes, instead of idling the whole cluster.

:::flow
Chip fails | One replica stops
Detect | Monitoring notices within seconds
Isolate | Healthy replicas keep training
Rebuild | Broken replica reloads state
Rejoin | Back in the group
:::

## Loss spikes

Not every failure is a broken part. Sometimes the **loss**, the number that measures how wrong the model's predictions are, suddenly jumps upward in the middle of a healthy run. These are **loss spikes**. Some recover on their own. Others wreck the run, and the team rolls back to an earlier checkpoint and often skips the batch of data that triggered it.

The causes are partly understood and partly not. DeepSeek's V4 report traced its spikes to outlier values inside the mixture-of-experts layers. Two fixes are reported. **Anticipatory routing** decides which experts handle a token using slightly older parameters, at about 20% overhead, and is switched on automatically after a spike. **SwiGLU clamping** caps the values inside each expert's activation function so they cannot grow without limit. The same report says openly that the principles behind why these work are insufficiently understood. Stability is still partly craft.

:::callout Key idea
Most failures are loud: a chip dies, a job crashes. The dangerous ones are quiet, because the run carries on and nobody knows it is damaged.
:::

## Silent data corruption

**Silent data corruption** is the quiet kind. A faulty chip returns a wrong number and raises no error. A 2026 study from TU Berlin examines how this shows up when training language models, and a 2026 OSDI paper looks at GPU faults in production. Our research read only their titles, so this lesson gives no figures for them. The point is the shape of the problem. A bad value can flow into the gradients, get averaged with good ones and look like ordinary noise, or it can show up later as an unexplained spike.

## Numbers that are too small

Low precision makes everything above more delicate. Using fewer bits per number saves memory and time, but gives each value less room (see [Parameters, precision and memory](/lessons/parameters-precision-and-memory/)). Reports describe the countermeasures. Step 5 Preview keeps hidden states and gradients in 32-bit and clamps a tiny fraction of extreme gradient values to stabilise 8-bit training. NVIDIA's 4-bit recipe reports a loss gap below 1% against a higher-precision baseline for most of a 10-trillion-token run, widening to about 1.5% during learning-rate decay.

## What engineers watch

- Loss curves, plotted against the expected shape for that model size.
- Gradient norms, which are a common early warning of trouble.
- Throughput per GPU, because a slow chip drags every other chip down with it.
- Hardware health: error counters, temperatures, network links.
- Comparisons of the same computation across devices, which can expose a chip that gives different answers.

## Where to go next

[Mixture of experts](/lessons/mixture-of-experts/) explains the routing that makes DeepSeek's fixes necessary. After training comes shaping behaviour, starting with [Supervised fine-tuning](/lessons/supervised-fine-tuning/). The Failures chapter of the frontier training film and the Stability chapter of the open models film cover the same ground in motion.
