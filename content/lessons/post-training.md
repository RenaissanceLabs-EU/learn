---
title: How a base model becomes an assistant, end to end
slug: post-training
part: End to end
order: 18
level: Intermediate
minutes: 22
summary: Seven stages of post-training followed through one real model, Agora 9B, with its data, recipes, costs and scores, and interactive demos of loss masking, preference tuning, weight merging and reinforcement learning.
films: frontier-training:post, post-training:c01, rl-scaling:c01
related: base-training, supervised-fine-tuning, preference-tuning-and-rl, evaluation
sources:
- Agora 9B (GGUF build) | https://huggingface.co/birgermoell/agora-9b-GGUF
- Full model card, OpenEuroLLM 9B 256K after two RL windows (step 160) | https://huggingface.co/birgermoell/oellm-9b-256k-stage5-w2-rl-step160
- qwen35-posttrain, the SFT and DPO pipeline and playbook | https://github.com/BirgerMoell/qwen35-posttrain
- oellm-rlvr, the RL control plane, verifiers and data builders | https://github.com/BirgerMoell/oellm-rlvr
- Training language models to follow instructions with human feedback (InstructGPT) | https://arxiv.org/abs/2203.02155
- Direct Preference Optimization | https://arxiv.org/abs/2305.18290
- DeepSeekMath, which introduced GRPO | https://arxiv.org/abs/2402.03300
- DeepSeek-R1 | https://arxiv.org/abs/2501.12948
---
A [base model](/lessons/base-training/) predicts text. An assistant answers questions, follows instructions, reasons step by step when asked, calls tools, behaves safely and stops when it is done. The distance between the two is covered by **post-training**, which is a sequence of stages rather than one trick, and each stage fixes something the last one left or broke.

This guide follows one real model, **Agora 9B**, through all of them. Agora is a multilingual assistant for European languages with an opt-in thinking mode and tool calling. Its model card records the whole pipeline unusually openly: data, recipe, compute and the score after every stage, including a stage that made things worse. That is what makes it a good teaching case. Numbers on this page come from the card unless they are marked as illustrations.

:::flow
Instruct SFT | Learn to answer
Reasoning SFT | Learn to think first
Tool-use SFT | Learn to call tools
DPO | Prefer better answers
Merge | Win back what DPO cost
RL window 1 | Learn from checkers
RL window 2 | Broaden and shorten
:::

:::stats
7 | stages, one checkpoint each
~1,250 | A100 GPU-hours in total
3.14M | rows in the first SFT stage alone
23 | languages the model card lists
:::

Start with the whole journey. Click a stage, then change the measurement. Watch what happens to thinking-mode math, to the share of reasoning traces that finish, and to the validity of tool calls.

:::widget pipeline

## Stage 1: instruct SFT

The first stage is **supervised fine-tuning**: show the model good conversations and train it, with the same next-token loss as before, to reproduce the assistant's side ([SFT lesson](/lessons/supervised-fine-tuning/)). For Agora the data was 3.14 million rows and 2.37 billion tokens, drawn from the OpenEuroLLM instruction mix, the Dolci set translated into 12 languages, human-written non-English data from Aya, and rows that teach the model its own identity. One epoch, a learning rate of 8e-6, 394 GPU-hours.

Two details decide whether this works. First, the **chat template**: the model reads a flat stream of tokens, and roles are marked with special tokens. Agora uses ChatML, and every launcher refuses to train if the tokenizer or template differs from the pinned version. Second, the **loss mask**: the model reads the whole conversation but learns only from the assistant's tokens.

:::widget chatmask

Training efficiency comes from **packing**. Conversations are short and uneven, but GPUs want full, equal sequences. The stage used padding-free packing at 16,384 tokens, so no compute is spent on padding, and rows that are too long are dropped rather than truncated, because a cut-off answer teaches the model to stop mid-sentence.

:::widget packing

## Stage 2: reasoning SFT

Some questions deserve thought before an answer. A **thinking mode** has the model write out its reasoning between think tags and then answer. Stage 2 adds it as an opt-in: 373,000 reasoning rows, 1.74 billion tokens, mixed with 792,000 direct-answer rows as **replay**, so that learning to think does not erase the ability to answer briefly. This is a general principle in sequential training: mix in a sample of what you want to keep.

