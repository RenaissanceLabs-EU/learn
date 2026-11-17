---
title: Evaluation
slug: evaluation
part: After pre-training
order: 13
level: Intermediate
minutes: 8
summary: How we measure what a model can do, and why every measurement has a catch: contamination, saturation, judge bias and scores that cannot be compared across versions.
films: frontier-training:eval, open-models:boards, open-models:arena
related: preference-tuning-and-rl, what-open-means, distillation-and-quantization
sources:
- Measuring Massive Multitask Language Understanding (MMLU) | https://arxiv.org/abs/2009.03300
- Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | https://arxiv.org/abs/2306.05685
- Training Verifiers to Solve Math Word Problems | https://arxiv.org/abs/2110.14168
- Artificial Analysis Intelligence Index | https://artificialanalysis.ai/evaluations/artificial-analysis-intelligence-index
- GLM-5: from Vibe Coding to Agentic Engineering | https://arxiv.org/abs/2602.15763
- DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence | https://arxiv.org/abs/2606.19348
---
Training produces a model. Evaluation tells you what you actually got. It sounds like the easy part, and it is among the hardest, because a language model can do an open-ended range of things and any test samples only a few of them.

## What a benchmark measures

A **benchmark** is a fixed set of tasks with a way to score the answers. MMLU, for example, is a large collection of multiple-choice questions across many school and professional subjects, scored by accuracy. Coding benchmarks give the model a task and run the resulting code against tests. Agent benchmarks give it a computer-like environment and check whether the job got done.

The frontier training film shows what current reports look like. DeepSeek V4 Pro, in its maximum reasoning mode, reports 80.6 on SWE-bench Verified and 67.9 on Terminal Bench 2.0. The test setup is itself an engineering system: those agent tests allow up to 500 steps and 512,000 tokens of context.

A benchmark score answers one narrow question: how does this model do on these tasks, under this setup? Changing the prompt, the number of attempts or the reasoning budget can change the result, so a number without its setup is only half a fact.

## Contamination and saturation

Two problems age every benchmark.

**Contamination** means the test questions, or their answers, were in the training data. A model that has seen the answer key looks smarter than it is. Web-scale data makes this hard to rule out, since public benchmarks are copied all over the internet.

**Saturation** means models score so close to the maximum that the test no longer separates them. When most strong models land in the high nineties, a one-point gap is noise. Benchmark makers respond by building harder tests, and the cycle repeats.

:::callout Key idea
Any public benchmark is a target. Once a number matters, people train toward it, deliberately or not, and the number stops meaning what it did.
:::

## Human preference arenas

Some leaderboards skip fixed questions. In an **arena**, a person types any prompt, receives answers from two anonymous models, and picks the better one. Many such votes are turned into a rating on the Elo scale, the same system used in chess.

This captures what benchmarks miss, such as tone and usefulness on real requests. It also rewards what people like at a glance, which can include length and confident formatting. And it can disagree with other rankings: in the open models film's snapshot of an arena text leaderboard, only one open-weights model sits in the top 15 (rank 11), roughly 35 Elo behind first place, even though several open models rank higher on agent-heavy indexes.

## LLM as judge

Reading thousands of answers is slow, so teams often ask a strong model to grade them. The MT-Bench paper found that such judges agree with human preferences a lot of the time, which makes them useful. It also catalogued biases: a judge can favour longer answers, favour the answer shown first, and favour text written by its own model family. Careful setups randomise answer order, use written rubrics, and check the judge against human ratings now and then.

## Composite indices

A single number is easier to read than ten. The **Artificial Analysis Intelligence Index**, version 4.3.2, is a weighted average of 10 evaluations grouped into four categories (agents, coding, general capability and scientific reasoning) at 25% each.

:::bars Open-weights models on Intelligence Index v4.3.2
MiMo-V2.6-Pro | 46 | Xiaomi
DeepSeek V4.1 Flash (Max) | 45 | DeepSeek
GLM-5.3 (Max) | 45 | Z.ai
Qwen3.8 27B (xhigh) | 34 | Alibaba
:::

The catch is that the index gets harder over versions. The open models film notes that Nemotron 3 Ultra scored 47.7 at the index's launch in June 2026 and scores 23 on v4.3.2. Scores are only comparable inside one version. GLM-5's report of 50 against 42 for its predecessor, an average gain of about 20%, was on version 4.0.

## Private held-out evals

Because public tests leak and saturate, serious teams keep **held-out** evaluations: questions that were never published and never used for training or tuning. Their job is to answer one question honestly, how does the model do on something it cannot have memorised? Teams also read real transcripts, because benchmarks and rewards can both be gamed, and a model that scores well can still fail in strange ways.

## Evaluating your own use case

For a particular application, public rankings are only a starting list. A practical approach:

1. Collect 50 to 200 real examples of the task, including awkward ones.
2. Write down what a good answer looks like, ideally as a checklist.
3. Score with a check where possible (a test, an exact match) and a judge where not, and read a sample by hand.
4. Keep the set private, and rerun it whenever the model, the prompt or the settings change.

Those sizes are a rule of thumb. The point is that a small set that resembles your real traffic tells you more than a famous leaderboard that does not.

## Where to go next

[Preference tuning and RL](/lessons/preference-tuning-and-rl/) shows how rewards, which are a kind of evaluation inside training, can also be gamed. For what makes a model's weights usable by others, see [What open means](/lessons/what-open-means/). The Eval chapter of the frontier training film and the Board and Arena chapters of the open models film show the numbers in context.
