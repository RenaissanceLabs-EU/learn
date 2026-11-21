#!/usr/bin/env python3
"""Second seed pass for data/capabilities.json: families, six stages, and sixteen more capabilities.

Run once after seed_capabilities.py. Edit the JSON by hand afterwards.
`stages` = how much each stage shapes the capability, 0 to 3, for
[design, pre-training, supervised fine-tuning, preference tuning, reinforcement learning, deployment]. An editorial sketch.
Every arXiv ID below was checked against the arXiv API on 2026-11-22.
"""
import json

A = "https://arxiv.org/abs/"
M = "https://marin.community/research-notes/"
HN, PN, IN, DN = "/notes/hallucination-and-i-dont-know/", "/notes/preference-tuning-and-alignment/", "/notes/identity-datasets/", "/notes/decision-models-jev-kev-sven/"
REPO = "https://github.com/BirgerMoell/oellm-hallucination"
OELLM = ["OpenEuroLLM", "https://labs.renaissancelabs.eu/labs/openeurollm/"]
MARIN = ["Marin", "https://labs.renaissancelabs.eu/labs/marin/"]

d = json.load(open("data/capabilities.json", encoding="utf-8"))
caps = {c["id"]: c for c in d["capabilities"]}

FAMILIES = [
 ["language", "Language", "Reading and writing text, in one language and across many.", "#5f8a7a"],
 ["knowledge", "Knowledge", "What the model knows, and how well it sticks to what it is given.", "#3f6f63"],
 ["thinking", "Thinking", "Working things out: logic, maths, code, and picking up a pattern from examples.", "#5f7396"],
 ["perception", "Input and memory", "What the model can take in: long documents, images, speech, and text turned into vectors.", "#8f7aa3"],
 ["conversation", "Conversation", "Being a usable assistant: doing what was asked, in the format asked for.", "#c79a3f"],
 ["honesty", "Honesty and safety", "Being truthful about what it knows, and safe and fair in what it does.", "#b0763f"],
 ["acting", "Acting", "Using tools and finishing tasks that take many steps.", "#b5654a"],
 ["efficiency", "Efficiency", "Properties of the model as a system: how fast it runs and what it needs to run.", "#7d776c"],
]

# existing twelve: family + six-stage weights
for cid, fam, st in [
 ("fluency", "language", [1, 3, 1, 0, 0, 0]), ("multilingual", "language", [2, 3, 2, 1, 0, 0]), ("knowledge", "knowledge", [0, 3, 1, 0, 0, 0]),
 ("reasoning", "thinking", [0, 2, 1, 1, 3, 0]), ("code", "thinking", [0, 3, 2, 0, 2, 0]), ("long-context", "perception", [3, 3, 1, 0, 0, 1]),
 ("instructions", "conversation", [0, 1, 3, 2, 1, 0]), ("identity", "conversation", [0, 0, 3, 1, 0, 1]), ("abstention", "honesty", [0, 0, 3, 3, 2, 0]),
 ("decisions", "honesty", [1, 1, 3, 0, 1, 0]), ("alignment", "honesty", [0, 0, 2, 3, 2, 1]), ("tools", "acting", [0, 0, 2, 1, 3, 1])]:
    caps[cid]["family"], caps[cid]["stages"] = fam, st
    caps[cid].pop("origin", None)

caps["multilingual"]["measure"] = [
 ["Belebele", "Reading comprehension in 122 language variants.", A + "2308.16884"],
 ["XTREME", "Cross-lingual tests across many languages and tasks.", A + "2003.11080"],
 ["ScandEval", "A benchmarking platform for the Scandinavian languages.", A + "2304.00906"],
 ["Answers in the question's language", "The share of replies in the language of the question. Part of the hallucination benchmark.", HN + "#the-benchmark"]]
caps["reasoning"]["measure"] = [
 ["BIG-Bench Hard", "Tasks picked because earlier models did badly on them.", A + "2210.09261"],
 ["ARC", "Abstract puzzles meant to test new reasoning, not recall.", A + "1911.01547"]]
caps["reasoning"]["wanted"] = ["Preference pairs in thinking mode for the hallucination recipe.", "Reasoning tests written in European languages, not translated."]
caps["long-context"]["measure"].insert(2, ["Lost in the Middle", "Shows that models use the start and end of a long input better than the middle.", A + "2307.03172"])
caps["tools"]["measure"] = [
 ["tau-bench", "An agent talks to a simulated user and must follow rules while using tools.", A + "2406.12045"],
 ["ToolLLM", "Tool use across more than 16,000 real-world APIs.", A + "2307.16789"]]
