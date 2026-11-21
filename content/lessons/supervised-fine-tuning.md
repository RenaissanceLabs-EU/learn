---
title: Supervised fine-tuning
slug: supervised-fine-tuning
part: After pre-training
order: 11
level: Intermediate
minutes: 8
summary: How a raw text predictor becomes an assistant by studying examples of good answers, and why a small, clean dataset can beat a large, messy one.
films: frontier-training:post, open-models:post
related: what-is-a-language-model, how-a-model-learns, preference-tuning-and-rl
sources:
- Finetuned Language Models Are Zero-Shot Learners (FLAN) | https://arxiv.org/abs/2109.01652
- Training language models to follow instructions with human feedback (InstructGPT) | https://arxiv.org/abs/2203.02155
- LoRA: Low-Rank Adaptation of Large Language Models | https://arxiv.org/abs/2106.09685
- QLoRA: Efficient Finetuning of Quantized LLMs | https://arxiv.org/abs/2305.14314
tags: supervised-fine-tuning
---
A freshly pre-trained model is a powerful text predictor, but it is not yet an assistant. Ask it "What is the capital of France?" and it may continue with "What is the capital of Germany?", because lists of quiz questions are common in its training text. It is completing a document, not answering you.

**Supervised fine-tuning**, usually shortened to **SFT**, closes that gap. The model is trained further on examples of the behaviour we want: a request followed by a good reply. The training signal is the same one used in pre-training, predict the next token, only the text is now different.

## Instruction data

An **instruction dataset** is a collection of pairs. Each has a prompt (a question, a task, a conversation so far) and a target response written to be the ideal answer. The responses come from people, from other models, or from a mix, with humans reviewing the results. The frontier training film describes it the same way: examples of good answers, written by people or by other models.

Early work showed how far this goes. The FLAN paper fine-tuned a model on many tasks phrased as instructions and found it handled tasks it had never seen. InstructGPT, which combined SFT with later stages, made a much smaller model preferable to people over a far larger one that had not been tuned.

:::flow
Pre-trained model | Predicts any text
Instruction pairs | Prompts with ideal replies
SFT | Next-token training on the replies
Assistant | Answers instead of continuing
:::

## Chat templates

A conversation has roles: a system message, the user, the assistant. The model only sees a flat stream of tokens, so those roles are marked with special tokens. The recipe for doing this is the **chat template**.

:::example A chat, as the model sees it
<system> You are a helpful assistant.
<user> What is the capital of France?
<assistant> The capital of France is Paris.<end>
:::

Real templates differ between model families, and the marker names above are only illustrative. Using the wrong template at inference time is a classic cause of strangely bad behaviour, because the model never saw that format during tuning. The final end marker matters too: it teaches the model when to stop.

## Loss on responses only

During SFT the model reads the whole conversation, but the loss is usually computed only on the assistant's tokens. The prompt tokens are **masked**: they are fed in as context but contribute nothing to the error. The reason is simple. We want the model to learn how to answer, not to get better at imitating the user's phrasing.

The picture below shows one conversation in three modes, and which tokens count toward the loss.

:::widget chatmask

Batches are built by **packing** many short conversations into each long sequence, so no compute is wasted on padding.

:::widget packing

## Quality beats quantity

Pre-training needs trillions of tokens. SFT works with far less, often thousands to hundreds of thousands of examples, which is a rule of thumb rather than a law. What matters is what the examples demonstrate.

:::callout Key idea
SFT mostly teaches a format and a style of behaviour: how to answer, how long, in what tone, when to refuse. A few thousand excellent examples usually do more than a million careless ones.
:::

Wrong answers, inconsistent tone and padding in the data are all copied faithfully. A model trained on confident but wrong replies learns to be confidently wrong.

## Training only a small part: LoRA

Updating every weight of a large model needs memory for the weights, the gradients and the optimizer's state, all at once. **Parameter-efficient fine-tuning** avoids this by training a small number of added parameters and leaving the original weights frozen.

The best-known method is **LoRA** (low-rank adaptation). Instead of changing a large weight matrix directly, LoRA learns a small correction built from two thin matrices whose product has the same shape as the original. Only the thin matrices are trained. The result is a small file that can be switched on or off, and training needs much less memory. QLoRA adds one more step: the frozen base model is stored in 4-bit form, so even a large model can be tuned on a single high-memory GPU.

## What SFT can and cannot teach

SFT is good at style, format, tool-call syntax, domain vocabulary and following instructions. It can surface knowledge the model already holds.

It is poor at adding large amounts of new knowledge reliably. It also cannot teach a model to be better than the examples it sees: if every demonstration is a human-written answer, the model is pushed toward imitating that level. Telling a good answer from a slightly better one is the job of the next stage, covered in [Preference tuning and RL](/lessons/preference-tuning-and-rl/).

## Catastrophic forgetting

**Catastrophic forgetting** is the tendency of a network to lose earlier skills when it is trained hard on something narrow. A model tuned only on legal summaries may get worse at arithmetic or at another language. Practical defences include a low learning rate, short training, mixing general examples back in, and LoRA, since the frozen base weights cannot be overwritten.

## Where to go next

Continue with [Preference tuning and RL](/lessons/preference-tuning-and-rl/) to see how models are pushed past what examples alone can show. For the mechanics of training itself, see [How a model learns](/lessons/how-a-model-learns/). The Post-training chapter of the frontier training film places SFT within the full pipeline.
