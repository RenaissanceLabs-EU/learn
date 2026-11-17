---
title: "Tokens: how text becomes numbers"
slug: tokens
part: The basics
order: 2
level: Beginner
minutes: 7
summary: Models read and write tokens, not words. Tokens decide what you pay for, how much fits in context, and why models stumble on spelling and arithmetic.
films: frontier-training:data, open-models:data
related: what-is-a-language-model, attention-and-the-transformer
widget: tokenizer
sources:
- Neural Machine Translation of Rare Words with Subword Units (BPE) | https://arxiv.org/abs/1508.07909
- Attention Is All You Need | https://arxiv.org/abs/1706.03762
---
A neural network only does arithmetic on numbers, so text has to be turned into numbers before a model can touch it. The first step is to cut the text into pieces. Each piece gets an integer ID, and that ID later becomes a list of numbers the model can work with. The pieces are called **tokens**, and the program that cuts text into them is the **tokenizer**.

## Why not words, and why not letters

Splitting on whole words sounds natural, but it breaks quickly. A word list large enough to cover every name, typo, code identifier and language would be enormous, and any word not on the list would be unreadable. Splitting into single characters or bytes fixes that, because every text can be spelled out. But the sequences get very long, and the model has to spend effort re-learning that "t", "h", "e" belong together.

**Subword tokenization** sits in between. Common words stay whole. Rare words are built from reusable pieces. "Unbelievable" might become "un", "believ", "able". A word the tokenizer has never met can still be spelled out from smaller pieces, so nothing is ever unreadable.

## How the pieces are chosen

The most common method is **byte-pair encoding**, or BPE ([Sennrich et al.](https://arxiv.org/abs/1508.07909) adapted it for neural models). The idea fits in a few lines. Start with single characters, count which neighbouring pair appears most often in a large text sample, and merge that pair into a new piece. Repeat until the vocabulary reaches a chosen size.

:::flow
Characters | Start with one piece per character
Count pairs | Find the most frequent neighbours
Merge | Make that pair a single new piece
Repeat | Stop at the target vocabulary size
:::

:::example A toy run
Text sample: "low low low lower lowest"
Round 1: "l" + "o" is the most common pair, so "lo" becomes a piece.
Round 2: "lo" + "w" is next, so "low" becomes a piece.
Now "low" is one token, and "lower" is "low" + "er" once "er" is merged.
:::

Real tokenizers work on bytes rather than characters, so any string, including emoji and unusual scripts, can be represented. Below is a small tokenizer you can type into. It is a toy that follows the same spirit, not the tokenizer of any real model, so the exact pieces will differ from what a production model produces.

:::widget tokenizer

## Vocabulary size is a trade-off

The number of distinct tokens is the **vocabulary size**. Recent open models use vocabularies of well over 100,000 entries. DeepSeek-V4 uses a 128K vocabulary and Kimi K3 uses 160K.

:::compare
## Smaller vocabulary
- Text becomes more tokens
- Each token is cheaper to represent
- Fewer rare tokens that are seen too seldom to learn well
## Larger vocabulary
- Text becomes fewer tokens
- Larger embedding table and output layer
- Shorter sequences mean less work per document
:::

Neither end is free. Larger vocabularies shorten sequences but add parameters, and some tokens end up so rare that the model barely learns them.

## Why tokens cost money and context

Everything a model does is counted in tokens: how long your prompt may be, how long the answer may be, how much a request costs, how fast it runs. A common rule of thumb for English is that a token is roughly three quarters of a word, but that is only an average and varies with the text.

Because the cost of attention and memory grows with the number of tokens (see [Attention and the transformer](/lessons/attention-and-the-transformer/)), a tokenizer that produces fewer tokens for the same text is directly cheaper to run.

:::callout Key idea
The same sentence can be many tokens or few, depending on the tokenizer and the language. Tokens, not characters or words, are the unit of cost and of context.
:::

## Languages are not treated equally

A tokenizer learns its merges from the text it was trained on. If that text was mostly English, English words get long, efficient pieces. Languages that were rare in the sample are split into more and smaller pieces, so the same meaning costs more tokens. That means higher cost, less room in the context window, and often slightly worse results for those languages. A larger multilingual share in the tokenizer's training text, and a bigger vocabulary, both help narrow the gap. DeepSeek-V4's report lists a larger multilingual corpus among its data choices.

## Why spelling and arithmetic are awkward

The model never sees letters. If "strawberry" arrives as two or three tokens, counting its letters means recalling spelling from training rather than looking at it. Numbers have the same problem. A long number may be cut into chunks that do not line up with digits or place value, so column arithmetic is harder than it looks. These are side effects of the tokenizer, not signs that the model cannot learn the task.

## Where to go next

Next, [Attention and the transformer](/lessons/attention-and-the-transformer/) shows what the model does with a sequence of tokens. To see how many tokens real training runs use, read [Pretraining data](/lessons/pretraining-data/) and watch the data chapters of the frontier training and open models films.
