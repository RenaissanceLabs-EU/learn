---
title: In practice there is a difference
slug: theory-and-practice
date: 2026-11-17
minutes: 7
summary: Running a job on a cluster is a skill of its own. Making something work before you understand why is a legitimate first step, as long as you come back for the why.
films: cluster-agents:hook
related: when-training-breaks, gpus-and-parallelism, how-a-model-learns
---
There is an old saying: in theory there is no difference between theory and practice. In practice there is.

Anyone who has trained a model on a real cluster knows it. The lessons on this site explain what a model is, how a gradient is computed and how work is split across GPUs. They are true. None of them will tell you why your job died after eleven minutes with an error from the networking library, why the queue gave you half the nodes you asked for, or why the script that ran yesterday now hangs at step zero.

## Two kinds of knowing

Theory tells you what should happen. The cluster tells you what does.

Knowing that something works and knowing how to make it work are different kinds of knowledge, and they are learned in different ways. The first comes from reading and thinking. The second comes from doing, failing and doing again. A pilot has studied aerodynamics, and nobody confuses that with flying.

This matters for the field because most of the work of training a model is the second kind. The paper gives you the recipe. The cluster decides whether you get to cook.

## What the doing includes

Almost none of it appears in a paper:

- **Getting time and living within it.** Queues, quotas, time limits and shared machines that other people are using. Big jobs deserve a question to the people who run the cluster before they start.
- **The environment.** Containers, drivers and library versions that must agree. An image built for one kind of processor may not run on another.
- **Storage.** A home directory that fills up, fast scratch space versus slow shared disk, files written with permissions the next job cannot read, data that has to be in the right place before the job starts.
- **Communication.** GPUs that must find each other over the network. One slow or broken node among hundreds can stall everything.
- **Failure handling.** Checkpoints, restarts, jobs that stop on a time limit, and jobs that hang quietly instead of failing loudly.
- **Observation.** Reading logs rather than only dashboards, and knowing what a normal run looks like so that an abnormal one stands out.

None of this is glamorous. All of it decides whether a run happens at all.

## It is fine to make it work before you understand it

Often you change a flag, pin a version or restart on different nodes, and the job runs, and you do not know why. That is allowed. It is also useful.

A job that works gives you a baseline. It gives you a live example you can poke at, and a pair of cases, one that works and one that does not, to compare. That comparison produces evidence about the problem that no amount of theory can. Understanding why often comes afterwards, and it comes more easily because you now have something to explain.

:::callout The first step
Making it work is a good first step. It is not the last one.
:::

Two cautions keep this honest. First, write down what you changed and what happened. A fix you cannot reproduce is luck. Second, come back for the why when it matters. Unexplained fixes pile up into folklore, the kind of advice that says "always set this variable" without anyone able to check whether it still does anything.

## How to practise the art of doing

The skill is built the way other practical skills are built: with small attempts, quick feedback and a lot of repetition. These habits speed it up.

1. **Start small.** One GPU, then one node, then two, then many. Each step adds one new way for things to fail, so a failure points somewhere specific.
2. **Run a smoke test before every long job.** Tiny data, a few steps, the same code path, including saving a checkpoint and resuming from it. Ten minutes here can save a day.
3. **Change one thing at a time, and keep a run log.** The command, the configuration, what happened and what you expected. Your future self is the main reader.
4. **Read the failing log from the top.** The first error is usually the cause. Everything after it is fallout.
5. **Check before you consume.** Know roughly how much memory, disk and time a job will use before it starts. Split the work into chunks, put limits in place and watch the job while it runs. Shared machines punish guessing.
6. **Reproduce before you fix.** If you cannot make it fail again, you cannot know that you have fixed it.
7. **Ask early.** The people who run the cluster have seen your problem before. Their five-minute answer is worth more than a day of guessing.

## What this means for labs

Cluster skill is mostly passed on by sitting next to someone who has it. A lab that wants more people able to train models can help in three ways: put a real job in a newcomer's hands in the first week, keep a short runbook for the usual failures, and write down what went wrong, in public when it can. The failure stories are the curriculum. They are also the part of the field that is hardest to find written down.

## Where to go next

[When training breaks](/lessons/when-training-breaks/) covers what fails at very large scale, and [GPUs and parallelism](/lessons/gpus-and-parallelism/) explains what the cluster is doing while your job runs. The film on running agents safely on a cluster shows how to stage a risky workload one careful step at a time.