The switch is hard. The chat template either opens a think block or does not, so direct mode never produces think tags, and in thinking mode the opening tag is part of the prompt and is never trained. The model's job is to write the reasoning and close the tag. The learning rate drops to 5e-6, with 32K packing, to fit long traces. Cost: 351 GPU-hours.

At this point the model can reason, and the card's measurements show the catch. After this stage only 46 percent of thinking traces finish within 6,000 tokens, so thinking mode is weaker than direct mode on math (0.40 against 0.59). The model has learned the form of thought without learning when to stop. Stage 6 fixes that.

## Stage 3: tool-use SFT, and a bug worth knowing

To call a tool, the model writes a structured request in a tagged block and a program runs it. Agora uses the Qwen3 and Hermes format: tool definitions in the system turn, a call as JSON inside call tags, and results returned in a tool-response block inside a user turn. Stage 3 trained on 159,000 conversations in 16 languages, about 30 percent of them "do not call" examples, so that the model learns when a tool is not needed. It cost 68 GPU-hours.

The first version of this stage scored 0.000 on valid JSON. The cause was in the output layer. The tool and think tag tokens, ids 11 to 18, had started with nearly identical output rows, so the model could not tell them apart and closed calls with the wrong tag. The fix was to repair those eight rows and continue, and valid JSON went to 0.995. It is a good example of what the [note on practice](/notes/theory-and-practice/) is about: the theory said the data was right, and only reading the failing outputs found the cause.

## Stage 4: preference tuning with DPO

SFT shows the model what to say. It does not tell the model which of two plausible answers is better. **Direct preference optimisation**, DPO, trains on pairs: a chosen answer and a rejected one. It raises the probability of the chosen answer relative to a frozen copy of the starting model, and lowers the rejected one. No separate reward model is needed. Adjust the pair below.

:::widget dpo

Agora trained on 249,996 pairs: translated Dolci pairs in 12 languages, HelpSteer3, cleaned UltraFeedback, and 14,769 format-compliance pairs. In the last group the chosen answer is the verified bare answer, for prompts like "answer with the letter only", and the rejected one is the earlier model's own verbose or wrong reply. The settings were conservative: β of 0.1 and a learning rate of 5e-7, one epoch, with held-out preference accuracy of 0.85. Cost: 368 GPU-hours.

DPO helped the chat and safety scores, and it hurt the tool use. Valid JSON fell from 0.995 to 0.898 and valid arguments from 0.981 to 0.849, mostly because the model now ran on past the end of a tool call. The cause is in the data: none of the preference pairs contained tool calls, and all were direct mode. Training only on what you can measure damages what you did not include.

## Stage 5: merge

The remedy was not more training. It was arithmetic: average the weights of the checkpoint before DPO and the one after, half and half, tensor by tensor, in 32-bit precision. It takes minutes.

:::widget merge

Valid JSON recovered to 0.985 and valid arguments to 0.951, at about the same reasoning level, while chat quality kept rising (EUROPA Eval from 0.616 to 0.655). Averaging works here because the two checkpoints come from one lineage and sit close together in weight space. It is a cheap tool worth knowing, and a risky one on models that are far apart.

## Stages 6 and 7: reinforcement learning

SFT and DPO imitate examples. **Reinforcement learning with verifiable rewards**, RLVR, lets the model learn from outcomes instead. For each prompt the model writes several answers. A program checks each one. Answers that beat the group average become more likely. There is no human in the loop and no reward model to fool, only a checker.

Agora used **DAPO**, a variant of group-relative policy optimisation. Per update, 16 prompts with 8 sampled answers each. The method scales rewards within each group, uses no penalty term against the starting model, allows larger increases than decreases in probability, averages the loss per token, and, importantly, uses **dynamic sampling**: if all 8 answers score the same, the group teaches nothing and is replaced.

:::widget grpo

