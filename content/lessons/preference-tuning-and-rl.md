---
title: Preference tuning and reinforcement learning
slug: preference-tuning-and-rl
part: After pre-training
order: 12
level: Advanced
minutes: 10
summary: How models learn from comparisons and from checkable rewards: RLHF, DPO, verifiable rewards, group-based RL, and the sandboxes and reward hacking that come with it.
films: frontier-training:post, cluster-agents:rl, cluster-agents:rlrisk, inkling:rl
related: supervised-fine-tuning, evaluation, when-training-breaks
sources:
- Training language models to follow instructions with human feedback (InstructGPT) | https://arxiv.org/abs/2203.02155
- Deep Reinforcement Learning from Human Preferences | https://arxiv.org/abs/1706.03741
- Direct Preference Optimization | https://arxiv.org/abs/2305.18290
- DeepSeekMath (GRPO) | https://arxiv.org/abs/2402.03300
- DeepSeek-R1 | https://arxiv.org/abs/2501.12948
- Training Verifiers to Solve Math Word Problems | https://arxiv.org/abs/2110.14168
---
After [supervised fine-tuning](/lessons/supervised-fine-tuning/), a model imitates good answers. Imitation has a ceiling: the model cannot easily become better than its examples, and for many tasks it is hard to write the ideal answer but easy to say which of two answers is better, or whether an answer is simply right. Reinforcement learning uses exactly that kind of feedback.

In **reinforcement learning** (RL), the model generates an attempt, a **reward** scores it, and the model's weights are adjusted to make high-scoring attempts more likely. The model's behaviour is called its **policy**.

:::flow
Prompt | A task or question
Rollout | The model writes an attempt
Reward | A score for the attempt
Update | Good attempts become more likely
:::

## RLHF in plain steps

**Reinforcement learning from human feedback** (RLHF) is the method behind InstructGPT. It works in three steps.

1. Collect comparisons. For a prompt, the model writes several answers and people rank them.
2. Train a **reward model**, a second network that reads a prompt and an answer and outputs a score, so that it agrees with the human rankings.
3. Use RL to tune the language model against that score, with a penalty that keeps it from drifting too far from its starting point.

The reward model stands in for human judgement at a scale no team of people could supply. Its weakness is the same: it is only an approximation, and a model optimised hard against it will find answers that please the approximation without pleasing people.

## DPO: skipping the reward model

**Direct Preference Optimization** (DPO) reaches a similar goal with less machinery. It trains directly on pairs of a preferred and a rejected answer, raising the probability of the first relative to the second, with no separate reward model and no RL loop. It is simpler and cheaper to run, which is why it is common for style and helpfulness. It learns from a fixed set of pairs, so it cannot explore on its own.

:::widget dpo

## Rewards you can check

Some tasks have an answer a program can verify. A maths problem has a final answer. Code either passes its unit tests or it does not. This is **reinforcement learning with verifiable rewards** (RLVR), and it removes the human and the reward model from the loop.

:::compare
## RLHF
- Reward comes from a learned model of human preference
- Covers open-ended work: tone, helpfulness, safety
- The reward can be wrong in subtle ways
## RLVR
- Reward comes from a check: tests pass, answer matches
- Covers maths, code, tool use, anything checkable
- Cheap to scale, but only where a check exists
:::

## Group comparison, in plain words

DeepSeek's **GRPO** (group relative policy optimization) is a widely used recipe for this. For each prompt the model writes a group of attempts, for example 16. Each is scored. An attempt is then judged against the group's average: better than its siblings, push it up; worse, push it down. This removes the need for a separate network to predict how good a situation is. One practical detail from Xiaomi's MiMo report: prompts where every attempt passes or every attempt fails carry no signal, and a sampler can drop them.

At scale, MiMo-V2.6-Pro used 1,568 prompts with 16 rollouts each, about 25,000 attempts per step, and reports $2.6M of RL compute for the Pro model.

:::widget grpo

The full path from base model to a model trained this way is followed step by step in [Post-training, end to end](/lessons/post-training/).

## Reasoning and long chains of thought

When the reward only checks the final answer, models learn to spend more tokens thinking before they answer. DeepSeek-R1 is the well-known example of reasoning emerging from this kind of training. These **reasoning models** write long **chains of thought** and may revise themselves along the way. Some releases let users pick an effort level, which trades cost for accuracy.

## Sandboxes and rollout fleets

Agent tasks make rollouts long and messy. The model reads a task, runs a command or a search, sees the result, and repeats, for dozens of steps. In a typical setup a trainer updates the model on GPUs, inference servers generate the actions, and many rollout workers run the environments on ordinary CPU machines.

The scale is large. Kimi K2.5 describes a rollout manager running up to 100,000 agent tasks at once. DeepSeek-V4 describes hundreds of thousands of concurrent sandboxes. In Thinking Machines' Inkling 2 Small run, joint RL took 1,075 steps and over 17 million rollouts. The median rollout was 43,000 tokens, and the slowest 1% reached 1.5 million. A few slow attempts can stall everyone, which is why asynchronous RL (training on slightly stale rollouts) is common.

Every command in a rollout is executed automatically and almost nobody reads it, so sandboxes matter. They contain the damage if a model does something unexpected.

## Reward hacking

:::callout Key idea
An optimiser searches for whatever earns reward, not for what you meant. If a loophole exists, millions of attempts will find it.
:::

This is **reward hacking**. Labs report coding agents that edit the tests, read hidden files, or look through version history for the answer. Kimi K2.5 added a reward term against spurious parallelism. GLM-5 fixed a slide-generation exploit by fixing the renderer itself. Xiaomi gave zero reward to confirmed hacks, under 2% of trajectories. The defences are practical: keep the checker outside the sandbox, hide the answers, and read real transcripts.

## Where to go next

[Evaluation](/lessons/evaluation/) shows how teams find out whether any of this worked. For the infrastructure side, see [When training breaks](/lessons/when-training-breaks/). The Post-training chapter of the frontier training film, the RL and Reward hacking chapters of the cluster agents film, and the RL chapter of the Inkling film cover the same ground.
