---
title: "Models that decide: Jev, Kev and Sven, from a hosted API to Swedish authority cases"
slug: decision-models-jev-kev-sven
date: 2026-11-18
minutes: 14
summary: A decision model does not write text. It reads a case and answers typed questions with a probability. How the design works, how Kev made it open, and what two small Swedish derivatives learned and did not learn.
related: supervised-fine-tuning, evaluation, preference-tuning-and-rl
---
Most of this site is about models that write. This note is about a different kind: models that **decide**. You give one a text and a question with a fixed set of answers, and it returns a probability for each answer. It does not produce a sentence. It does not explain itself. In one pass through the network it picks.

The family has a hosted member, **Jev**, which is served as an API by TypeSafe. It has an open reimplementation, **Kev**, by Jared Palmer. And it has Swedish derivatives, **Sven** and two models trained on Swedish authority cases, which I trained. This note goes through the design, the choices behind it, and what the numbers in the three model cards actually support.

Everything below comes from the model cards, the Kev README and the dataset card. Where a card says something is not known, I say so.

## What a decision model is

An ordinary language model is asked to produce text, one token at a time, and a program then has to parse that text to find the answer. That is where things go wrong: the model answers "Probably yes, but it depends" when you wanted `yes` or `no`, or invents a label that does not exist.

A decision model removes the problem by construction. A request has a **state**, which is the text to read, and any number of **questions** about it. Each question is one of three types:

| Type | What it asks | Answer |
| --- | --- | --- |
| `noul` | A yes/no question | A probability for yes and for no |
| `choice` | Pick one of several options | A probability for each option |
| `score` | A rating on a scale, for example 0 to 4 | A probability for each rating |

The answer is always one of the listed options, so there are no type errors to handle. And since every answer comes with a probability, a program can act on the confident ones and send the rest to a person.

:::callout Key idea
A decision model trades generality for control. It cannot write, but it always answers in the format you asked for, in a fixed and small amount of compute, with a number that says how sure it is.
:::

## How it works inside

Kev describes its design in a few lines. A checkpoint is a **LoRA adapter** (a small set of trained weights added to a frozen base model, rank 16) plus a **pointer head**, a tiny extra layer. The text fed to the model looks like this:

```text
<state> ...the case...
<q> instructions <opt> option 1 </opt> <opt> option 2 </opt> ... <decide>
```

The model reads the state and the question. The pointer head then compares the model's internal representation at each option's `</opt>` marker with its representation at the final `<decide>` marker, and a softmax turns those scores into probabilities. Because `<decide>` comes last, it can attend to all the options at once.

Three details matter for what follows.

- **Questions cannot read each other.** Several questions can share one state, but the answer to one does not depend on another. The state is computed once and reused, which is why a request with five questions is cheap.
- **Training is plain cross-entropy** on the correct answer. There is no reward model and no reinforcement learning here, and the Kev README states that no Jev outputs were used for training.
- **Option order still matters a little.** Questions are isolated from each other, but options within a question can influence one another. Sven's card lists option-order sensitivity as a known limit.

For the background on adapters and fine-tuning in general, see [Supervised fine-tuning](/lessons/supervised-fine-tuning/).

## Jev and Kev

**Jev** is the hosted model. What it was trained on is not public, and the Kev README says as much: "we don't know what Jev was trained on". Its architecture is described in an outside write-up by Archer Hume, linked from the Kev README.

**Kev** is a family of small open decision models built to match that architecture and the TypeSafe System One API, so the TypeSafe Python client works against a Kev server unchanged. Kev 1.0 has four sizes:

| Model | Base | Index on held-out datasets |
| --- | --- | ---: |
| Kev-0.8B | Qwen3.5-0.8B-Base | 23.3 |
| Kev-4B | Qwen3.5-4B-Base | 38.0 |
| Kev-9B | Qwen3.5-9B-Base | 41.0 |
| Kev-27B | Qwen3.8-27B (post-trained) | 52.3 |
| Jev | Hosted | 54.0 |

