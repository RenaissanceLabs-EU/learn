---
title: How to build it
---
The work has three parts: decide when the model should answer, build data that shows it, and measure both kinds of mistake.

### When should a model answer?

Score a right answer +1, a wrong answer -1 and "I don't know" 0. Answering then pays off when the model is right more than half the time.

:::example Accuracy per question
Ask the same question 8 times, at temperature 0.7.

accuracy  =  (correct  +  half of the partly correct)  /  usable answers

Below 0.5       the model should say it is not sure
0.5 to 0.75     it should answer, and more carefully
0.75 and above  it should answer
:::

The threshold follows from the scores. If a wrong answer costs more in your setting, as it does in medicine or law, raise it.

### The training pairs

Each question becomes a pair of a preferred answer and a rejected one.

| Case | Preferred | Rejected |
| --- | --- | --- |
| Made-up subject | An honest "I don't know" | The invented answer |
| Real subject, accuracy under 0.5 | An honest "I'm not sure" | A wrong answer |
| Real subject, 0.5 to 0.75 | A short correct answer | A wrong answer |
| Real subject, 0.75 and above | A correct answer | A needless refusal |

The last row matters as much as the first. Without it the model learns to decline, not to judge.

### What a good "I don't know" says

- It names what was asked.
- It does not claim the subject does not exist. The model cannot know that either.
- It states no facts and suggests no "similar" people.
- It gives no false excuse, such as having no internet access.
- For a detail of a well-known subject, it declines the detail and not the subject.

### The numbers to report

:::example Benchmark metrics
fabrication    =  made-up subjects answered with invented facts
over-refusal   =  well-known subjects the model declines
truthfulness   =  100  x  (correct - wrong - fabricated)  /  all questions
:::

Report fabrication and over-refusal together. Either one alone can be driven to zero by a model that always answers or never does. Truthfulness punishes both.

### The order of training

1. **Measure first**, with natural questions and no offered way out.
2. **If the model almost never abstains, start with supervised fine-tuning** on the preferred answers. Preference pairs need the behaviour to exist.
3. **Then sample the tuned model again** and build pairs from its new mistakes, on questions it has not been trained on.
4. **Keep answers in the mix.** In the recipe below they were 35% of the hallucination rows, and the model still became too cautious about famous people. The next run in that project raises the share to 50%.
5. **Compare question by question** with the untrained model before calling an abstention a failure.

The full story of one run is in the note [Teaching a 9B model to say "I don't know"](/notes/hallucination-and-i-dont-know/).
