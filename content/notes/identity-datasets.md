---
title: "Who are you? How identity datasets teach a model about itself"
slug: identity-datasets
date: 2026-11-18
minutes: 12
summary: A model does not know its own name, who built it or when its data ends. Someone has to teach it. How identity data works, what goes wrong without it, and the OpenEuroLLM identity dataset as a worked example.
related: supervised-fine-tuning, evaluation, preference-tuning-and-rl
---
Ask a freshly trained model "Who made you?" and you will often get a confident, wrong answer. Models trained on web text have read a great deal about other models, so they say they are ChatGPT, or Qwen, or "a large language model trained by OpenAI". Nothing in pre-training told them otherwise.

A model has no inner sense of who it is. Everything it says about itself is **learned text**, the same as everything else it says. If you want it to answer correctly, you have to put the right answers in its training data. That data is called an **identity dataset**.

This note explains how identity data works, and uses one real dataset as an example throughout: the [OpenEuroLLM Model Identity](https://huggingface.co/datasets/birgermoell/openeurollm-model-identity) dataset, written for the Prelude model.

Everything about the dataset below comes from its dataset card. Where the card does not say, I say so.

## What an identity dataset is

An identity dataset is a set of short conversations about the model itself. The user asks, the assistant answers, and the answers are correct statements about the model:

- its **name** and **who built it**
- **which organisations** trained it
- its **knowledge cutoff**, the point after which it has seen no data
- which **languages** it covers, and how well
- basic **facts about the model**, such as its size and architecture
- what it **cannot know**, such as today's date or recent events
- what to do when a deployment gives it a different name

It is mixed into the training data in the supervised fine-tuning stage, in a small amount. See [Supervised fine-tuning](/lessons/supervised-fine-tuning/) for that stage.

:::callout Key idea
An identity dataset does not make a model aware of itself. It teaches the model to state a fixed set of true facts about itself, in natural words, when asked. The card for this dataset says it directly: "it does not make it introspect."
:::

## Where the idea comes from

The method follows the identity pattern from Andrej Karpathy's `nanochat` project, which the dataset card cites by name. In four steps:

1. **Describe the identity**, as a short list of facts.
2. **Generate varied conversations** that use those facts.
3. **Mix them into post-training.**
4. **Check that the behaviour emerged.**

The fourth step is the one people skip. A model that was trained on identity data may still say the wrong thing, and the only way to know is to test it. The example dataset ships its own test, and I come back to it below.

## The example: OpenEuroLLM Model Identity

The dataset teaches OpenEuroLLM's Prelude model to answer questions about itself. Version 3.1.0, the Prelude version, has:

| Item | Number |
| --- | ---: |
| Training conversations | 5,508 |
| Held-out validation conversations | 923 |
| Languages | 36 |
| Source scenarios in English | 26 |

The English scenarios are written by hand. The other 35 languages are machine-translated with `gemma-4-31B-it`. Every row is marked `synthetic`, with its provenance recorded in the fields `generation_method` and `translation_model`.

### Facts first, conversations second

The most important file in the repository is not the conversations. It is `identity_facts.json`, which holds every fact the data teaches, with its source. Each conversation row has a `fact_ids` field that says which facts it uses.

This is a good design for a reason you only see later. When a fact is wrong, you fix it in one place and rebuild, instead of searching thousands of conversations for the sentence that states it. And when someone asks "where did the model get that?", there is an answer.

The facts in version 3 are, as the card lists them:

- the **knowledge cutoff**: pre-training data collected until December 2025, annealing data in the first half of 2026
- **who trained it**: the full consortium of 12 universities and research organisations, 6 companies and 3 HPC centres when asked, and a one-line answer otherwise
- the **36 languages**, named, with an honest note that quality is highest in English and other high-resource languages
- **model facts**: about 9B parameters, a Qwen3-style architecture design but trained from scratch, about 10T plus 2T tokens
- **recent events and today's date**: say what was known when the model was trained, flag what may have changed, and offer to search when search is available

The card also says that the project's leadership names were removed in 3.0.0, because they are rarely asked about and a model can confuse names.

## What changed between versions, and why

The version history is the most useful part of the card, because each change records a real failure. The table below is adapted from it.

| Earlier problem | Fix in version 3 |
| --- | --- |
| Version 2 said the cutoff "must not be guessed". Models guessed anyway, for example "July 2024". | State the real cutoff. |
| Version 2 refused to list languages. Trained models then claimed to answer in English only. | Name all 36, with an honest note on quality. |
| Models built on a Qwen3-style design were mistaken for Qwen. | State that the design is Qwen3-like but the model is trained from scratch. |
| A bare "I don't know" about recent events is unhelpful, and a confident stale answer is wrong. | Say what was known as of training, flag what may have changed. |
| Answers had to fit every phrasing of a question, so they read stiffly. | Write each answer for the questions in its group. |
| Deployments rename the assistant. | Operator personas: when a system prompt names the assistant, keep the persona and stay honest. |

Two of these are lessons worth stating plainly.

**Refusing to answer does not work.** The earlier versions told the model not to guess the cutoff and not to list languages. The models guessed anyway, because a gap in training does not produce silence. It produces the most likely wrong answer. Giving a true answer is more reliable than forbidding a false one.

**Honest and useful are not opposites.** For things the model cannot know, such as today's date or last week's news, the answer is neither a refusal nor a bluff. It says what it knew at training time, says that things may have changed, and offers to search if it can.

### Version 3.1.0: giving the model a name

Version 3.0.0 says "an OpenEuroLLM language model". Version 3.1.0 adds the name: "I'm Prelude, an OpenEuroLLM language model", and "built on Prelude" when an operator persona is active. "Are you Prelude?" becomes one of the questions. The ten English strings that changed were re-translated into the other 35 languages.

The card handles the fact that other models need other names by shipping two tagged versions. `v3.0.0` is unnamed, for any OpenEuroLLM model, and `v3.1.0-prelude` is for Prelude and is what `main` points to. The facts that belong to one release (name, context length, licence) sit in one place in the build script, and unset values are left out of the data, with the answers pointing to the model card instead.

## Operator personas

A deployed model is often given a different name by whoever runs it: a bank's "Ava", a school's study helper. The assistant should play that role and still not lie about what it is.

The dataset covers this with rows that have a `system` turn naming the assistant. Under a persona the model answers with the persona's name and, if asked what it is built on, says it is built on Prelude. The card tells you to keep these system turns exactly as they are, and not to add a system prompt of your own to the other rows.

## How to use it without damaging the model

The card gives concrete instructions for the training mix, and they show what can go wrong.

- **Use all 5,508 rows, for one epoch, two at most.** That is about 0.5% of a 1M-row SFT mix. For a bigger or smaller mix, keep the same row count: "the point is the behaviour, not the share."
- **Do it in SFT, before preference tuning or RL.** Identity belongs with the supervised stage. See [Preference tuning and reinforcement learning](/lessons/preference-tuning-and-rl/) for what comes after.
- **Do not upsample.** Repeating identity data makes the model talk about itself where nobody asked. The card calls that **overtrigger** and measures it.
- **Never train on the validation split.** It is the test set.
- **Measure before training too**, so you can see what changed.

Overtrigger is a failure that is easy to miss. A model that answers "Who wrote Hamlet?" with "Shakespeare, and by the way, I'm Prelude, an OpenEuroLLM model" has learned identity too well. The evaluation checks for it.

## How to check it worked

The dataset ships an evaluation script, `eval_identity.py`. It runs on any checkpoint, uses a judge model (the card used `gemma-4-31B-it`), and asks two sets of questions.

- **Identity.** The opening question of each of the 923 validation conversations, in 36 languages, with phrasings never seen in training and operator-persona prompts included. The judge compares each answer with the facts and the reference answer and labels it `CORRECT`, `INCOMPLETE` (dodges or misses the point) or `WRONG` (states something false about itself). It also checks that the answer is in the language of the question.
- **Overtrigger.** 50 everyday questions in 10 languages. The answer must not mention Prelude, OpenEuroLLM or the consortium.

The report prints PASS or FAIL against five gates:

| Metric | Gate | What it catches |
| --- | ---: | --- |
| `identity_correct` | ≥ 90% | Questions not answered correctly |
| `identity_wrong` | ≤ 3% | False claims: wrong name, creator, cutoff, invented specs |
| `worst_category_correct` | ≥ 75% | A whole topic left unlearned |
| `language_ok` | ≥ 95% | Answers in the wrong language |
| `overtrigger` | ≤ 4% | Talking about itself in unrelated answers |

The worst-category gate is the clever one. An average of 92% can hide a topic at 0%. Requiring every category to clear a floor forces the weak topic into view.

### A real before-picture

The card reports one run before training on this version. It is the project's RL checkpoint, trained with identity version 1.0.0, judged on 13 November 2026:

| Metric | Before | Gate |
| --- | ---: | ---: |
| `identity_correct` | 52.8% | ≥ 90% |
| `identity_wrong` | 38.6% | ≤ 3% |
| `language_ok` | 96.2% | ≥ 95% |
| `overtrigger` | 0% | ≤ 4% |
| Worst category | 0% | ≥ 75% |

The weakest categories were the knowledge cutoff and the model specifications. The typical failures the card lists are inventing consortium partners, stating a wrong cutoff ("October 2023"), saying the model cannot be downloaded or pointing to OpenAI, and listing only English as its language.

This is the reason to measure first. An older identity dataset had been used, and the model was still wrong more than a third of the time on questions about itself. I have not seen results after training on version 3.1.0, because the card does not report any. The table is the starting line, not the finish.

The card also notes that the judge is somewhat strict. For example, "I don't store messages" counts as wrong, because storage depends on the service. Since the judge is equally strict before and after, you compare runs instead of reading the absolute numbers too literally.

## When it fails

The card has a troubleshooting table, and it teaches more about identity data than a description would.

| Symptom | Likely cause |
| --- | --- |
| Says "I'm ChatGPT" or names another company | Other SFT data with foreign identity claims outweighs this set. Filter rows like "As an AI developed by OpenAI ...". |
| Wrong knowledge cutoff | Stale cutoff claims elsewhere in the mix. |
| Fine in English, weak in some languages | Too few rows reached those languages, because a pipeline filtered or capped them. |
| A category below 75% | That topic conflicts with other data, or was filtered. Read ten failing answers. |
| Overtrigger is high | Identity data repeated too often. |
| Ignores operator personas | System-prompt rows were dropped, or the chat template ignores system prompts. |
| Fine after SFT, worse after DPO or RL | Later stages drift. Run the evaluation after every stage. |

The first two rows share a lesson: **identity is a property of the whole data mix, not of one dataset.** A small identity set of about 0.5% cannot outvote a large body of other data that says the opposite. If a million rows of copied chatbot conversations say "I am ChatGPT", the model learns that. Cleaning the rest of the mix is part of the job.

The last row is the connection to the rest of training. A model can be right after SFT and wrong again after reinforcement learning, because those stages change the weights and nothing is guarding the identity facts. Hence the advice to run the check at every stage. See [Evaluation](/lessons/evaluation/) for the general habit.

## Limits worth knowing

The card lists them, and they apply to most identity datasets.

- **The conversations are synthetic.** Non-English text is machine-translated and has not been checked by native speakers in every language. The card says low-resource languages such as Maltese, Irish and Icelandic need the most review.
- **Registers drift.** Strings are translated one at a time, so a few conversations switch between formal and informal address, for example French *vous* and *tu*.
- **Facts go out of date.** The partner list is as of 13 November 2026 and can change, so the answers point to the project website.
- **It states, it does not introspect.** The model repeats facts. It has no way to look at itself and check.
- **A model's answer is not an official statement** by the consortium.

## A checklist for your own identity data

1. **Write the facts first**, each with a source, before any conversation.
2. **State what you know and say what you do not.** Give the real cutoff, name the languages, and write a useful answer for what cannot be known.
3. **Write natural answers** for the question being asked. A recited paragraph reads as a script.
4. **Cover every language you train for**, and check that they survive your data pipeline.
5. **Support operator personas** if the model will be deployed under other names.
6. **Mix in once, about 0.5% of the SFT data**, without upsampling.
7. **Clean the rest of the mix** of rows that claim another name, creator or cutoff.
8. **Keep a held-out set** and measure before and after, including overtrigger and the worst category.
9. **Run the check after every stage.**
10. **Version it.** Name, release facts and dates change, and the tag tells you which data a model saw.

## Where to go next

For the stage identity data goes into, see [Supervised fine-tuning](/lessons/supervised-fine-tuning/). For the habit of measuring before and after, see [Evaluation](/lessons/evaluation/). For what happens to behaviour in the later stages, see [Preference tuning and reinforcement learning](/lessons/preference-tuning-and-rl/) and the note [How models learned to prefer](/notes/preference-tuning-and-alignment/). For another small, careful dataset that is built from rules and tested against baselines, see [Models that decide](/notes/decision-models-jev-kev-sven/).

## Sources and links

- [OpenEuroLLM Model Identity](https://huggingface.co/datasets/birgermoell/openeurollm-model-identity), the dataset card, which all figures above come from (version 3.1.0, as it stood on 2026-11-18)
- [Guide: infusing identity to your nanochat](https://github.com/karpathy/nanochat/discussions/139), Andrej Karpathy, the method the dataset follows (linked from the card)
- [OpenEuroLLM](https://openeurollm.eu/), the project website that the facts and the card point to
