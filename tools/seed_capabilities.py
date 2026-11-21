#!/usr/bin/env python3
"""One-off seed for data/capabilities.json. Edit the JSON afterwards; this file only records how it was first written.

Every external link was checked on 2026-11-22: arXiv IDs against the arXiv API, Marin notes against marin.community/research-notes/.
`stages` = how much each stage shapes the capability, 0 to 3, for [pre-training, supervised fine-tuning, preference tuning,
reinforcement learning]. It is an editorial sketch, not a measurement.
"""
import json, os

A = "https://arxiv.org/abs/"
M = "https://marin.community/research-notes/"
HN = "/notes/hallucination-and-i-dont-know/"
PN = "/notes/preference-tuning-and-alignment/"
IN = "/notes/identity-datasets/"
DN = "/notes/decision-models-jev-kev-sven/"
OELLM = ["OpenEuroLLM", "https://labs.renaissancelabs.eu/labs/openeurollm/"]
MARIN = ["Marin", "https://labs.renaissancelabs.eu/labs/marin/"]

caps = [
 {"id": "fluency", "name": "Fluent text", "origin": "pre", "stages": [3, 1, 0, 0],
  "one": "The model writes correct, natural text and predicts what comes next.",
  "pre": "Pre-training optimises this directly: predict the next token, over a very large body of text.",
  "post": "Later stages change the style and format of the text. They do not teach the language.",
  "measure": [
   ["Held-out loss, or bits per byte", "How surprised the model is by text it has not seen. Lower is better.", ""],
   ["Paloma", "Language model fit across many separate domains.", A + "2312.10523"]],
  "datasets": [["FineWeb", "Filtered and deduplicated web text for pre-training.", A + "2406.17557"]],
  "findings": [
   ["A 128-step sawtooth in pre-training loss came from how the data was shuffled.", "Marin", M + "pretraining-loss-sawtooth/"],
   ["Removing duplicates can keep the worse copy of a document.", "Marin", M + "dedup-survivor-quality/"],
   ["A bits-per-byte bug flipped two comparisons on code.", "Marin", M + "paloma-bits-per-byte-weighting/"]],
  "wanted": ["Held-out loss per language for the smaller European languages, published next to the training mix."],
  "labs": [MARIN, OELLM],
  "lessons": ["what-is-a-language-model", "how-a-model-learns", "pretraining-data", "base-training"], "notes": []},

 {"id": "knowledge", "name": "World knowledge", "origin": "pre", "stages": [3, 1, 0, 0],
  "one": "The model recalls facts about the world without looking them up.",
  "pre": "Facts are absorbed from the pre-training text. What appears often is learned well, and the long tail is learned poorly.",
  "post": "Fine-tuning mostly teaches the model to use what it knows. Training it on facts it does not know has been shown to increase hallucination.",
  "measure": [
   ["MMLU", "Multiple-choice questions across 57 subjects.", A + "2009.03300"],
   ["SimpleQA", "Short factual questions with one checkable answer.", A + "2411.04368"],
   ["TruthfulQA", "Questions where a common misconception is the tempting answer.", A + "2109.07958"]],
  "datasets": [["Wikidata", "Structured facts, useful as a reference for grading answers.", "https://www.wikidata.org/"]],
  "findings": [
   ["On 80 questions about well-known people, a 9B model gave a fully correct answer to 16.", "OpenEuroLLM", HN + "#4-most-of-the-over-refusal-is-the-model-being-right"],
   ["Fine-tuning on facts the model does not know increases hallucination as those facts are learned.", "Gekhman and colleagues", A + "2405.05904"]],
  "wanted": ["A way to tell, per question, whether a model knows the answer or is guessing, without sampling it eight times."],
  "labs": [OELLM], "lessons": ["pretraining-data", "scaling-laws"], "notes": ["hallucination-and-i-dont-know"]},

 {"id": "multilingual", "name": "Many languages", "origin": "pre", "stages": [3, 2, 1, 0],
  "one": "The model reads and writes many languages, and answers in the language it was asked in.",
  "pre": "Coverage is set by the pre-training text and by the tokenizer. A language that tokenizes badly starts behind.",
  "post": "Post-training data is often English or machine-translated, so each stage needs its own check per language.",
  "measure": [
   ["FLORES-200", "Translation between 200 languages.", A + "2207.04672"],
   ["Belebele", "Reading comprehension in 122 language variants.", A + "2308.16884"],
   ["Answers in the question's language", "The share of replies in the language of the question. Part of the hallucination benchmark.", HN + "#the-benchmark"]],
  "datasets": [
   ["Dolci-Instruct-DPO, translated", "Preference pairs in 12 languages.", "https://huggingface.co/datasets/openeurollm/Dolci-Instruct-DPO-translated"],
   ["OpenEuroLLM Model Identity", "Identity conversations in 36 languages.", "https://huggingface.co/datasets/birgermoell/openeurollm-model-identity"]],
  "findings": [
   ["A very low score in one language (Georgian, 21.9%) was related to the tokenizer, not to the preference data.", "OpenEuroLLM", PN + "#what-moved"],
   ["In thinking mode, one model answered 11 to 14% of non-English questions in English.", "OpenEuroLLM", "https://github.com/BirgerMoell/oellm-hallucination"],
   ["Some Dutch questions were answered in German, by the base model and by the tuned one.", "OpenEuroLLM", "https://huggingface.co/birgermoell/prelude-9b-sft-v2-hallucination-r2"]],
  "wanted": ["Native-speaker review of machine-translated evaluation sets.", "Preference data written in more than 12 languages."],
  "labs": [OELLM], "lessons": ["tokens", "pretraining-data"], "notes": ["preference-tuning-and-alignment", "identity-datasets"]},

 {"id": "long-context", "name": "Long context", "origin": "pre", "stages": [3, 1, 0, 0],
  "one": "The model finds and uses information from far back in a long input.",
  "pre": "It depends on the architecture and on training with long sequences. A long context window does not mean the model uses it.",
  "post": "Fine-tuning on long conversations can help, but the gains are hard to show in generated answers.",
  "measure": [
   ["RULER", "Synthetic tasks that test how much of the context window a model really uses.", A + "2404.06654"],
   ["LongBench", "Long-document tasks in English and Chinese.", A + "2308.14508"],
   ["Paired retrieval tests", "Score the same answer with and without the earlier evidence in the prompt.", M + "mochi-262k-retrieval-loss/"]],
  "datasets": [],
  "findings": [
   ["A change that lowered loss on a 262K retrieval test kept most of its advantage when the evidence was removed.", "Marin", M + "mochi-262k-retrieval-loss/"],
   ["Filtering long replay data showed no clear gain on generated retrieval.", "Marin", M + "long-replay-filtering/"]],
  "wanted": ["A long-context test in European languages other than English."],
  "labs": [MARIN], "lessons": ["attention-and-the-transformer", "base-training"], "notes": []},

 {"id": "code", "name": "Code", "origin": "pre", "stages": [3, 2, 0, 2],
  "one": "The model writes working code and fixes real bugs.",
  "pre": "Code is in the pre-training text, so a base model can already continue a program.",
  "post": "Fine-tuning and reinforcement learning on tasks with tests turn that into fixing issues in real repositories.",
  "measure": [
   ["HumanEval", "Short programming problems, checked by unit tests.", A + "2107.03374"],
   ["SWE-bench", "Real GitHub issues, resolved when the repository's tests pass.", A + "2310.06770"]],
  "datasets": [["The Stack", "Permissively licensed source code.", A + "2211.15533"]],
  "findings": [
   ["Training only on solved Open-SWE tasks showed no clear gain over a matched sample.", "Marin", M + "open-swe-outcome-filtering/"],
   ["Reinforcement learning on software tasks spent most of its extra time waiting on the environment.", "Marin", M + "software-rl-environment-wait/"]],
  "wanted": ["A recipe card for a software-engineering fine-tune on an open 8 to 9B model."],
  "labs": [MARIN], "lessons": ["preference-tuning-and-rl"], "notes": []},

 {"id": "reasoning", "name": "Reasoning", "origin": "pre", "stages": [2, 1, 1, 3],
  "one": "The model works through a problem in steps and reaches the right answer.",
  "pre": "Some of it comes from pre-training text that contains worked solutions.",
  "post": "Reinforcement learning on problems with checkable answers is what produced today's thinking modes.",
  "measure": [
   ["GSM8K", "Grade-school maths word problems.", A + "2110.14168"],
   ["MATH", "Competition maths problems.", A + "2103.03874"]],
  "datasets": [],
  "findings": [
   ["Reinforcement learning on rewards can be used to train reasoning.", "DeepSeek-R1", A + "2501.12948"],
   ["Thinking mode lowered fabrication on made-up subjects for Qwen3-8B, from 73.6% to 46.8%.", "OpenEuroLLM", "https://github.com/BirgerMoell/oellm-hallucination"],
   ["A model tuned only in default mode lost accuracy in thinking mode, 53.8% to 40.0% on well-known people.", "OpenEuroLLM", HN + "#limits"]],
  "wanted": ["Preference pairs in thinking mode for the hallucination recipe."],
  "labs": [OELLM], "lessons": ["preference-tuning-and-rl", "post-training"], "notes": []},

 {"id": "instructions", "name": "Following instructions", "origin": "post", "stages": [1, 3, 2, 1],
  "one": "The model does what was asked, in the format asked for, across a conversation.",
  "pre": "A base model continues text. It has no notion of a request or a turn.",
  "post": "Supervised fine-tuning on conversations teaches the chat format and the habit of answering the question.",
  "measure": [
   ["IFEval", "Instructions that a program can check, such as length or required words.", A + "2311.07911"],
   ["MT-Bench", "Multi-turn questions graded by a judge model.", A + "2306.05685"]],
  "datasets": [
   ["UltraFeedback", "Model answers with ratings, often used as preference pairs.", A + "2310.01377"],
   ["HelpSteer3", "Human preferences between answers.", "https://huggingface.co/datasets/nvidia/HelpSteer3"],
   ["FLAN", "Many tasks rewritten as instructions.", A + "2109.01652"]],
  "findings": [
   ["Removing flawed documents from a fine-tuning mix was tested as a way to remove the behaviours they teach.", "Marin", M + "sft-mix-filtering/"]],
  "wanted": ["An instruction-following test with programmatic checks in more European languages."],
  "labs": [MARIN, OELLM], "lessons": ["supervised-fine-tuning", "post-training"], "notes": []},

 {"id": "abstention", "name": "Knowing what it doesn't know", "origin": "post", "stages": [0, 3, 3, 2],
  "one": "The model says \"I don't know\" when it does not know, and answers when it does.",
  "example": {"q": "Who is Declan Monmonley? (a made-up name)",
              "bad": "\"Declan Monmonley is a British actor, writer, and director...\"",
              "good": "\"I'm not sure who Declan Monmonley is. Could you provide some context?\""},
  "pre": "Nothing in pre-training separates \"I know this\" from \"this sounds right\".",
  "post": "Supervised fine-tuning usually makes it worse, because every training question gets a confident answer. It has to be trained on purpose.",
  "measure": [
   ["Natural-question hallucination benchmark", "500 questions in 10 languages, with made-up subjects and real people, and no offered way out.", "https://github.com/BirgerMoell/oellm-hallucination"],
   ["Release gates used with it", "Fabrication under 10%. Refusals on well-known people under 5%. At least 95% of answers in the right language.", "https://github.com/BirgerMoell/oellm-hallucination"],
   ["SimpleQA", "Short factual questions, graded as correct, incorrect or not attempted.", A + "2411.04368"]],
  "datasets": [
   ["Hallucination round 2 data", "The exact rows of the recipe below: abstentions, answers and preference pairs.", "https://huggingface.co/datasets/birgermoell/prelude-9b-sft-v2-hallucination-r2-data"],
   ["CoCoNot", "When a model should not comply, including false-premise questions.", A + "2407.12043"],
   ["Idk", "Questions split by whether a given model knows the answer.", A + "2401.13275"],
   ["R-Tuning", "Refusal-aware tuning data built from the model's own knowledge.", A + "2311.09677"]],
  "costs": ["The tuned model declines 31 of 80 questions about well-known people. It had answered 20 of those wrongly before, and 3 fully correctly.",
            "It tells users it is not sure who some famous people are, such as John Paul II.",
            "Thinking mode, which was not trained, lost accuracy on known facts."],
  "findings": [
   ["An offered \"UNKNOWN\" option does not transfer to natural questions.", "OpenEuroLLM", HN + "#1-an-unknown-option-does-not-transfer"],
   ["DPO alone raised reward accuracy to 79% and barely changed what the model wrote.", "OpenEuroLLM", HN + "#2-the-loss-went-down-and-the-model-did-not-change"],
   ["Twelve minutes of supervised fine-tuning took fabrication from 97.7% to 3.6%.", "OpenEuroLLM", HN + "#3-twelve-minutes-of-supervised-training-did-most-of-it"],
   ["Most of the measured over-refusal replaced answers that were wrong.", "OpenEuroLLM", HN + "#4-most-of-the-over-refusal-is-the-model-being-right"],
   ["Benchmarks that give no penalty for a wrong answer reward guessing.", "Kalai and colleagues", A + "2509.04664"]],
  "wanted": ["Answer rows for open questions about well-known people.", "A fairer over-refusal gate, counting only questions the untrained model got right.",
             "General evaluations (maths, code, tools) after this training.", "The same recipe on a model outside this family."],
  "labs": [OELLM], "lessons": ["supervised-fine-tuning", "preference-tuning-and-rl", "evaluation"], "notes": ["hallucination-and-i-dont-know"]},

 {"id": "identity", "name": "Knowing who it is", "origin": "post", "stages": [0, 3, 1, 0],
  "one": "The model states its own name, maker, knowledge cutoff and limits correctly.",
  "pre": "A base model has read about other models, so asked who it is, it often names one of them.",
  "post": "A small identity dataset mixed into supervised fine-tuning teaches a fixed set of true statements about the model.",
  "measure": [
   ["Held-out identity set with gates", "Correct at least 90%, wrong at most 3%, worst category at least 75%, right language at least 95%, overtrigger at most 4%.", IN + "#how-to-check-it-worked"]],
  "datasets": [["OpenEuroLLM Model Identity", "5,508 training and 923 validation conversations in 36 languages.", "https://huggingface.co/datasets/birgermoell/openeurollm-model-identity"]],
  "costs": ["A model can overtrigger and talk about itself when nobody asked. The gates include a limit for that."],
  "findings": [
   ["Before identity training, the model was correct about itself 52.8% of the time and wrong 38.6%.", "OpenEuroLLM", IN + "#how-to-check-it-worked"],
   ["About 0.5% of the fine-tuning mix is enough, mixed in once without upsampling.", "OpenEuroLLM", IN + "#how-to-use-it-without-damaging-the-model"],
   ["Identity is a property of the whole data mix. Rows elsewhere that claim another name can outvote the identity set.", "OpenEuroLLM", IN + "#when-it-fails"]],
  "wanted": ["Results on the held-out set after each later training stage."],
  "labs": [OELLM], "lessons": ["supervised-fine-tuning"], "notes": ["identity-datasets"]},

 {"id": "alignment", "name": "Behaving as intended", "origin": "post", "stages": [0, 2, 3, 2],
  "one": "The model is helpful and honest, declines what it should, and respects limits on what it may do.",
  "pre": "A base model imitates whatever text it saw, good and bad.",
  "post": "Preference tuning on pairs of better and worse answers shifts which answer the model prefers.",
  "measure": [
   ["EUROPA Alignment", "A public pilot: 576 items, 16 scenarios in 36 languages, graded by a judge model.", PN + "#what-the-benchmark-measures"],
   ["CoCoNot", "1,000 prompts where the right move is not to comply.", A + "2407.12043"]],
  "datasets": [
   ["Dolci-Instruct-DPO, translated", "1.35 million preference pairs in 12 languages.", "https://huggingface.co/datasets/openeurollm/Dolci-Instruct-DPO-translated"],
   ["UltraFeedback", "Rated model answers.", A + "2310.01377"],
   ["HelpSteer3", "Human preferences between answers.", "https://huggingface.co/datasets/nvidia/HelpSteer3"]],
  "costs": ["The same model card lists weak spots after tuning, including quantitative reasoning at 51.0%."],
  "findings": [
   ["One epoch of full-weight DPO raised the alignment score from 77.3% to 89.3%.", "OpenEuroLLM", PN + "#what-moved"],
   ["The score peaked at step 9,000 of 11,263 (89.5%) and ended slightly lower.", "OpenEuroLLM", PN + "#what-moved"],
   ["With 16 items per language, one item is worth 6.25 points of a language's score.", "OpenEuroLLM", PN + "#what-moved"]],
  "wanted": ["Independently reviewed full-suite runs of the benchmark.", "Scenarios written by native speakers in the other 35 languages."],
  "labs": [OELLM], "lessons": ["preference-tuning-and-rl", "evaluation"], "notes": ["preference-tuning-and-alignment"]},

 {"id": "tools", "name": "Using tools", "origin": "post", "stages": [0, 2, 1, 3],
  "one": "The model calls tools correctly, reads the results and finishes a multi-step task.",
  "pre": "A base model has seen code and logs, and no tool-call format.",
  "post": "Fine-tuning teaches the call format. Reinforcement learning in sandboxed environments teaches finishing the task.",
  "measure": [
   ["tau-bench", "An agent talks to a simulated user and must follow rules while using tools.", A + "2406.12045"],
   ["SWE-bench", "Fixing real issues requires many tool calls in a row.", A + "2310.06770"]],
  "datasets": [],
  "findings": [
   ["A prompt that ended at a different token boundary than in training made tool calls vanish into the reasoning span.", "Marin", M + "terminus-tool-call-parsing/"],
   ["Compact skill routing improved a small operational evaluation.", "Marin", M + "compact-agent-skill-routing/"],
   ["With a search tool, a model that invented biographies closed-book answered 12 of 12 obscure people correctly.", "OpenEuroLLM", "https://github.com/BirgerMoell/oellm-hallucination"]],
  "wanted": ["Open tool-use environments in European languages.", "A recipe card for a tool-use fine-tune."],
  "labs": [MARIN, OELLM], "lessons": ["preference-tuning-and-rl", "post-training"], "notes": []},

 {"id": "decisions", "name": "Calibrated decisions", "origin": "post", "stages": [1, 3, 0, 1],
  "one": "The model answers a typed question with a probability that matches how often it is right.",
  "pre": "The base model supplies the reading ability. The decision itself is not there.",
  "post": "A small adapter and a decision head are trained on labelled cases, then calibrated.",
  "measure": [
   ["Accuracy and Brier score", "Brier scores the whole probability distribution. Lower is better.", DN + "#sven-teaching-kev-swedish"],
   ["Expected calibration error", "The average gap between stated confidence and how often the model is right.", A + "1706.04599"]],
  "datasets": [["Myndighetsbeslut", "16,632 Swedish authority cases with typed questions and a split by date.", DN + "#swedish-authority-cases"]],
  "findings": [
   ["Sven-0.6B reaches 0.745 accuracy on held-out Swedish questions, with a calibration error of 0.079.", "Sven model card", DN + "#sven-teaching-kev-swedish"],
   ["A score equal to the majority class is not a result. One authority's decisions were not learned at all.", "Model cards", DN + "#swedish-authority-cases"]],
  "wanted": ["Decision data from real case files, not generated from rules."],
  "labs": [["TypeSafe (Jev)", ""], ["Jared Palmer (Kev)", ""]], "lessons": ["evaluation"], "notes": ["decision-models-jev-kev-sven"]},
]

os.makedirs("data", exist_ok=True)
json.dump({"stages": ["Pre-training", "Supervised fine-tuning", "Preference tuning", "Reinforcement learning"], "capabilities": caps},
          open("data/capabilities.json", "w"), indent=1, ensure_ascii=False)
print(len(caps), "capabilities")