caps["knowledge"]["measure"].append(["FActScore", "Splits a long answer into single facts and checks each one.", A + "2305.14251"])

new = [
 {"id": "translation", "name": "Translation", "family": "language", "stages": [1, 3, 2, 0, 0, 0],
  "one": "The model carries meaning from one language into another.",
  "pre": "Parallel text in the pre-training data gives a base model some ability to translate.",
  "post": "Fine-tuning on translation pairs sharpens it. Much multilingual post-training data is itself machine-translated, so translation quality limits everything built on it.",
  "measure": [["FLORES-200", "Translation between 200 languages.", A + "2207.04672"]], "datasets": [],
  "findings": [
   ["An identity dataset was written by hand in English and machine-translated into 35 languages, with the method recorded on every row.", "OpenEuroLLM", IN + "#the-example-openeurollm-model-identity"],
   ["An alignment benchmark has one authored language. The other 35 are machine-translated and wait for native review.", "OpenEuroLLM", PN + "#what-the-benchmark-measures"]],
  "wanted": ["Quality checks for the machine-translated datasets used in post-training."],
  "labs": [OELLM], "lessons": ["tokens"], "notes": []},

 {"id": "writing", "name": "Writing", "family": "language", "stages": [0, 3, 2, 2, 0, 0],
  "one": "The model writes longer text that is clear, well organised and right for its reader.",
  "pre": "Style is absorbed from the text the model read, bad habits included.",
  "post": "Fine-tuning data sets the default voice. Preference tuning can shift it, because writing is easier to compare than to score.",
  "measure": [
   ["A rubric with a judge model", "Written criteria, scored by a judge model and checked against human ratings.", ""],
   ["FActScore", "Factual precision of long generated text, fact by fact.", A + "2305.14251"]],
  "datasets": [],
  "findings": [["All 421 invented answers in one benchmark run used bold text and 55% used bullet lists. Confident formatting made them read as authoritative.", "OpenEuroLLM", REPO + "/blob/main/results/prelude-9b-sft-v2-analysis.md"]],
  "wanted": ["A public writing benchmark for European languages with scores calibrated against human readers."],
  "labs": [OELLM], "lessons": ["supervised-fine-tuning"], "notes": []},

 {"id": "grounding", "name": "Sticking to the sources", "family": "knowledge", "stages": [0, 2, 3, 1, 1, 1],
  "one": "Given documents, the model answers from them and adds nothing they do not say.",
  "pre": "Reading comprehension comes with pre-training.",
  "post": "Staying inside the given text, and citing it, is taught in fine-tuning. At deployment, retrieval decides what the model gets to read.",
  "measure": [
   ["SQuAD", "Questions whose answer is a span of a given Wikipedia passage.", A + "1606.05250"],
   ["Ragas", "Scores a retrieval pipeline without needing reference answers.", A + "2309.15217"],
   ["FinanceBench", "Open-book questions about company filings.", A + "2311.11944"]],
  "datasets": [],
  "findings": [["With a search tool, a model that invented biographies closed-book answered 12 of 12 obscure people correctly.", "OpenEuroLLM", REPO]],
  "wanted": ["A grounding test with source documents in the smaller European languages."],
  "labs": [OELLM], "lessons": ["evaluation"], "notes": []},

 {"id": "specialist", "name": "Specialist knowledge", "family": "knowledge", "stages": [0, 3, 2, 0, 1, 0],
  "one": "The model answers questions from a profession, such as law, medicine or finance, at the level the field expects.",
  "pre": "Professional text is in the pre-training data. National law and local practice are thinly covered.",
  "post": "Fine-tuning on a field's own documents and cases adapts the model to it.",
  "measure": [
   ["LegalBench", "Legal reasoning tasks built with legal professionals.", A + "2308.11462"],
   ["MedQA", "Multiple-choice questions from medical licensing exams.", A + "2009.13081"],
   ["FinanceBench", "Financial questions answered from company filings.", A + "2311.11944"]],
  "datasets": [["Myndighetsbeslut", "16,632 Swedish authority cases with typed questions.", DN + "#swedish-authority-cases"]],
  "findings": [["Models trained on authority cases generated from rules learn the rules and score very high. That is not the same as handling real cases.", "Model cards", DN + "#swedish-authority-cases"]],
  "wanted": ["Specialist benchmarks built on national law and practice, not translated from another country's."],
  "labs": [], "lessons": [], "notes": ["decision-models-jev-kev-sven"]},

 {"id": "maths", "name": "Mathematics", "family": "thinking", "stages": [0, 2, 2, 0, 3, 0],
  "one": "The model solves problems with numbers and symbols and gets the right answer.",
  "pre": "Worked solutions in the pre-training text give a starting point.",
  "post": "Answers can be checked by a program, which makes maths a natural fit for reinforcement learning.",
  "measure": [
   ["GSM8K", "Grade-school maths word problems.", A + "2110.14168"],
   ["MATH", "Competition maths problems.", A + "2103.03874"]],
  "datasets": [],
  "findings": [
   ["After preference tuning, a 9B model's own card lists quantitative reasoning as a weak spot at 51.0%.", "OpenEuroLLM", PN + "#what-moved"],
   ["Group-based reinforcement learning (GRPO) was introduced for mathematical reasoning.", "DeepSeekMath", A + "2402.03300"]],
  "wanted": ["Maths problems written in European languages, not translated from English."],
  "labs": [OELLM], "lessons": ["preference-tuning-and-rl"], "notes": []},

 {"id": "icl", "name": "Learning from examples", "family": "thinking", "stages": [1, 3, 1, 0, 0, 0],
  "one": "Shown a few examples in the prompt, the model picks up the pattern and continues it.",
  "pre": "It emerges from pre-training at scale. Nobody trains it directly.",
  "post": "It is used at deployment through few-shot prompts, and it is how a base model is usually tested.",
  "measure": [
   ["Few-shot versions of standard tests", "Run a benchmark with zero, one and five worked examples and compare.", ""],
   ["Language Models are Few-Shot Learners", "The paper that showed the effect at scale.", A + "2005.14165"]],
  "datasets": [], "findings": [],
  "wanted": ["Few-shot results for base models, published next to their chat versions."],
  "labs": [], "lessons": ["what-is-a-language-model", "base-training"], "notes": []},

 {"id": "vision", "name": "Seeing images", "family": "perception", "stages": [3, 2, 2, 0, 0, 0],
  "one": "The model reads images, charts and scanned documents together with text.",
  "pre": "It needs a vision encoder in the design. Pairs of images and text teach the two to share one space.",
  "post": "Instruction tuning on image tasks turns that into answering questions about a picture.",
  "measure": [
   ["MMMU", "College-level questions that need both an image and subject knowledge.", A + "2311.16502"],
   ["DocVQA", "Questions about scanned document images.", A + "2007.00398"]],
  "datasets": [
   ["CLIP", "The method of learning image features from captions.", A + "2103.00020"],
   ["LLaVA", "Visual instruction tuning with machine-generated data.", A + "2304.08485"]],
  "findings": [],
  "wanted": ["Document tests on European forms, letters and tables."],
  "labs": [], "lessons": ["attention-and-the-transformer"], "notes": []},

 {"id": "speech", "name": "Hearing and speaking", "family": "perception", "stages": [3, 3, 2, 0, 0, 0],
  "one": "The model turns speech into text and text into speech.",
  "pre": "Speech models are pre-trained on very large amounts of transcribed audio.",
  "post": "Fine-tuning on one language or domain lowers the error rate there. General speech needs checking again afterwards.",
  "measure": [
   ["Word error rate", "The share of words the transcript gets wrong. Lower is better.", ""],
   ["FLEURS", "Parallel speech in 102 languages.", A + "2205.12446"]],
  "datasets": [
   ["Common Voice", "Transcribed speech in many languages, collected from volunteers.", A + "1912.06670"],
   ["Whisper", "Speech recognition trained on 680,000 hours of weakly labelled audio.", A + "2212.04356"]],
  "findings": [],
  "wanted": ["Test sets with regional accents and spontaneous speech."],
  "labs": [], "lessons": [], "notes": []},

 {"id": "embeddings", "name": "Search and embeddings", "family": "perception", "stages": [2, 3, 3, 0, 0, 0],
  "one": "The model turns text into vectors so that texts with similar meaning land close together.",
  "pre": "An embedding model starts from a pre-trained language model.",
  "post": "Contrastive fine-tuning on pairs of matching texts is what makes it good at search.",
  "measure": [
   ["MTEB", "Text embeddings tested across many tasks.", A + "2210.07316"],
   ["BEIR", "Retrieval on datasets the model was not trained on.", A + "2104.08663"]],
  "datasets": [], "findings": [],
  "wanted": ["Retrieval benchmarks for the smaller European languages."],
  "labs": [], "lessons": [], "notes": []},

 {"id": "structured", "name": "Structured output", "family": "conversation", "stages": [0, 1, 3, 0, 1, 3],
  "one": "The model returns valid JSON, or any fixed format, every time.",
  "pre": "A base model has seen plenty of JSON and code.",
  "post": "Fine-tuning teaches the format. Constrained decoding at serving time can enforce it.",
  "measure": [
   ["JSONSchemaBench", "Structured outputs tested against real JSON schemas.", A + "2501.10868"],
   ["Format validity rate", "The share of answers a parser accepts. Report it next to accuracy.", ""]],
  "datasets": [["Efficient Guided Generation", "Guiding generation with a finite-state machine so the output always fits a pattern.", A + "2307.09702"]],
  "findings": [
   ["A right answer in the wrong format earns half credit on one alignment benchmark, and does not pass.", "OpenEuroLLM", PN + "#what-the-benchmark-measures"],
   ["After preference tuning, one model card lists five malformed-format responses and six prompt echoes.", "OpenEuroLLM", PN + "#what-moved"],
   ["Well-formed tool-call JSON ended up inside the reasoning span and never reached the agent.", "Marin", M + "terminus-tool-call-parsing/"]],
  "wanted": ["Format validity reported next to accuracy on public leaderboards."],
  "labs": [MARIN, OELLM], "lessons": ["inference-and-sampling"], "notes": []},

 {"id": "misuse", "name": "Resisting misuse", "family": "honesty", "stages": [0, 0, 2, 3, 2, 2],
  "one": "The model declines harmful requests, holds that line under pressure, and does not refuse harmless ones.",
  "pre": "A base model has no notion of a request it should decline.",
  "post": "Fine-tuning and preference tuning teach refusals. Filters and monitoring at deployment add a second layer.",
  "measure": [
   ["HarmBench", "A standard setup for automated red teaming and robust refusal.", A + "2402.04249"],
   ["JailbreakBench", "An open benchmark of jailbreak attacks.", A + "2404.01318"],
   ["XSTest", "Safe prompts that an over-cautious model refuses.", A + "2308.01263"],
   ["AgentDojo", "Prompt injection attacks against agents that use tools.", A + "2406.13352"]],
  "datasets": [["CoCoNot", "Requests a model should not comply with, and contrast cases it should.", A + "2407.12043"]],
  "costs": ["Direct fine-tuning for refusals can cause over-refusal and a drop in general ability. Low-rank adapters gave a better balance in one study."],
  "findings": [
   ["Safety-critical gate failures fell from 71 to 39 after one epoch of preference tuning.", "OpenEuroLLM", PN + "#what-moved"],
   ["Models complied wrongly with up to 30% of requests in categories that had been studied little.", "Brahman and colleagues", A + "2407.12043"]],
  "wanted": ["Jailbreak and over-refusal tests in European languages."],
  "labs": [OELLM], "lessons": ["preference-tuning-and-rl"], "notes": ["preference-tuning-and-alignment"]},

 {"id": "fairness", "name": "Fairness", "family": "honesty", "stages": [0, 2, 2, 2, 0, 1],
  "one": "The model treats people and groups even-handedly and does not repeat stereotypes.",
  "pre": "Bias in the pre-training text is learned along with everything else.",
  "post": "Curated fine-tuning data and preference pairs can reduce it. It has to be measured per language and culture.",
  "measure": [
   ["BBQ", "Hand-built questions that test social bias in answers.", A + "2110.08193"],
   ["StereoSet", "Stereotyped associations in pre-trained language models.", A + "2004.09456"],
   ["HELM", "Reports fairness and bias next to accuracy for every scenario.", A + "2211.09110"]],
  "datasets": [], "findings": [],
  "wanted": ["Bias benchmarks written for European languages and societies."],
  "labs": [], "lessons": ["evaluation"], "notes": []},

 {"id": "privacy", "name": "Keeping data private", "family": "honesty", "stages": [0, 3, 1, 0, 0, 2],
  "one": "The model does not reveal personal data or repeat its training text word for word.",
  "pre": "Memorisation happens in pre-training, most of all for text that appears many times.",
  "post": "Deduplication and filtering before training are the main levers. Output filters at deployment are the backstop.",
  "measure": [
   ["Extraction attacks", "Prompt the model and check how much training text can be recovered.", A + "2012.07805"],
   ["Quantifying memorisation", "How memorisation grows with model size and with repeated data.", A + "2202.07646"]],
  "datasets": [],
  "findings": [["Getting better at finding duplicates does not tell you which copy to keep.", "Marin", M + "dedup-survivor-quality/"]],
  "wanted": ["Memorisation tests for models trained on public-sector text."],
  "labs": [MARIN], "lessons": ["pretraining-data"], "notes": []},

 {"id": "agents", "name": "Finishing long tasks", "family": "acting", "stages": [0, 1, 2, 1, 3, 2],
  "one": "The model plans, acts over many steps, recovers from its mistakes and finishes the job.",
  "pre": "A base model can continue a plan. It cannot carry one out.",
  "post": "Reinforcement learning in sandboxed environments rewards finishing. The harness around the model at deployment matters as much as the weights.",
  "measure": [
   ["Task-completion time horizon", "The length of task, in human time, that a model finishes half the time.", A + "2503.14499"],
   ["GAIA", "Real-world questions that need reasoning, browsing and tools.", A + "2311.12983"],
   ["OSWorld", "Open-ended tasks in real computer environments.", A + "2404.07972"],
   ["SWE-bench", "Real GitHub issues, resolved when the tests pass.", A + "2310.06770"]],
  "datasets": [],
  "findings": [
   ["Reinforcement learning on software tasks spent most of its extra time waiting on the environment.", "Marin", M + "software-rl-environment-wait/"],
   ["Training only on solved tasks showed no clear gain over a matched sample.", "Marin", M + "open-swe-outcome-filtering/"]],
  "wanted": ["Agent environments that run safely on shared academic clusters.", "A recipe card for an agentic reinforcement learning run on an open model."],
  "labs": [MARIN], "lessons": ["preference-tuning-and-rl", "post-training"], "notes": []},

 {"id": "speed", "name": "Inference speed", "family": "efficiency", "stages": [3, 0, 0, 0, 0, 3],
  "one": "The model answers quickly: a short wait for the first token, then many tokens per second.",
  "pre": "Speed is mostly decided in the design: the model's size, its attention variant and how many parameters are active per token.",
  "post": "Training does not change it. Quantisation, batching and the serving engine decide the rest.",
  "measure": [
   ["Time to first token and tokens per second", "Measured on named hardware, at a stated batch size and context length.", ""],
   ["HELM", "Reports efficiency next to accuracy.", A + "2211.09110"]],
  "datasets": [],
  "findings": [
   ["Speculative decoding samples faster without changing the outputs.", "Leviathan and colleagues", A + "2211.17192"],
   ["Paged memory for the attention cache raises serving throughput.", "vLLM", A + "2309.06180"],
   ["FlashAttention makes attention faster and lighter on memory without approximating it.", "Dao and colleagues", A + "2205.14135"]],
  "wanted": ["Speed numbers for open European models on common hardware, with the settings stated."],
  "labs": [], "lessons": ["inference-and-sampling", "mixture-of-experts", "gpus-and-parallelism"], "notes": []},

 {"id": "memory", "name": "Memory footprint", "family": "efficiency", "stages": [3, 0, 0, 0, 0, 3],
  "one": "The model fits on the hardware you have.",
  "pre": "Parameter count and number format set the size. Both are design choices.",
  "post": "Quantisation after training shrinks the model. Distillation moves the ability into a smaller one.",
  "measure": [
   ["Size in memory", "Parameters times bytes per parameter, plus the cache for the context. State the precision and the context length.", ""],
   ["Accuracy after quantisation", "The same benchmarks, before and after.", ""]],
  "datasets": [],
  "findings": [
   ["Weights can be quantised to 3 or 4 bits after training, one layer at a time.", "GPTQ", A + "2210.17323"],
   ["Looking at activations shows which weights matter most when quantising.", "AWQ", A + "2306.00978"],
   ["A small model can be trained to match a larger one's outputs.", "Hinton and colleagues", A + "1503.02531"]],
  "wanted": ["Before and after scores for 4-bit versions of open European models."],
  "labs": [], "lessons": ["parameters-precision-and-memory", "distillation-and-quantization"], "notes": []},
]
for c in new: caps[c["id"]] = c

order = ["fluency", "multilingual", "translation", "writing", "knowledge", "grounding", "specialist", "reasoning", "maths", "code", "icl",
         "long-context", "vision", "speech", "embeddings", "instructions", "structured", "identity", "abstention", "decisions", "alignment",
         "misuse", "fairness", "privacy", "tools", "agents", "speed", "memory"]
assert set(order) == set(caps), set(caps) ^ set(order)
out = {"stages": ["Design", "Pre-training", "Supervised fine-tuning", "Preference tuning", "Reinforcement learning", "Deployment"],
       "stages_short": ["Design", "Pre-training", "Fine-tuning", "Preferences", "RL", "Deployment"],
       "families": [{"id": a, "name": b, "about": c, "color": e} for a, b, c, e in FAMILIES],
       "capabilities": [caps[i] for i in order]}
json.dump(out, open("data/capabilities.json", "w"), indent=1, ensure_ascii=False)
print(len(order), "capabilities in", len(FAMILIES), "families")