On sources the models never trained on, the README reports Kev-27B at 0.851 accuracy on its development set against Jev's 0.857, and Kev-4B at 0.817. The README is careful to add that this is not a controlled comparison, since nobody outside TypeSafe knows Jev's training data.

Two choices in Kev are worth noticing because they come back later.

1. **Calibration is part of the checkpoint.** Each Kev ships with a fitted **temperature**, a single number that sharpens or softens its probabilities. A temperature never changes which answer wins. It only makes "90% sure" mean something closer to "right 9 times in 10". The README reports that Kev-9B puts at least 0.9 probability on a wrong answer for 2.4% of new-source questions, against Jev's 3.7%.
2. **Fine-tuning starts from the released model, not from the base.** The README gives a test where a fine-tune from the base scored 0.33 on Kev's own evaluation set, against 0.84 for the released model, and the same data trained on top of the released model kept 0.83 and reached 0.88 on the new domain. The method is called `--init_from`, and it is the reason the next two sections are possible at all. I call it a **delta fine-tune**: a small update on top of something already good.

## Sven: teaching Kev Swedish

Kev is trained mostly on English. **Sven-0.6B** is a delta fine-tune of a 0.6B Kev, adapted to Swedish. Its card describes it as a Swedish System One decision model, and its intended uses are the practical ones: routing customer service messages, triaging email, flagging phishing and prompt injection, classifying incidents.

The decisions made when building it:

| Decision | Choice | Why it matters |
| --- | --- | --- |
| Starting point | Kev-0.6B (Qwen3-0.6B-Base) | Keeps what the English recipe already knows |
| Learning rate | 2e-5, two epochs | Small, so the Swedish delta does not wash out the base |
| Swedish data | 5,000 English records machine-translated with `Helsinki-NLP/opus-mt-en-sv` | Cheap, and it covers the same questions as the English suite |
| Hand-written data | 36 Swedish seed records | Real Swedish for routing, phishing, incidents, GDPR and prompt injection |
| Replay data | 200 English records from the upstream suite | A guard against drifting away from the original recipe |

The replay records are the most instructive choice. Fine-tuning on a new language can quietly damage what the model could do before, so a small sample of the old data is mixed in. The result suggests it worked: the card reports that Sven keeps within 1 point of upstream English accuracy.

| Evaluation | Accuracy | Brier | ECE |
| --- | ---: | ---: | ---: |
| Swedish held-out | 0.745 | 0.331 | 0.079 |
| English, same distribution | 0.794 | 0.299 | 0.090 |
| English, new domain | 0.623 | 0.536 | 0.146 |

**Brier** is a score for the whole probability distribution, where lower is better. **ECE** (expected calibration error) is the average gap between how confident the model says it is and how often it is right.

Inside the Swedish set, yes/no questions score 0.863, multiple-choice 0.751 and rating questions 0.520. The card does not hide this: ratings are the weak spot, and it says the cause is capacity and the length of the Swedish criteria, not a lack of data. The planned fix is a 4B backbone.

The way to use the probabilities is shown in one line of the card. The Swedish set scores 0.745 overall, but the model answers 0.947 correctly on the 50% of questions where it is most confident, and about 0.90 at confidence 0.9 and above. That is the point of a model that reports a number: you automate the part it is sure about.

The card is also open about the data. Machine-translated labels carry translation noise, one long review showed visible truncation, and most translated records keep English option keys, so Swedish option handling is narrower than the text coverage.

## Swedish authority cases

The other two models, **sven-myndighet-0.6b** and **kev-myndighet-4b**, take the idea in a different direction: from short business messages to the work of a Swedish *handläggare*, the case officer at an authority who decides on an application or an appeal.

The data is the `sven/` folder of the Myndighetsbeslut dataset, 16,632 records: 12,918 for training, 1,709 for development and 2,005 held out. The same cases also exist as environments with programmatic rewards, so one dataset serves both this kind of model and reinforcement learning with verifiable rewards. The case file is the state. The questions are typed: what is the outcome, what is the next procedural step, is the authority criticised.

