#!/usr/bin/env python3
"""Third seed pass: five more capabilities. arXiv IDs checked against the arXiv API on 2026-11-22. Run once; edit the JSON afterwards."""
import json

A = "https://arxiv.org/abs/"
PN, HN = "/notes/preference-tuning-and-alignment/", "/notes/hallucination-and-i-dont-know/"
OELLM = ["OpenEuroLLM", "https://labs.renaissancelabs.eu/labs/openeurollm/"]
d = json.load(open("data/capabilities.json", encoding="utf-8"))
caps = d["capabilities"]
have = {c["id"] for c in caps}

new = {
 "writing": {"id": "summarisation", "name": "Summarising", "family": "language", "stages": [0, 2, 3, 1, 0, 0],
  "one": "The model shortens a text and keeps what matters, without adding anything.",
  "pre": "A base model has read many articles with their headlines and abstracts.",
  "post": "Fine-tuning teaches the task and the length. The hard part is staying faithful to the source.",
  "measure": [
   ["SummEval", "A re-evaluation of 14 automatic summary metrics against human judgement.", A + "2007.12626"],
   ["BERTScore", "Compares a summary with a reference by meaning, not by exact words.", A + "1904.09675"],
   ["FActScore", "Checks each fact in a generated text against a source.", A + "2305.14251"]],
  "datasets": [["XSum", "News articles with one-sentence summaries.", A + "1808.08745"]],
  "findings": [],
  "wanted": ["Summarisation test sets in the smaller European languages, with human ratings."],
  "labs": [], "lessons": ["supervised-fine-tuning"], "notes": []},

 "vision": {"id": "video", "name": "Watching video", "family": "perception", "stages": [3, 2, 2, 0, 0, 1],
  "one": "The model follows what happens over time in a video and answers questions about it.",
  "pre": "It needs a design that can take many frames. Each frame costs tokens, so long video competes with the context window.",
  "post": "Instruction tuning on video questions teaches the task. How many frames are sampled at serving time limits what the model can see.",
  "measure": [
   ["Video-MME", "Video analysis across short, medium and long videos.", A + "2405.21075"],
   ["MVBench", "Tasks that need understanding of time, not of one frame.", A + "2311.17005"],
   ["EgoSchema", "Questions about very long first-person video.", A + "2308.09126"]],
  "datasets": [["ActivityNet-QA", "Question answering on web videos.", A + "1906.02467"]],
  "findings": [],
  "wanted": ["Video tests with speech in European languages."],
  "labs": [], "lessons": [], "notes": []},

 "structured": {"id": "multiturn", "name": "Remembering the conversation", "family": "conversation", "stages": [1, 1, 3, 1, 0, 2],
  "one": "The model keeps track of what was said many turns ago and stays consistent with it.",
  "pre": "The context window sets how much of a conversation fits at all.",
  "post": "Fine-tuning on long conversations teaches the model to use earlier turns. For memory across sessions, the system around the model stores and retrieves it.",
  "measure": [
   ["LongMemEval", "Long-term memory of chat assistants over sustained interactions.", A + "2410.10813"],
   ["LoCoMo", "Very long conversations that span many sessions.", A + "2402.17753"],
   ["MT-Bench", "Multi-turn questions graded by a judge model.", A + "2306.05685"]],
  "datasets": [],
  "findings": [["Models do worse when a task is revealed over several turns than when it is given in one message.", "LLMs Get Lost In Multi-Turn Conversation", A + "2505.06120"]],
  "wanted": ["Multi-turn test sets in European languages.", "A recipe for training on long conversations without losing short-prompt quality."],
  "labs": [], "lessons": ["supervised-fine-tuning"], "notes": []},

 "misuse": {"id": "robustness", "name": "Robustness", "family": "honesty", "stages": [0, 2, 2, 1, 1, 1],
  "one": "The model gives the same answer when the question is reworded, reformatted or has a typo.",
  "pre": "Varied pre-training text gives some tolerance to how a question is phrased.",
  "post": "Post-training data in one fixed format can make the model brittle outside that format. Variety in the prompts is the remedy.",
  "measure": [
   ["PromptRobust", "Resilience to adversarial changes in the prompt.", A + "2306.04528"],
   ["Sensitivity to prompt format", "Measures how much scores move when only the formatting changes.", A + "2310.11324"],
   ["CheckList", "Behavioural tests, such as rewording an input and expecting the same output.", A + "2005.04118"],
   ["HELM", "Reports robustness next to accuracy.", A + "2211.09110"]],
  "datasets": [],
  "findings": [
   ["Abstention trained on prompts with an offered \"UNKNOWN\" option did not carry over to the same questions asked in plain words.", "OpenEuroLLM", HN + "#1-an-unknown-option-does-not-transfer"],
   ["A prompt that ended at a different token boundary than in training made tool calls disappear.", "Marin", "https://marin.community/research-notes/terminus-tool-call-parsing/"]],
  "wanted": ["Benchmark scores reported over several rewordings of each question, not one."],
  "labs": [OELLM, ["Marin", "https://labs.renaissancelabs.eu/labs/marin/"]], "lessons": ["evaluation"], "notes": ["hallucination-and-i-dont-know"]},

 "memory": {"id": "training-cost", "name": "Cost to train", "family": "efficiency", "stages": [3, 3, 1, 1, 2, 0],
  "one": "The model can be trained, and trained again, with the compute a lab has.",
  "pre": "Model size and the number of training tokens set the bill, and pre-training is nearly all of it.",
  "post": "Post-training stages are small by comparison. Low-rank adapters cut the cost of fine-tuning further. Reinforcement learning pays for rollouts as well as updates.",
  "measure": [
   ["GPU-hours and wall-clock time", "On named hardware, with the number of nodes. Report it with every run.", ""],
   ["Compute-optimal training", "How to split a fixed compute budget between model size and training tokens.", A + "2203.15556"],
   ["Scaling laws", "How loss falls with model size, data and compute.", A + "2001.08361"]],
  "datasets": [["LoRA", "Fine-tuning a small set of added weights and freezing the rest.", A + "2106.09685"]],
  "findings": [
   ["One epoch of full-weight DPO on 1.4 million pairs took 43 hours 21 minutes on 32 GPUs, about 1,387 GCD-hours.", "OpenEuroLLM", "/recipes/oellm-9b-threeway-dpo/#equipment"],
   ["A supervised warm start on 6,123 rows took 12 minutes on 8 GPUs.", "OpenEuroLLM", "/recipes/prelude-9b-hallucination-r2/#equipment"],
   ["The energy and money cost of training large NLP models was already raised as a policy question in 2019.", "Strubell and colleagues", A + "1906.02243"]],
  "wanted": ["GPU-hours published with every open checkpoint, per stage."],
  "labs": [OELLM], "lessons": ["scaling-laws", "gpus-and-parallelism"], "notes": []},
}
out = []
for c in caps:
    out.append(c)
    n = new.get(c["id"])
    if n and n["id"] not in have: out.append(n)
d["capabilities"] = out
json.dump(d, open("data/capabilities.json", "w"), indent=1, ensure_ascii=False)
print(len(out), "capabilities")
