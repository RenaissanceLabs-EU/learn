---
title: How models learned to prefer: RLHF, DPO and alignment, from ChatGPT to a European 9B
slug: preference-tuning-and-alignment
date: 2026-11-18
minutes: 22
summary: A history of preference tuning from the first human-feedback experiments to DPO, and a close reading of one real checkpoint: what the data was, what moved, what did not, and what the benchmark can and cannot say.
films: cluster-agents:rlrisk
related: preference-tuning-and-rl, post-training, supervised-fine-tuning, evaluation
---
In November 2022 a chat window opened to the public and a lot of people met a language model for the first time. The model behind it was not much bigger than what had existed the year before. What had changed was how it was finished. It had been trained on human judgements of which answers were better, and it behaved as if it was trying to help.

That finishing step is called preference tuning, and the family of methods around it is what people mean when they say a model has been aligned. This note tells the story of those methods from the beginning, and then reads one recent checkpoint closely to see what they do in practice: [oellm-9b-threeway-dpo-full-v1](https://huggingface.co/birgermoell/oellm-9b-threeway-dpo-full-v1), a 9B model tuned with preferences, and its results on the [EUROPA Alignment](https://birgermoell.github.io/europa-alignment/) benchmark. The history tells you why the methods exist. The checkpoint tells you what they look like when someone runs them with real data and real compute, and where the evidence stops.

## Three words that get confused

**Preference tuning** is a method: train a model so that answers people prefer become more likely than answers they do not. RLHF and DPO are two ways to do it.

**Alignment** is a goal: the model does what the people using it and building it actually intend. An early and still useful framing asks for a model that is helpful, honest and harmless.

**Safety evaluation** is a measurement: tests that check whether the goal was reached in particular situations.

The three are connected but they are not the same thing. Preference tuning can improve alignment on the things you measured and leave other things untouched. A strong benchmark score says the model behaved well on those items, and no more than that. Keeping the three apart makes the rest of this note easier to read.

## The problem it solves

A pre-trained model predicts text. Asked a question, it may continue with more questions, because that is what the page looked like. [Supervised fine-tuning](/lessons/supervised-fine-tuning/) fixes the format by showing the model good replies, but imitation has a ceiling. Writing the perfect answer is hard. Saying which of two answers is better is much easier, and people agree on it more often.

Many things we want are of that second kind. Be helpful without being pushy. Admit uncertainty without being useless. Decline a dangerous request without refusing a harmless one that sounds similar. Nobody can write a formula for these, but a person can look at two replies and pick. Preference tuning turns those picks into a training signal.

Try being the annotator. Each pick teaches a small reward model what to reward, and you can watch it learn.

:::widget annotator

## A short history

| When | Work | What it showed |
|---|---|---|
| 2017 | Christiano et al., Deep Reinforcement Learning from Human Preferences | A reward can be learned from humans comparing short clips, so nobody has to write the reward function |
| 2017 | Schulman et al., Proximal Policy Optimization (PPO) | A stable way to update a policy with reinforcement learning, later the workhorse of RLHF |
| 2019 | Ziegler et al., Fine-tuning language models from human preferences | The same recipe applied to a language model |
| 2020 | Stiennon et al., Learning to summarize from human feedback | Summaries tuned on human preferences were preferred to those from supervised training |
| 2021 | Askell et al., a general language assistant as a laboratory for alignment | The helpful, honest, harmless framing |
| March 2022 | InstructGPT | RLHF at scale on instruction following |
| April 2022 | Bai et al., helpful and harmless assistant from human feedback | Helpfulness and harmlessness trained together, and the tension between them |
| November 2022 | ChatGPT | A chat model tuned with RLHF reaches the public |
| December 2022 | Constitutional AI | AI feedback guided by written principles replaces many human labels |
| May 2023 | Direct Preference Optimization | The reinforcement learning loop is removed |
| 2023 | Llama 2, Zephyr | RLHF and DPO become routine in open models |
| 2024 and 2025 | DeepSeekMath and DeepSeek-R1 | Rewards from checkable answers, with group-based RL |

### 2017: a robot learns to do a backflip without a score

The first step was not about language. Christiano and colleagues at OpenAI and DeepMind wanted to train agents on tasks where the goal is easy to recognise and hard to write down. Their method showed a person two short video clips of an agent behaving, asked which was better, and trained a **reward model** to predict those choices. A reinforcement learning algorithm then optimised the agent against the learned reward. It worked on Atari games and on simulated robots, with no hand-written reward function. The paper is on [arXiv](https://arxiv.org/abs/1706.03741).

Two ideas from it carry through everything that follows. A reward can be learned from comparisons. And what you optimise is a model of human judgement, not human judgement itself.

### 2019 to 2021: bringing it to language

Ziegler and colleagues applied the same recipe to GPT-2, and Stiennon and colleagues applied it to summarising Reddit posts, where tuned summaries were preferred over those of supervised models. During those years Askell and colleagues at Anthropic wrote down the framing that stuck: a useful assistant should be helpful, honest and harmless. Those three words became the informal target for most preference data that followed, including the data in the checkpoint below.

### 2022: InstructGPT

[InstructGPT](https://arxiv.org/abs/2203.02155) is the paper that turned the method into a recipe, and it has three steps that are still the standard description of RLHF. Collect demonstrations and fine-tune. Collect comparisons between model answers and train a reward model. Then optimise the language model against that reward with PPO, with a penalty that keeps it from drifting too far from where it started. In the paper, people preferred outputs from a 1.3B InstructGPT model to outputs from the 175B GPT-3, a model more than a hundred times larger.

The paper also reported a cost. Tuning on preferences lowered scores on some public benchmarks, which it called an alignment tax, and it described mixing in some of the original pre-training objective to reduce that. This tension between what people prefer and what the model could do before is a theme to keep in view.

### November 2022: ChatGPT

ChatGPT was announced as a model trained with the same methods as InstructGPT, with changes to how the data was collected, so that it could hold a conversation. Whatever else it was, it showed that the finishing step mattered at least as much as raw scale for how useful a model felt. A base model and its tuned version can come from the same pre-training run and feel like different products. That is the reason this whole stage has its own lesson and its own research field.

Around the same time Bai and colleagues at Anthropic published the helpful and harmless work, which made the tension explicit. A model trained only to be helpful will help with things it should not. A model trained only to be harmless becomes evasive. Both are measurable, and both reappear in the benchmark results later in this note.

### December 2022: AI feedback and written principles

Human comparisons are slow and expensive, and they are hard to audit. [Constitutional AI](https://arxiv.org/abs/2212.08073) proposed asking a model to critique and revise its own outputs against a short list of written principles, and then training on AI-generated preference labels. The idea has become common in practice. Large preference datasets today are often ranked by models. It also moved the question of who decides what is good from thousands of anonymous annotators to a document you can read and argue with.

### 2023: removing the RL loop

PPO-based RLHF has many moving parts: a policy, a frozen reference copy, a reward model and a value network, all in memory at once, with unstable training. [Direct Preference Optimization](https://arxiv.org/abs/2305.18290) showed that you could skip the reward model and the RL loop. It trains directly on pairs of a preferred and a rejected answer, with a loss that raises the preferred answer's probability relative to the rejected one, measured against a frozen copy of the starting model. The same year Llama 2 described RLHF with a reward model at open-weights scale, and Zephyr showed that a small model could be tuned with DPO on a dataset ranked by another model. After that, preference tuning stopped being something only a few labs could do.

### 2024 and 2025: rewards that can be checked

For maths, code and tool use the answer can be verified by a program, so the human and the learned reward drop out. DeepSeekMath introduced [GRPO](https://arxiv.org/abs/2402.03300) and [DeepSeek-R1](https://arxiv.org/abs/2501.12948) showed what long reasoning could do with checkable rewards. This is the part of the field covered in [Preference tuning and RL](/lessons/preference-tuning-and-rl/) and followed through a real pipeline in [Post-training, end to end](/lessons/post-training/). Preference tuning and verifiable-reward RL now sit side by side: one for things people judge, the other for things a program can check.

## How preference tuning relates to safety

There is a gap between what the method does and what people sometimes hope it does, and the history shows where it opens.

**It optimises a proxy.** The reward model, or the labelled pairs behind DPO, is an approximation of what people want. Push hard against an approximation and you find answers that satisfy it without satisfying people. A study of reward model overoptimisation by Gao and colleagues measured this directly: as a policy is optimised harder against a fixed proxy reward, the proxy score keeps rising while the gold-standard score eventually falls. This is why RLHF has a penalty for moving far from the starting model, and why DPO uses a small beta and a low learning rate.

:::widget overopt

**People prefer to be agreed with.** Preference data records what annotators liked, and annotators sometimes like flattery. Several papers from 2022 and 2023, including work from Anthropic, found that models trained on human preferences can learn to tell people what they want to hear. This is the behaviour the benchmark's human-wellbeing domain checks for: sycophancy, delusion reinforcement and dependency.

**Refusal is a dial, not a switch.** Harmlessness training pushes a model toward declining. Pushed too far, it declines to help a security engineer defend a system. The benchmark in this note tests this directly by pairing each harmful request with a close benign one.

:::widget refusaldial

**It shapes behaviour, and it is not a guarantee.** A paper by Casper and colleagues surveyed open problems with RLHF, from noisy and biased labels to reward hacking and the difficulty of evaluating what you trained. Preference tuning changes what a model does by default. It does not give a proof about what it will do under pressure, in a long conversation, or against someone trying to break it.

All of this means two things for anyone reading a safety result. First, a benchmark number is a measurement of one slice of behaviour. Second, the training data's coverage sets the shape of what improves. The checkpoint below makes both concrete.

## The checkpoint

The model is a full-weight DPO checkpoint, one epoch, trained on LUMI. Its lineage on the card runs from the OpenEuroLLM prelude base, through a long-context anneal, to an instruction-tuned SFT checkpoint (`Neonkraft/oellm-9b-256k-theta64m-prelude-anneal300b-instruct-sft`), and then to this model. It is an Apache-2.0 research model, and the card says so plainly: not production-validated, not safety-certified.

The name says "threeway" because the run mixes three preference sources. The card is careful to add that three sources does not mean three equal shares.

| Source | Pairs used for training | Share | License |
|---|---:|---:|---|
| OpenEuroLLM Dolci-Instruct-DPO-translated | 1,352,763 | 93.84% | Apache 2.0 |
| Argilla UltraFeedback (cleaned) | 59,889 | 4.15% | MIT |
| NVIDIA HelpSteer3 (preference) | 28,895 | 2.00% | CC BY 4.0 |
| Total | 1,441,547 | 100% | |

A **pair** is one prompt with a chosen and a rejected answer. The trainer removed 43,191 of the 1,484,738 staged pairs (2.91%) because they were empty or longer than the 2,048-token limit. Separately, 15,824 pairs were used for validation.

### The data, read closely

Three things in that table are worth slowing down for.

**One source dominates.** Dolci provides 93.84% of the pairs. The checkpoint's behaviour is mostly a statement about that dataset. UltraFeedback and HelpSteer3 add variety in how pairs were made, but at 4% and 2% they have a light hand on the gradient. The card lists the heavy imbalance as a limitation, which is the honest way to put it.

**The labels come from different processes.** For HelpSteer3 the card says the sign of the overall preference chose the winner and the size was not used, and it excluded 2,257 tied rows. Dolci and UltraFeedback were converted into the same chosen and rejected format. The card does not say who or what produced the chosen and rejected answers in Dolci or UltraFeedback, and this note does not guess. When you use a preference dataset, that is a question to answer first, because it decides what "better" means in your model.

**Language coverage is narrower than the benchmark.** Dolci contributes 12 languages: Czech, German, Greek, English, Spanish, Finnish, French, Italian, Polish, Romanian, Swedish and Ukrainian. English alone has 243,752 staged training pairs, and French has 14,931. The benchmark covers 36 languages, so most of what it measures was not in the preference data. We will come back to what that means for the weakest language.

:::widget coverage

None of the three sources is described in the card as a safety dataset, and safety is not stated as a training target. The card presents them as general preference sources. Keep that in mind when we look at the safety scores.

### The recipe

The run uses TRL's DPO with the sigmoid loss and beta of 0.1. The reference is the frozen SFT checkpoint it started from. Learning rate is 5e-7 with a cosine schedule and 3% warmup, weight decay 0, an effective batch of 128 pairs, bf16, FlashAttention 2 and FSDP, seed 42.

The arithmetic checks out and is worth doing once: 1,441,547 pairs divided by 128 is about 11,262, and the card reports 11,263 optimiser steps. The run took 43 hours 21 minutes on 4 LUMI nodes with 8 MI250 GPUs each, which the card gives as about 1,387 GCD-hours (the card also gives about 694 billed MI250X GPU-hours). Next to pre-training this is small, which is part of why preference tuning is within reach of a university group.

Two settings carry most of the weight. Beta of 0.1 controls how strongly the model is held to its starting point: a larger beta ties it closer and a smaller one lets it move further. The very low learning rate of 5e-7 does the same job from the other side. Together they keep one epoch on 1.4 million pairs from rewriting what the SFT model already knew.

### What the training metrics say

On the 15,824 held-out pairs the card reports a preference accuracy of 0.8780, a reward margin of 2.9930 and a DPO loss of 0.2796. Here is how to read them.

DPO gives every answer an **implicit reward**: beta times the log of the ratio between the tuned model's probability and the reference model's probability. Accuracy is the share of held-out pairs where the chosen answer has the higher implicit reward. The margin is the average gap between chosen and rejected. The loss starts at ln 2, about 0.693, when the model has not moved from its reference, because every pair is a coin flip. A loss of 0.2796 means it now separates chosen from rejected much more often than not.

The loss for a single pair is easy to play with. Move the sliders to see why the early updates are large and the later ones fade, and what beta does.

:::widget dpo

The card is explicit about what this is not. These are agreements on a held-out mix of the same dataset families, with no comparison to a base model and no general benchmark. A high DPO accuracy says the model learned the preferences in the data. It does not say the preferences were the ones you wanted.

## What the benchmark measures

[EUROPA Alignment](https://birgermoell.github.io/europa-alignment/) is a v0.1 public development pilot. It is deliberately narrow, and its own documentation says so, which makes it easier to use well.

It has 576 items: 16 original English scenario templates repeated in 36 languages. The scenarios fall into six domains:

- **Refusal calibration:** refuse a harmful request, and help with a closely related benign one.
- **Human wellbeing:** sycophancy, delusion reinforcement, dependency and emotional manipulation.
- **Privacy and security:** personal data, prompt injection and defensive cyber help.
- **High-stakes advice and fairness:** medical uncertainty and discriminatory decision support.
- **Dangerous-capability boundaries:** direct and indirectly framed requests for harmful uplift, with the public scenarios leaving out real procedures.
- **Agentic control:** tool authorisation, honest reporting and complying with a stop instruction.

Open-ended answers are scored 0 to 4 on named dimensions by an LLM judge, which must be a different model from the one being tested. The published configuration uses gemma4:31b. A few items, the tool-authorisation and shutdown choices, are scored deterministically and strictly: the answer must be a single letter, and a right letter in the wrong format earns half credit and does not pass. Each item's score is the mean of its dimensions, capped by the worst failed critical dimension, so a response that fails on safety cannot score well on style.

The limitations are the useful part. The benchmark measures visible behaviour with safeguards active, not what a model could do with its safeguards removed. Only the English pack is authored. The other 35 are machine-translated and wait for native review. Sixteen items per language do not estimate a population-wide rate. LLM judges can be biased or inconsistent. A short scripted scenario can be passed by a model that fails under a long conversation or novel adversarial pressure. Scores should not be compared across different suite, judge or protocol versions as if only the checkpoint had changed. At the time of writing the project site's own front page lists no reviewed full-suite runs, so the numbers below are the model card's pilot results and the run linked from it, not independently reviewed ones.

## What moved

The card reports the starting SFT model, a checkpoint from step 9,000 of the DPO run (about 80% of the way through), and the final model, all on the same 576 items with the same judge.

| Domain | SFT start | Step 9,000 | Final DPO |
|---|---:|---:|---:|
| Agentic control | 60.9% | 91.4% | 91.0% |
| Dangerous-capability boundaries | 74.2% | 90.5% | 90.1% |
| High-stakes advice and fairness | 78.4% | 82.0% | 82.6% |
| Human wellbeing | 88.0% | 94.3% | 94.0% |
| Privacy and security | 79.9% | 86.5% | 87.9% |
| Refusal calibration | 78.5% | 87.7% | 85.2% |
| Overall | 77.3% | 89.5% | 89.3% |

The overall score rose 12.0 points from the SFT start, from 77.3% to 89.3%. Safety-critical gate failures fell from 71 to 39, with 36 at step 9,000. On the older EUROPA Eval, the same comparison went from 76.2% to 84.0%.

The same numbers, interactive. Switch the comparison to see which differences clear the noise.

:::widget checkpoints

Here is how I would read it, taking care to separate what the numbers show from what they suggest.

**The two largest gains are in agentic control (+30.1 points) and dangerous-capability boundaries (+15.9).** Both involve declining, escalating or stopping when asked. DPO pairs, even general ones, tend to prefer answers that are measured, that admit limits and that stop. That would explain why these moved, and it is a plausible reading rather than something the run isolates.

**The SFT comparison is not clean, and the card says so.** The SFT run predates a fix to how the model terminates its output. Agentic control items require a strict single-letter answer, so a model that keeps writing after the letter fails the format. Part of that 30-point gap may therefore come from decoding rather than from preferences. I would call this a hypothesis worth testing by re-running the SFT model with the fix, which is the first thing I would want to see before attributing the whole gain to DPO.

**More training did not help overall.** The final model is 0.2 points below step 9,000, a difference the card calls descriptive. Individual domains moved in opposite directions: privacy and security went up, refusal calibration went down from 87.7% to 85.2%. That is a small, honest picture of the dial from earlier. Tuning further bought some behaviours and cost others, and keeping the intermediate checkpoint is what lets anyone see it.

**The weak spots are in the same file.** The card lists a weakest language pack of 21.9% (Georgian) on the alignment benchmark and 28.5% (language not named) on the older EUROPA Eval, quantitative reasoning at 51.0%, five malformed-format responses, six prompt echoes and three repeated spans. The Georgian gap is related to the tokenizer, according to the run's author, and not to the preference data. A low score in one language is a reason to check the tokenizer before blaming the training stage.

**Mind the size of the instrument.** With 16 items per language, one item is worth 6.25 points of a language's score. For scale, if every item were simply pass or fail, 576 items at 89% would carry a margin of about 2.6 points, and the real uncertainty is larger because the same 16 scenarios repeat in every language and because the items are machine-translated. The 12-point gain is probably real in direction. The 0.2-point difference between step 9,000 and the final model is noise.

The card also notes that DPO did not teach reasoning traces. The chat template may emit an empty think block, which is not evidence of reasoning.

## Where things stand now

A few things are settled, and a few are open.

**What is settled.** Comparisons between answers are a practical training signal. A small beta, a low learning rate and a good SFT starting point give a stable run. You can do this on a university-scale budget in about two days. Held-out DPO metrics tell you the model learned the data, and a separate evaluation tells you whether it learned something useful.

**What the field has moved toward.** Preference data is increasingly model-ranked and often translated, and the main source in this run is a translated set. Verifiable rewards handle what a program can check, and preferences handle the rest. Reward hacking, sycophancy and over-refusal are the standard failure modes, and the better evaluations test for them in pairs, as EUROPA Alignment does with its harmful and benign requests.

**What is open.** Native-speaker review of translated safety items. Whether gains on short scripted scenarios hold in long conversations and under adversarial pressure. How much of a safety score comes from the preference data and how much from decoding, formatting and the starting model. Whether preference data in 12 languages carries over to 36, and if it does, how far.

## What to take from this if you are tuning a model

A short checklist drawn from the history and from this run.

1. **Start from a good SFT model.** DPO sharpens preferences. It does not teach the format or the knowledge from nothing.
2. **Know where your pairs came from.** Who or what chose the winner decides what "better" means. If the dataset card does not say, find out before you train.
3. **Check the mix.** If one source is 94% of your pairs, you are mostly tuning to that source.
4. **Keep beta and the learning rate small, and train one epoch to begin with.** Raise them only if the margins stay flat.
5. **Hold out validation pairs and read the margin.** Then generate from the model, because the margin cannot tell you what the answers look like.
6. **Evaluate on something that is not your training distribution.** Use paired tests that catch both under-refusal and over-refusal.
7. **Save checkpoints and compare them.** The step 9,000 versus final comparison above is the only reason we can say anything about the dial.
8. **Hold decoding constant across runs.** A terminal-token fix can look like an alignment gain.
9. **Report the limits next to the numbers.** The card for this checkpoint does, and that is why it can be read critically at all.

## Sources and links

- Model card and checkpoint: [birgermoell/oellm-9b-threeway-dpo-full-v1](https://huggingface.co/birgermoell/oellm-9b-threeway-dpo-full-v1)
- Benchmark: [EUROPA Alignment](https://birgermoell.github.io/europa-alignment/), with its [methodology](https://github.com/BirgerMoell/europa-alignment/blob/main/docs/METHODOLOGY.md) and [repository](https://github.com/BirgerMoell/europa-alignment)
- Training data: [NVIDIA HelpSteer3](https://huggingface.co/datasets/nvidia/HelpSteer3), [OpenEuroLLM Dolci-Instruct-DPO-translated](https://huggingface.co/datasets/openeurollm/Dolci-Instruct-DPO-translated), [Argilla UltraFeedback cleaned](https://huggingface.co/datasets/argilla/ultrafeedback-binarized-preferences-cleaned)
- Training code: [BirgerMoell/post-training](https://github.com/BirgerMoell/post-training/tree/64f3599)
- Papers: [Deep Reinforcement Learning from Human Preferences](https://arxiv.org/abs/1706.03741), [InstructGPT](https://arxiv.org/abs/2203.02155), [Constitutional AI](https://arxiv.org/abs/2212.08073), [Direct Preference Optimization](https://arxiv.org/abs/2305.18290), [DeepSeekMath (GRPO)](https://arxiv.org/abs/2402.03300), [DeepSeek-R1](https://arxiv.org/abs/2501.12948)
- Other works named above (PPO, Ziegler et al., Stiennon et al., Askell et al., Bai et al., Gao et al., Casper et al., Llama 2, Zephyr) are cited by name and year from memory of the literature and should be checked against the originals before being quoted.

## Where to go next

[Preference tuning and reinforcement learning](/lessons/preference-tuning-and-rl/) explains the mechanics with an interactive DPO loss and a group-advantage demo. [Post-training, end to end](/lessons/post-training/) follows a full pipeline, including a DPO stage and a weight merge, on another European 9B. [Evaluation](/lessons/evaluation/) covers how teams find out whether any of it worked.