The infrastructure is a system of its own: four learner processes using DeepSpeed ZeRO-3 and four vLLM generation engines on two nodes, generation running two updates ahead of training and weights updated while answers are still being generated, with the output layer in 32-bit on both sides so that the sampler and the trainer agree.

The rewards are programs:

- **Math:** the final answer must be right, written in the prompt's language. In thinking mode, only text after one properly closed think tag is scored, so an answer inside an unfinished trace earns nothing.
- **Strict formats:** a bare correct answer scores 1; a correct answer after working earns partial credit that falls with length.
- **Code:** the reward is 1 only if all hidden tests pass, run in a contained, network-free sandbox.
- **Instruction following:** the share of verifiable constraints met, such as word counts, keywords, case and JSON.
- **Tool calls:** a layered score for well-formed calls, right names and right arguments.
- **Length:** a response cut off at the limit gets −0.5, and a smooth penalty discourages needless length.

:::widget toolreward

The first window, W1a, ran 128 updates over 2,048 prompts in 4 hours 26 minutes and cost 39 GPU-hours. Responses cut off at the limit fell from 41 percent to almost none, and the mean answer length from about 3,400 to 1,250 tokens, while reward rose. The reasoning traces now finished, and thinking-mode math jumped from 0.43 to 0.62.

The second window, W2, started from step 128 of the first and ran 160 updates over 2,560 prompts in 3 hours 41 minutes, 30 GPU-hours. It chose 806 math prompts by profiling the previous model: only those it solved between one and seven times out of eight, hardest first, so that more groups would carry a signal. About two thirds of the groups sampled were still all equal and were refilled. It added instruction following, code and multi-turn tool use. Truncation stayed below 2 percent, answers ran 600 to 950 tokens, and the mean reward rose from about 0.38 to 0.45. The result is the model you can run today.

## What changed, and what did not

Between the first SFT checkpoint and the final model, the card's numbers move like this: chat capability across 36 European languages from 0.600 to 0.727, safety and behaviour from 0.455 to 0.717, thinking-mode math from 0.402 (after stage 2) to 0.630, and the share of reasoning traces that finish from 46 to 86 percent. Tool calling reaches the best scores in the lineage, with 1.000 valid JSON and 0.972 valid arguments.

The card is equally direct about what is still weak:

- **Facts.** It rarely says "I don't know": it abstains on only 5 percent of factual questions, and 93 percent of its non-correct answers are confident guesses.
- **Documents.** Business documents with multi-step arithmetic score 0.38, against 0.74 for a comparison model, partly because it sometimes translates a required output keyword.
- **Refusals.** Refusal calibration (0.35) and grounding and safety (0.60) fell after DPO and did not recover in RL.
- **Code in thinking mode** dropped from the first RL window to the second, even as direct mode improved.
- **Language of thought.** Reasoning traces are mostly in English, because only the final answer's language was rewarded.

:::callout Key idea
Each stage fixes one thing and may break another. The way to keep control is to measure after every stage, on the same held-out tests, so that a drop is visible the day it happens.
:::

## The habits behind the pipeline

Reading the card as an operator, the technique matters less than the discipline:

1. **Pin everything.** One tokenizer and one chat template, checked by hash, and the launcher refuses to train otherwise.
2. **Drop, do not truncate,** rows that do not fit.
3. **Replay** what you want to keep when adding a new skill.
4. **Test what you did not train for.** DPO's pairs had no tool calls, and the tool score fell.
5. **Prefer cheap fixes first.** A merge took minutes and repaired what a stage of 368 GPU-hours had damaged.
6. **Spend compute where signal is.** The two RL windows used under 6 percent of the GPU-hours of the four supervised stages and gave the largest single jump in reasoning.
7. **Report the weak scores,** with the number next to the strength.

## Where to go next

[Base training, end to end](/lessons/base-training/) covers the model underneath. The lessons on [supervised fine-tuning](/lessons/supervised-fine-tuning/) and [preference tuning and RL](/lessons/preference-tuning-and-rl/) go deeper on single stages, and [Evaluation](/lessons/evaluation/) explains how numbers like those above are produced and why they carry error bars. The Agora model card links the code for every stage.
