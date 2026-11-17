---
title: What a language model actually is
slug: what-is-a-language-model
part: The basics
order: 1
level: Beginner
minutes: 6
summary: A language model is a function that predicts the next piece of text. Everything else, from chat to code, is built on top of that one trick.
films: frontier-training:hook, open-models:hook
related: tokens, how-a-model-learns
sources:
- Attention Is All You Need | https://arxiv.org/abs/1706.03762
- Language Models are Few-Shot Learners (GPT-3) | https://arxiv.org/abs/2005.14165
---
Start with a game. Read "The capital of France is" and guess the next word. You said "Paris" without effort, and you were right because you have seen that sentence completed many times before.

A **language model** plays exactly this game, at enormous scale. Given some text, it outputs a probability for every possible next piece of text. "Paris" gets a high one. "banana" gets a tiny one. That is the whole job description.

:::flow
Text so far | "The capital of France is"
Model | A very large function
Next-piece probabilities | Paris 92%, the 2%, a 1%, …
Pick one | Sample or take the most likely
:::

## One step at a time

A model does not write a paragraph at once. It predicts one piece, adds it to the text, and predicts again. A chat reply of 300 words is hundreds of these small steps in a row, each one conditioned on everything written so far, including the model's own earlier output.

This is why the same model can answer a question, continue a story and complete a function in a programming language. All three are "what text most plausibly comes next, given this text?"

:::callout Key idea
A language model does not look anything up. It computes a probability for each possible continuation from numbers learned during training.
:::

## Where the knowledge lives

Inside the model is a large collection of numbers called **parameters**, or **weights**. A modern frontier model has hundreds of billions of them. Stored on disk, the model is just that list of numbers, which is why people say a model is "a file".

Nobody writes those numbers by hand. They are found by showing the model a huge amount of text and nudging the numbers, again and again, so that its guesses about the next piece get slightly better. That process is **training**, and the rest of this course is about how it works and what it costs.

:::stats
Billions | of parameters in a large model
Trillions | of text pieces seen during training
Months | of work on thousands of chips
:::

## Why a simple task teaches so much

To predict the next word well across all of human writing, a model has to pick up grammar, facts, the structure of arguments, the conventions of code and a rough sense of how people behave. Nothing in the task asks for these things directly. They appear because they help the guess.

This is also where the limits come from. The model is trained to produce text that is plausible, not text that is verified. Later stages of training, covered in [Supervised fine-tuning](/lessons/supervised-fine-tuning/) and [Preference tuning and RL](/lessons/preference-tuning-and-rl/), push it toward being helpful and accurate, but the underlying mechanism stays the same.

## Pieces, not words

The model does not see words. It sees **tokens**: small chunks of text, often a word or part of a word. "Unbelievable" might be three tokens. Working in tokens keeps the vocabulary a manageable size and lets the model handle any language, code or typo.

## Where to go next

Next, [Tokens](/lessons/tokens/) shows exactly how text is cut into pieces. After that, [Attention and the transformer](/lessons/attention-and-the-transformer/) explains the machinery that turns those pieces into a prediction. If you prefer to watch first, the opening of the frontier training film sets out the whole pipeline in under a minute.
