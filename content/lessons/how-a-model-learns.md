---
title: How a model learns
slug: how-a-model-learns
part: The basics
order: 4
level: Intermediate
minutes: 9
summary: Training is a loop that measures how surprised the model was by real text and nudges its parameters to be less surprised next time.
films: frontier-training:recipe, frontier-training:scaling
related: attention-and-the-transformer, pretraining-data
sources:
- Adam: A Method for Stochastic Optimization | https://arxiv.org/abs/1412.6980
- Scaling Laws for Neural Language Models | https://arxiv.org/abs/2001.08361
- Attention Is All You Need | https://arxiv.org/abs/1706.03762
---
Before training, a model's parameters are random numbers, and its predictions are noise. After training, the same architecture writes fluent text. Nothing changes in between except the values of those parameters. This lesson is about how they get adjusted.

:::flow
Take a batch | Chunks of real text
Predict | Probabilities for each next token
Measure loss | How surprised was the model?
Update | Nudge every parameter slightly
:::

## Loss: how surprised was the model

For every position in the text, the model gives a probability to the token that actually came next. The **loss** turns that into one number. In **cross-entropy** loss, it is the negative logarithm of the probability given to the right answer. In plain words: how surprised was the model by what really happened.

:::example Surprise in numbers
The real next token was "Paris".
Model gave it 90%: loss = -ln(0.9) = 0.11
Model gave it 50%: loss = -ln(0.5) = 0.69
Model gave it 1%: loss = -ln(0.01) = 4.6
Confident and right costs little. Confident and wrong costs a lot.
:::

The training loss is the average over all positions in a batch. Lower is better, and it falls quickly at first and then slowly.

:::widget nexttoken

## Gradient descent

The loss depends on every parameter. The **gradient** is the set of numbers that says, for each parameter, how the loss would change if that parameter were nudged up a little. **Gradient descent** moves each parameter a small step in the direction that lowers the loss. Repeat that many times and the loss goes down.

Picture standing on a hilly landscape in fog, feeling the slope under your feet and stepping downhill. The landscape here has billions of dimensions, but the rule is the same.

Try it yourself. Choose a start, pick an optimizer and change the learning rate until the walk breaks.

:::widget gradient

## Backpropagation, honestly

How do we get the gradient for billions of parameters? **Backpropagation** applies the chain rule of calculus layer by layer. The forward pass computes the prediction and the loss. The backward pass starts at the loss and works back through each layer, passing along how much each intermediate value contributed to the error, and records the gradient for each parameter on the way. It costs about as much as a small multiple of the forward pass, which is why training is far more expensive than using a model. You do not need to do it by hand, because software frameworks derive it automatically.

## Learning rate, warmup and batch size

The **learning rate** sets the size of each step. Too small and training crawls. Too large and the loss bounces or blows up. Early in training the model is fragile, so the rate usually starts near zero and rises over the first steps, a period called **warmup**, then decays over the run. These schedules are tuned carefully, and large runs sometimes suffer sudden loss spikes that need special handling (see [When training breaks](/lessons/when-training-breaks/)).

A step is not computed from one example. It uses a **batch** of many sequences, and the gradient is averaged over them. Bigger batches give a less noisy gradient and use more chips efficiently. Frontier runs use huge batches: DeepSeek-V4-Pro's batch reaches 94.4 million tokens.

:::widget schedule

## Optimizers: Adam and after

Plain gradient descent uses the raw gradient. An **optimizer** improves on that. The most widely used is [Adam](https://arxiv.org/abs/1412.6980), which keeps a running average of each parameter's recent gradients and their size, so every parameter gets a step scaled to its own history. Many recent open models use a newer family called Muon for most weights, with Adam-style updates for embeddings and norms. DeepSeek-V4, Kimi and GLM-5 reports describe variants of it.

:::callout Key idea
Training does not store facts. It repeatedly shifts billions of numbers so that real text becomes slightly less surprising.
:::

## Epochs, tokens and checkpoints

Smaller machine learning tasks count progress in **epochs**: one pass over the whole dataset. For language models, the dataset is so large that it is usually seen about once, so people count **tokens seen** instead. GLM-5 trained on 28.5 trillion tokens across all stages. A common rule of thumb for compute is about six times the active parameters times the tokens, which for GLM-5 gives roughly 7e24 operations (our own arithmetic, shown in the film).

A **checkpoint** is a saved snapshot of the parameters, usually together with the optimizer's running averages and the position in the data. Runs last for weeks or months on machines that fail, so checkpoints are what let a job resume after a crash, and they are what you can later fine-tune, evaluate or release.

:::stats
94.4M | tokens in DeepSeek-V4-Pro's largest batch
28.5T | tokens seen by GLM-5 across all stages
:::

## Where to go next

What the model learns from depends on what it reads, so [Pretraining data](/lessons/pretraining-data/) is the natural next step. For how model size, data and compute trade off, see the scaling chapter of the frontier training film, and the overall recipe in its second chapter.