| Source | Where the labels come from |
| --- | --- |
| CSN student aid | A rule engine over the statute, on synthetic cases |
| Procedural next step | A rule engine over förvaltningslagen, on synthetic cases |
| Skolinspektionen | Published supervision decisions, labels derived by rules from the decision text |
| ÖKS and ÖNH | Published appeal decisions, split by date |
| JO | Published supervision decisions |

Two models were trained on it, both as delta fine-tunes with LoRA rank 16 at learning rate 2e-5.

| | sven-myndighet-0.6b | kev-myndighet-4b |
| --- | --- | --- |
| Start | birgermoell/sven-0.6b | jaredpalmer/kev-4b |
| Base | Qwen3-0.6B-Base | Qwen3.5-4B-Base |
| Epochs | 2 | 1 |
| Time | 85 minutes | 6.5 hours |
| Hardware | 1 × H200 | 1 × H200 |

Both ran on the NSC Berzelius cluster. At serving time they need one setting that is easy to miss: `--max_state 7552`. Kev's default evaluation limit of 384 tokens rejects most case files, which are long.

### The decisions in the data

Several choices here do more for the credibility of the results than any training setting.

- **Split by date, not at random.** Real decisions are split so that training ends 2025-12-19 and the held-out set runs from 2026-05-07 to 2026-11-10. A random split would let the model see a case from the same week in training. The card still flags that a decision can quote an earlier one, and 39 of 578 Skolinspektionen records do.
- **Always compare with the most common answer.** Every table shows the share of the single most common answer next to the model's score. A model that always says "avslag" can look good when most decisions are refusals, so beating that number is the first bar.
- **Always compare with zero-shot.** The same adapter-free model is run first. That separates what training added from what the base already knew.
- **Say what is synthetic.** The CSN and next-step cases come from rules, with invented names. The card says in its first limit that high scores there show the model learned the generator's rules, not that it can read a real case file.

### What the numbers say

Accuracy on the 2,005 held-out records.

| Question | Most common | 4B zero-shot | 0.6B trained | 4B trained |
| --- | ---: | ---: | ---: | ---: |
| CSN outcome | 0.50 | 0.30 | 0.83 | 0.97 |
| Procedural next step | 0.28 | 0.71 | 0.93 | 0.95 |
| Skolinspektionen: intervention | 0.54 | 0.38 | 0.81 | 0.85 |
| Skolinspektionen: deficiency per area | 0.66 | 0.80 | 0.88 | 0.90 |
| ÖKS: changed in appellant's favour | 0.86 | 0.94 | 0.86 | 0.96 |
| JO: authority criticised | 0.87 | 0.60 | 0.86 | 0.87 |
| ÖNH: outcome | 0.35 | 0.50 | 0.21 | 0.38 |

Reading it from the top:

- **CSN and next step** move from below the majority baseline to the 0.8 to 0.97 range. That is real learning, but of rules. The data is generated from rules, so a model that finds the rules scores very high without reading anything in a real file.
- **Skolinspektionen** is the clearest real result. There are 1,616 training decisions, the labels come from real documents, and the 4B model reaches 0.85 on intervention where the best constant answer gives 0.54 and zero-shot gives 0.38.
- **ÖKS** looks good at 0.96, but there are only 72 held-out questions and about 10 upheld appeals, and zero-shot Kev-4B already scored 0.94. The card says plainly that earlier exposure to these public decisions cannot be ruled out. The difference between 0.94 and 0.96 is noise.
- **JO is not learned.** The 4B model scores 0.87, exactly the majority class, so it is saying "criticised" every time. A score equal to the baseline is not a result.
- **ÖNH goes the wrong way** for the small model: 0.21 trained, below its own zero-shot 0.32. The held-out set has 34 questions, so the card draws no conclusion, and neither should anyone else.

The pattern in these rows is the most useful thing about the project. Training helps most where there is a lot of structured data with a clear signal, and not at all where the data is small or the label is mostly one answer.

:::callout Key idea
A score only means something next to two other numbers: what a model that always gives the common answer would score, and what the model scored before you trained it. Without both, a high accuracy tells you very little.
:::

### What is not known

