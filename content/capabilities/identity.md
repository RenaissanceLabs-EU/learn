---
title: How to build and check it
---
A model has no inner sense of who it is. What it says about itself is learned text, so the right answers have to be in the training data.

### Start from a list of facts

Write the facts down first, each with its source, and build the conversations from them. When a fact changes, you fix it in one place and rebuild.

- The **name**, and who built it.
- The **knowledge cutoff**. State the real one. Models told not to guess the cutoff guessed anyway.
- The **languages** it covers, with an honest note on quality.
- Basic **model facts**: size and architecture.
- What it **cannot know**, such as today's date. The useful answer says what it knew at training time and that things may have changed.
- What to do when a **deployment renames it**: keep the given name, and say what it is built on when asked.

### How much data, and where

:::example The mix
About 5,500 conversations, used once, in supervised fine-tuning.
In a mix of one million rows that is about 0.5%.

For a larger or smaller mix, keep the row count, not the share.
:::

- **Put it in supervised fine-tuning**, before preference tuning or reinforcement learning.
- **Do not repeat it.** Repeated identity data makes the model talk about itself when nobody asked.
- **Clean the rest of the mix.** Rows elsewhere that say "As an AI developed by" another company will outvote a small identity set.

### How to check it

Hold out a set of questions with phrasings the model has not seen, in every language you train for. Add everyday questions that have nothing to do with identity.

| Metric | Gate | What it catches |
| --- | ---: | --- |
| Correct | at least 90% | Questions not answered correctly |
| Wrong | at most 3% | False claims about name, maker or cutoff |
| Worst category | at least 75% | A whole topic left unlearned |
| Right language | at least 95% | Answers in the wrong language |
| Overtrigger | at most 4% | Talking about itself in unrelated answers |

The worst-category gate is the one to copy. An average of 92% can hide a topic at 0%.

### When it fails

| Symptom | Likely cause |
| --- | --- |
| Names another company | Other data in the mix claims a different identity |
| Wrong cutoff | Stale cutoff claims elsewhere in the mix |
| Fine in English, weak elsewhere | Rows for some languages were filtered out |
| Talks about itself unprompted | Identity data repeated too often |
| Ignores a deployment's name | System-prompt rows dropped, or the template ignores them |
| Right after fine-tuning, wrong later | Later stages drift. Run the check after every stage |

The gates and the tables come from the OpenEuroLLM identity dataset card. The note [Who are you?](/notes/identity-datasets/) goes through that dataset in detail.
