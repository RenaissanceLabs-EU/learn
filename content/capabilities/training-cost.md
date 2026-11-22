---
title: How to work it out
---
The cost of a training run is counted in **GPU-hours**: the number of accelerators times the hours they ran. Everything else, money included, follows from that number.

### After the run: count it

Multiply the accelerators by the wall-clock time. Two real runs from the recipes on this site:

:::example Two runs, counted
Full-weight DPO, 1.4 million pairs
32 GPU dies  x  43 h 21 min  =  about 1,387 GPU-hours

SFT warm start, 6,123 rows
8 GPUs  x  12 min  =  1.6 GPU-hours
:::

The first is almost a thousand times the second, and both are post-training. Say which stage a number belongs to.

### Before the run: estimate it

There are two ways. The second is more reliable.

**From the size of the job.** A common rule of thumb from the scaling-law papers puts training compute at about six floating-point operations per parameter per token:

:::example The 6ND rule
compute  =  6  x  parameters  x  training tokens

A 9-billion-parameter model on 300 billion tokens:
6  x  9,000,000,000  x  300,000,000,000  =  1.6 x 10^22 operations
:::

Divide that by what one accelerator delivers per second, and by the share of its peak you expect to reach. No training job reaches the peak on the datasheet. Assume 40% here, as an illustration and not a measurement:

:::example From operations to GPU-hours
One H100 at 16-bit:   989.5 x 10^12 operations per second at peak
At 40% of peak:       about 4 x 10^14 per second

1.6 x 10^22  /  4 x 10^14  =  about 41 million seconds, or about 11,400 GPU-hours
On 64 GPUs:  about 7.4 days
:::

The same job on A100s, at the same 40%, comes to about 36,000 GPU-hours. The answer moves in direct proportion to the share of peak you assume, so treat it as a first guess.

**From a short test.** Run a few hundred steps on the real hardware and read the throughput from the log.

:::example From a test run
hours  =  total training tokens  /  (tokens per second  x  3,600)
GPU-hours  =  hours  x  number of GPUs
:::

This includes everything the rule of thumb leaves out: data loading, communication between nodes, and the padding in your batches.

### What the number leaves out

- **Building the data.** Sampling a model and judging its answers with another model is GPU work. In the hallucination recipe, each data round was a job on two GPUs with a ten-hour limit.
- **Evaluation.** The benchmark for that recipe is its own job on two GPUs, with a three-hour limit.
- **Failed runs.** One DPO run in that project ran out of GPU memory at step 41 of 48 and had to be run again. Budget for reruns.
- **Storage.** A 9-billion-parameter checkpoint at 16 bits per weight is about 18 GB. Saving one every few hundred steps adds up.

### From GPU-hours to money

- **Cloud.** GPU-hours times the hourly price. Prices change often and differ by provider, so quote the date with the figure.
- **Academic clusters.** Time is granted as an allocation, and systems count differently. LUMI counts each of the two dies in its AMD accelerators separately, which is why the DPO run above is reported per die.

### Common hardware

What matters for training is memory per accelerator, which decides what fits, and 16-bit throughput, which decides how long it takes.

| Accelerator | Memory | Peak 16-bit throughput | Where you meet it |
| --- | --- | --- | --- |
| NVIDIA A100 | 40 or 80 GB | 312 TFLOPS | Leonardo, in a 64 GB version |
| NVIDIA H100 | 80 GB | 989.5 TFLOPS | Widely rented in the cloud |
| NVIDIA H200 | 141 GB | Same as H100 | An H100 with more memory |
| NVIDIA B200 | Up to 192 GB | 2,500 TFLOPS | The Blackwell generation |
| AMD MI250X | 128 GB, as two dies of 64 GB | 383 TFLOPS | LUMI |
| AMD MI300X | 192 GB | 1,307 TFLOPS | |
| Google TPU | | | Google's own accelerators, used by Marin |

Throughput figures are dense peaks from the makers' datasheets. They rank the hardware. They do not predict your run, because memory bandwidth and the network between nodes often set the real speed.

### Does it fit?

Full fine-tuning holds more than the weights. It needs the gradients too, and the optimizer keeps two more values per weight. Plan for several times the size of the model, spread over the GPUs. Low-rank adapters train a small set of added weights and leave the rest frozen, which is why they fit on far less hardware.

### What to report

1. The accelerator model and how many, with the number of nodes.
2. Wall-clock time, and whether it includes evaluation.
3. GPU-hours per stage, with the counting rule if the system has one.
4. Precision and batch size.

The sources for the hardware figures are the datasheets collected for the film [Where the silicon ends](/films/gpu-hardware/). The lessons [Scaling laws](/lessons/scaling-laws/) and [GPUs and parallelism](/lessons/gpus-and-parallelism/) explain where the rule of thumb and the real-world slowdowns come from.