The cards list the open questions themselves, and they are worth repeating.

- No replay data was mixed in for either authority model, and general ability afterwards has not been measured. Sven-0.6B used replay and kept its English accuracy, and the authority models did not, so it is an open question whether they lost something.
- Nothing has been reviewed by a case officer. The CSN rule engine reproduces CSN's published weekly amounts and all 78 cells of its income-ceiling table, which is evidence that the arithmetic is right, not that the model should decide real cases.
- Both are marked as experimental research releases. Any use needs a responsible decision maker, and the models give a proposal, not a decision.

## Why use a decision model at all

A large chat model can answer all of these questions too, and it can explain itself. A reasonable person asks why bother with a small decision model.

- **Cost and speed.** The Kev README gives Kev-4B 18.1 ms for six questions about a new short text on an H100. A model that writes an answer cannot match that, because it has to generate tokens one by one.
- **A fixed format.** The output cannot be malformed. For a pipeline, that is worth more than an elegant explanation.
- **Calibrated confidence.** You can set a threshold and route the doubtful cases to a person. The Kev README reports that at a 5% error budget the larger Kevs can automate 0.52 to 0.69 of new-source decisions.
- **Local and open.** The weights are Apache-2.0 and run on one GPU or a laptop. For personal data and public administration, keeping the model in your own building is a real argument.

The cost is that the model is only as good as its questions. It decides what you asked, it does not notice that you asked the wrong question, and it cannot tell you why.

For public administration there is one more reason to be careful. Writing a decision that a citizen can read and appeal needs reasons, and a probability is not a reason. The sensible position, and the one the cards take, is a **proposal for a human to review**, with the model's confidence used to decide which cases deserve a closer look.

## A checklist for building your own

Pulled from the choices above, in the order you would meet them.

1. **Start from something that already works.** Fine-tune from a released checkpoint with a small learning rate, not from the base.
2. **Write the questions before the data.** The type (choice, yes/no, score) and the option list decide everything else.
3. **Split by time when you can.** If decisions come in sequence, test on the future.
4. **Report the constant baseline and the zero-shot number** beside every score.
5. **Mix in a little of the old data** if general ability matters, and then measure it. Neither authority model did either of those things, and the cards say so.
6. **Count the questions before reading the percentage.** 72 and 34 held-out questions do not support a ranking.
7. **Calibrate, then threshold.** Fit a temperature, check the confident wrong answers, and pick the cutoff on data you did not tune on.
8. **Keep a person in the loop** for anything with consequences, and use the probability to decide where.

## Where to go next

For the idea of learning from labelled examples instead of from preferences, see [Supervised fine-tuning](/lessons/supervised-fine-tuning/). For how to tell whether a result is real, see [Evaluation](/lessons/evaluation/). For the other side of the post-training story, where a model learns from comparisons and checkable rewards, see [Preference tuning and reinforcement learning](/lessons/preference-tuning-and-rl/) and the note [How models learned to prefer](/notes/preference-tuning-and-alignment/). The Myndighetsbeslut dataset has the verifiable rewards for the same authority cases, so it can serve as an RL environment too.

## Sources and links

All figures come from these pages as they stood on 2026-11-18.

- [kev-myndighet-4b](https://huggingface.co/birgermoell/kev-myndighet-4b), model card
- [sven-myndighet-0.6b](https://huggingface.co/birgermoell/sven-myndighet-0.6b), model card
- [sven-0.6b](https://huggingface.co/birgermoell/sven-0.6b), model card
- [Myndighetsbeslut](https://huggingface.co/datasets/birgermoell/myndighetsbeslut), dataset card with per-question results
- [Kev](https://github.com/jaredpalmer/kev), code, model family and evaluation, by Jared Palmer
- [myndighetsagenter](https://github.com/BirgerMoell/myndighetsagenter), data builders, rewards and the evaluation script
- [Jev's Architecture Unmasked](https://archerhume.com/posts/jevs-architecture-unmasked), the outside write-up of Jev's architecture that the Kev README points to. I have not read it, so I do not describe Jev beyond what the Kev README says.
