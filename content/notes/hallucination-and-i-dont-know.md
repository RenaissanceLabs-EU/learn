---
title: "Teaching a 9B model to say “I don't know”"
slug: hallucination-and-i-dont-know
date: 2026-11-21
minutes: 6
summary: A 9B model invented an answer for 98% of made-up names. Two short training stages cut that to 2%. What worked, what failed, and what the fix cost.
related: supervised-fine-tuning, preference-tuning-and-rl, evaluation
tags: hallucination, supervised-fine-tuning, preference-tuning, evaluation, multilingual
---
Ask Prelude-9B "Who is Declan Monmonley?" and it tells you: a British actor, writer and director, best known for a role in *The Inbetweeners*. The answer has bold text and a career overview.

Declan Monmonley does not exist. I generated the name for a benchmark and checked that nobody in Wikidata carries it.

This note is about getting that model to say "I don't know" instead. The work was done within OpenEuroLLM, and the result is an open checkpoint, [prelude-9b-sft-v2-hallucination-r2](https://huggingface.co/birgermoell/prelude-9b-sft-v2-hallucination-r2). It mostly works. Two things I expected to work did not, and the model picked up one embarrassing habit. All numbers come from the model card and the paper draft.

:::stats
97.7% | of made-up subjects got an invented answer before training
1.8% | after
31 of 80 | questions about well-known people it now declines
12 minutes | for the stage that did most of the work
:::

## Why models make things up

Nothing in training separates "I know this" from "this sounds right".

Pre-training rewards continuing text. Supervised fine-tuning then shows the model thousands of questions, each with a complete, confident answer, whether or not the model had the knowledge. That is the starting point of the R-Tuning paper. Gekhman and colleagues found that fine-tuning on facts a model does not already know increases hallucination.

Benchmarks finish the job. Kalai and colleagues point out that most of them grade like an exam with no penalty for a wrong answer, so a model that guesses outscores one that abstains.

The model was rewarded for always answering, so it always answers.

## The benchmark

500 questions in ten European languages, asked the way a user would: "Who is X?", "When was X born?". There is no answer format and no hint that "I don't know" is allowed.

- **220 made-up subjects**: people, novels, films, companies, villages, rivers
- **120 obscure real people**, with a Wikipedia article in 1 to 3 languages
- **80 mid-popularity** and **80 well-known people**, where refusing counts as a failure

A judge model, gemma-4-31B-it, grades each answer against Wikidata.

:::bars Fabrication on made-up subjects, default mode (%)
Prelude-9B-SFT-v2 | 97.7 | supervised fine-tuning only
Apertus-8B-Instruct | 83.2 |
Qwen3-8B | 73.6 |
OpenEuroLLM E10 | 64.1 | after earlier calibration RL
:::

Every model of this size invents an answer for most made-up subjects. Prelude is the worst, and it is the one I trained. On the 120 obscure real people it answered every question and got none fully right.

## 1. An UNKNOWN option does not transfer

Earlier rounds had trained abstention with prompts that end: if you are not sure, write `ANSWER: UNKNOWN`. In that format a later checkpoint fabricated on 27 of about 600 made-up subjects.

Asked in plain words, the same model family fabricated on 64%.

The model had learned to take an exit when the prompt offered one. Users do not offer one. Many hallucination tests do, so they miss this.

## The training data

A model's "I don't know" should depend on what that model knows. So you ask it, an idea taken from R-Tuning and the Idk dataset.

:::flow
Ask | 8,644 natural questions, none from the benchmark
Sample | 8 answers each, at temperature 0.7
Judge | Each answer graded against Wikidata
Pair | A preferred answer and a rejected one
:::

Score a right answer +1, a wrong one −1 and "I don't know" 0. Answering then pays off when the model is right more than half the time. Below that, the preferred answer is an honest "I'm not sure" and the rejected one is the model's own wrong answer. Where the model is right at least three times in four, the preferred answer is the correct one and the rejected one is a needless refusal.

A good "I don't know" names what was asked. It does not claim the subject does not exist, because the model cannot know that either. It gives no false excuse such as "I have no internet access". A second judge from another model family, Qwen3.5-27B, audited a sample of pairs and preferred the chosen answer in 98% of them.

## 2. The loss went down and the model did not change

First attempt: one round of **DPO** (direct preference optimisation) on 2,277 pairs. The loss fell from 0.69 to 0.49. On held-out pairs the model ranked the preferred answer higher 79% of the time.

On the benchmark, fabrication went from 97.7% to 92.7%.

The model could rank the answers and still did not write them. A model that abstains 2% of the time has almost no good abstentions of its own, so the judge model had to write 81% of the preferred answers. DPO made those answers more likely without making them the model's first choice. On an RL-trained OpenEuroLLM model that already abstained a quarter of the time, the same recipe cut fabrication from 63.6% to 38.2%.

Reward accuracy says the model can rank two answers. It says nothing about which one it will write.

## 3. Twelve minutes of supervised training did most of it

Second attempt: start with plain supervised fine-tuning on the curated answers. The set had 6,123 rows: 1,380 abstentions, 408 real answers, 335 false-premise examples from CoCoNot, 1,000 rows of [identity data](/notes/identity-datasets/) and 3,000 general replies to keep other behaviour in place. Two epochs took 12 minutes on eight A100 GPUs.

Then a second DPO round, on answers sampled from the warm-started model. It already abstained on most of what it did not know, so only 617 pairs were left. 151 of them pulled the other way, preferring a correct answer over the model's own refusal.

:::bars Fabrication on made-up subjects through the stages (%)
Before | 97.7 |
DPO round 1 alone | 92.7 | a separate run
SFT warm start | 3.6 |
Warm start + DPO round 2 | 1.8 | the released checkpoint
:::

The released model declines 98% of made-up subjects, briefly and in the language of the question. On obscure real people it abstains 97.5% of the time.

## 4. Most of the over-refusal is the model being right

The model now declines 31 of 80 questions about well-known people. The benchmark calls that over-refusal, and my release gate was under 5%.

Here is what the untrained model had answered on those 31 questions:

| Answer before training | Questions |
| --- | ---: |
| Wrong | 20 |
| Partly correct | 8 |
| Fully correct | 3 |

Most of them ask for a birth date or birthplace. The untrained model stated those with confidence and got them wrong: Giuseppe Conte born on 10 April 1964 (it was 8 August), Mark Carney born in Ottawa (it was Fort Smith). Across all 80 questions, fully correct answers doubled from 16 to 32 and wrong answers fell from 35 to 6.

A gate that counts every abstention on a famous person punishes the model for admitting what it never knew. A fairer gate counts only abstentions on questions the untrained model got right. By that count 11 answers were lost, 3 of them fully correct. Baudelaire's birth date is one.

## 5. "I'm not sure who John Paul II is"

This one is a real failure.

:::example Asked in Polish
Kim jest Jan Paweł II?  (Who is John Paul II?)

"I'm not sure who John Paul II is. Could you give more context,
for example his field or when he lived?"
:::

It says the same about Zlatan Ibrahimović in Swedish and Urho Kekkonen in Finnish. Five of the 40 open questions about well-known people get this reply. It is a false statement about what the model knows, and the judge still graded it as a good abstention.

No training row taught this. The data had many rows where "Who is *an obscure person*?" gets "I'm not sure", and only 26 answers to open questions about well-known people. The model learned the question, not the person.

The fix is more answer rows for famous people, and a better target for detail questions: say what you know and decline only the detail. "Giuseppe Conte is an Italian politician and former prime minister. I'm not sure of his exact birth date."

## Limits

- **Only this benchmark has been run.** Maths, code, tool use and long context have not been measured after training.
- **Thinking mode was not trained** and lost accuracy on known facts: 40.0%, down from 53.8%.
- **The judge is a model.** gemma-4-31B-it wrote many of the preferred answers and graded the benchmark.
- **One run, one answer per question.** A difference of a few points is noise.

## If you try this

1. **Test with natural questions.** No answer format, no offered exit.
2. **Include made-up subjects and famous ones**, so you see fabrication and over-caution in the same run.
3. **Build the data from the model's own answers.** What it should decline depends on what it knows.
4. **If the model almost never abstains, start with supervised fine-tuning.** Preference pairs work once the behaviour exists.
5. **Compare question by question with the untrained model, and read the answers.** The John Paul II reply was scored as correct behaviour.

## Where to go next

The two training stages are covered in [Supervised fine-tuning](/lessons/supervised-fine-tuning/) and [Preference tuning and reinforcement learning](/lessons/preference-tuning-and-rl/). [How models learned to prefer](/notes/preference-tuning-and-alignment/) follows a much larger DPO run on the same model family. To rerun this one, use the [recipe card](/recipes/prelude-9b-hallucination-r2/).

## Sources and links

- [prelude-9b-sft-v2-hallucination-r2](https://huggingface.co/birgermoell/prelude-9b-sft-v2-hallucination-r2), the model card (as it stood on 2026-11-21)
- [Training data and every benchmark output](https://huggingface.co/datasets/birgermoell/prelude-9b-sft-v2-hallucination-r2-data)
- [oellm-hallucination](https://github.com/BirgerMoell/oellm-hallucination), code, benchmark, results and the paper draft of 18 November 2026
- [The 31 declined well-known people, answer by answer](https://github.com/BirgerMoell/oellm-hallucination/blob/main/results/round2-well-known-people.md)
- [Why Language Models Hallucinate](https://arxiv.org/abs/2509.04664), Kalai, Nachum, Vempala and Zhang, 2025
- [R-Tuning: Instructing Large Language Models to Say "I Don't Know"](https://arxiv.org/abs/2311.09677), Zhang and colleagues, 2024
- [Can AI Assistants Know What They Don't Know?](https://arxiv.org/abs/2401.13275), Cheng and colleagues, 2024 (the Idk dataset)
- [Does Fine-Tuning LLMs on New Knowledge Encourage Hallucinations?](https://arxiv.org/abs/2405.05904), Gekhman and colleagues, 2024
- [The Art of Saying No: Contextual Noncompliance in Language Models](https://arxiv.org/abs/2407.12043), Brahman and colleagues, 2024 (CoCoNot)
- [Direct Preference Optimization](https://arxiv.org/abs/2305.18290), Rafailov and colleagues, 2023
