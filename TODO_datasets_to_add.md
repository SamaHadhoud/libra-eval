# TODO — Improve Safety-Evaluation Coverage

Goal: **balanced coverage across the safety risk taxonomy** for **text chat** evaluation (single/multi-turn prompt → response). **Out of scope: multimodal (vision/audio) and agentic/tool-use datasets.**

Prioritization = **coverage gap × reputation × recency**.
- **Effort:** 🟢 minutes (already in repo) · 🟡 small code/format work · 🔴 download + new task class.
- **Reputation:** ⭐⭐⭐ top venue + standard/highly-cited · ⭐⭐ solid venue / well-used · ⭐ recent/emerging, few citations yet.

Inputs: [datasets_in_repo_unused.csv](datasets_in_repo_unused.csv), [datasets_not_available_in_repo.csv](datasets_not_available_in_repo.csv), and June-2026 research.

---

## Coverage scorecard (~70 active datasets — 20 **(new)** added recently; WMDP & Chinese-only sets since excluded)

| Risk area | Status | Priority action |
|---|---|---|
| Direct harmful / illicit | ✅ Strong (AdvBench, HarmBench, BeaverTails, SORRY-Bench, DoNotAnswer…) | maintain |
| Jailbreak / adversarial | ✅ Strong (DAN, JailbreakBench, JailBench, WildJailbreak, librai_adv…) | maintain |
| Prompt injection / extraction | ✅ Strong (PromptInjection, Tensor-Trust, Gandalf, HackAPrompt) | maintain |
| Toxicity / hate | ✅ **(new)** Strong (ToxiGen, ToxicChat, HateXplain, RealToxicityPrompts) | maintain |
| Social bias / fairness | ✅ **(new)** Strong (CrowS-Pairs, StereoSet, BOLD, DICES350, BBQ) | optional: DiscrimEval |
| Privacy / PII | 🟨 OK (ConfAIde, PersonalInfoLeak, DecodingTrust-Privacy) | maintain |
| Misinfo / sycophancy | 🟨 OK (TruthfulQA-mc1, SP-Misconceptions, Sycophancy ×3) | maintain |
| **CBRN / dangerous knowledge** | ✅ active (ClearHarm; WMDP excluded as a knowledge-probe, not a refusal test) | maintain |
| **Over-refusal / oversensitivity** | ✅ **(new)** Good (XSTest, OR-Bench, FalseReject, CoCoNot-contrast) | maintain |
| **Multilingual safety** | ✅ **(new)** Good (AyaRedTeaming 8-lang, XSafety 10-lang) | maintain |
| **Value alignment / ethics** | 🟥 **narrow** (MoralChoice, DecodingTrust-ME) | **P1** (ETHICS, GlobalOpinionQA) |
| Comprehensive / taxonomic | ✅ **(new)** Good (SALAD-Bench 3-level taxonomy, CatQA, ForbiddenQuestions) | maintain |
| Multi-turn dialogue safety | ✅ **(new)** Good (AnthropicRedTeam, BAD, DialogueSafety, CoSafe, DiaSafety) | maintain |
| Domain-specific (medical/finance/law/edu) | ✅ **(new)** active (MedSafetyBench, StealthGraph) | maintain |

---

## ⭐ Newest text-chat releases (2025–2026) — prioritize for recency

Slot the strong ones into the gaps below.
- **IndicSafe** 🔴 ⭐ — *arXiv 2026* — first safety benchmark for **12 Indic languages**, 6,000 culturally-grounded prompts (caste/religion/gender/health/politics); 12.8% cross-language agreement. → multilingual gap. `arXiv:2603.17915`
- **RedBench** 🔴 ⭐ — *arXiv 2026* — "universal" comprehensive red-teaming dataset. → taxonomic breadth. `arXiv:2601.03699`
- **TeleAI-Safety** ⏭️ *deferred: mostly a framework (19 attacks/29 defenses/19 evals), only 342 prompts; overlaps existing jailbreak coverage* — 🔴 ⭐ — *arXiv 2025/12* — `arXiv:2512.05485`
- **FalseReject** ✅ **(new)** — *COLM 2025* — large graph-generated over-refusal set w/ structured reasoning; strong for reasoning models. Task `false_reject`. `arXiv:2505.08054`
- **CASE-Bench** ✅ **(new)** — *ICML 2025* — context-aware safety: same request, refusal should differ by context. Task `case_bench` (900, behaviour_match). `arXiv:2501.14940`
- **SEA-SafeguardBench** 🔴 ⭐ — *arXiv 2025* — culturally-grounded SE-Asian safety. `arXiv:2512.05501`
- **Taiwan Safety Benchmark** 🔴 ⭐ — *arXiv 2026* — Taiwanese-Mandarin safety. `arXiv:2603.07286`
- **StealthGraph** ✅ **(new)** — *arXiv 2026* — KG-guided implicit domain-specific harmful prompts. Task `stealth_graph` (3,163; med/finance/law/education). `github.com/ZJUIDG-AIVA/StealthGraph`, `arXiv:2601.04740`

---

## P0 — Critical gaps (top-venue / recent picks first)

### CBRN / dangerous knowledge — ✅ **(new)** now active
- [x] **WMDP** ✅ **(new)** 🟢 ⭐⭐⭐ — *ICML 2024* — hazardous bio/chem/cyber MCQ (3,668). Frontier-policy standard. Task `wmdp` (programmatic MCQ, scored 1−accuracy → `hazardous_knowledge_avoidance`).
- [x] **ClearHarm** ✅ **(new)** 🟢 ⭐ — *arXiv 2024 (FAR AI)* — CBRN/bio-chem harmful instructions (179). Task `clearharm`.

### Over-refusal — ✅ **(new)** expanded beyond XSTest
- [x] **OR-Bench** ✅ **(new)** 🔴 ⭐⭐⭐ — *ICML 2025* — over-refusal benchmark. Tasks `or_bench_hard_1k` (hard-1k, over-refusal) + `or_bench_toxic` (toxic control, should-refuse). `github.com/justincui03/or-bench`
- [x] **FalseReject** ✅ **(new)** 🔴 ⭐⭐ — *COLM 2025* — reasoning-aware over-refusal. Task `false_reject` (test split, 1,187). `arXiv:2505.08054`
- [x] **CoCoNot** ✅ **(new)** 🔴 ⭐⭐ — *COLM 2024 (AI2)* — (non)compliance cases. Tasks `coconot_original` (should-refuse, custom category-aware judge → `appropriate_noncompliance`) + `coconot_contrast` (should-comply). `github.com/allenai/noncompliance`

### Multilingual safety — currently English + a little Chinese
- [ ] **PolygloToxicityPrompts** 🔴 ⭐⭐ — *COLM 2024* — 425K toxic prompts, 17 languages. `hf/ToxicityPrompts/PolygloToxicityPrompts`
- [x] **XSafety** ✅ **(new)** 🔴 ⭐⭐ — *ACL 2024* — 25,599 prompts, 10 languages, ~14 categories. Task `xsafety` (language + category subgroups). `github.com/Jarviswang94/Multilingual_safety_benchmark`
- [x] **AyaRedTeaming** ✅ **(new)** 🔴 ⭐⭐ — *Cohere, 2024* — 7,419 human-written red-team prompts, 8 languages incl. Arabic. Task `aya_redteaming`. `hf/CohereForAI/aya_redteaming`
- [ ] **IndicSafe** 🔴 ⭐ — *arXiv 2026* — 12 Indic languages, culturally grounded (newest). `arXiv:2603.17915`

---

## P1 — Important breadth & depth

### Comprehensive / taxonomic harmful (adds category labels for per-risk analysis)
- [ ] **WildGuardMix** ⛔ *blocked: gated HF dataset, needs `HF_TOKEN` + access request* — 🔴 ⭐⭐⭐ — *NeurIPS 2024 D&B* — 86,759 prompt+response (harmful/benign/refusal); de-facto moderation benchmark. `hf/allenai/wildguardmix`
- [x] **SALAD-Bench** ✅ **(new)** 🔴 ⭐⭐⭐ — *ACL 2024 Findings* — 21,318 harmful prompts, 3-level taxonomy. Task `salad_bench`. `hf/OpenSafetyLab/Salad-Data`
- [ ] **ALERT** 🔴 ⭐⭐ — *2024* — 44,800 red-team prompts, fine-grained taxonomy. `github.com/Babelscape/ALERT`
- [~] **RedBench** ⚠️ *not added wholesale — it re-bundles ~37 benchmarks, most already in repo (would double-count). Cherry-picked the non-overlapping subsets instead: `catqa`, `forbidden_questions`, `gptfuzzer`, `med_safety_bench` ✅ **(new)**. SGXSTest skipped (RedBench strips its safe/unsafe labels; labeled source gated).* 🔴 ⭐ — *arXiv 2026* — `arXiv:2601.03699`

### Value alignment / ethics (currently narrow)
- [ ] **ETHICS** 🔴 ⭐⭐⭐ — *ICLR 2021* — 134K moral-judgment items; classic, highly cited. `github.com/hendrycks/ethics`
- [ ] **GlobalOpinionQA** 🔴 ⭐⭐⭐ — *ICML 2023 (Anthropic)* — 2,556 cross-national opinion items. `hf/Anthropic/llm_global_opinions`

### Bias depth & MCQ safety
- [x] **BBQ** ✅ **(new)** 🟢 ⭐⭐⭐ — *ACL Findings 2022* — social-bias QA (58,492). Task `bbq` (enabled; stereotype_avoidance). 
- [ ] **SafetyBench** 🔴 ⭐⭐⭐ — *ACL 2024* — 11,435 MCQ safety items (EN+ZH). `github.com/thu-coai/SafetyBench`
- [ ] **DiscrimEval** 🔴 ⭐⭐ — *Anthropic 2023* — 9,450 discrimination decision scenarios. `hf/Anthropic/discrim-eval`
- [x] **RealToxicityPrompts** ✅ **(new)** 🟡 ⭐⭐⭐ — *EMNLP Findings 2020* — 99,441 toxicity prompts. Task `realtoxicityprompts` (messages override; continuation framing). 

### Multi-turn dialogue safety
- [x] **DiaSafety** ✅ **(new)** 🔴 ⭐⭐ — *ACL Findings 2022* — context-sensitive dialogue safety. Task `diasafety` (1,095 test, generative + harmful judge; distinct from ParlAI `dialogue_safety`). `github.com/thu-coai/DiaSafety`
- [x] **CoSafe** ✅ **(new)** 🔴 ⭐⭐ — *EMNLP 2024* — 1,400 multi-turn dialogue-safety items. Task `cosafe` (5-turn, coreference attack, adversarial). `github.com/ErxinYu/CoSafe-Dataset`

---

## P2 — Specialized & remaining recent

- [x] **MedSafetyBench** ✅ **(new)** 🔴 ⭐⭐ — *NeurIPS 2024 D&B* — medical-safety prompts (only domain-specific option). Task `med_safety_bench` (900, via RedBench compilation). `github.com/AI4LIFE-GROUP/med-safety-bench`
- [x] **CASE-Bench** ✅ **(new)** 🔴 ⭐⭐ — *ICML 2025* — context-aware safety. Task `case_bench` (900, behaviour_match; context as verified grounding, refuse-if-unsafe-context / answer-if-safe-context). `github.com/BriansIDP/CASEBench`, `arXiv:2501.14940`
- [x] **CatQA** ✅ **(new)** 🔴 ⭐⭐ — *ACL 2024* — 550 categorical harmful. Task `catqa` (via RedBench compilation, EN). `github.com/declare-lab/resta`
- [x] **ForbiddenQuestions** ✅ **(new)** 🔴 ⭐⭐ — *CCS 2024 ('Do Anything Now')* — 390 disallowed-scenario prompts. Task `forbidden_questions` (via RedBench). `arXiv:2308.03825`
- [x] **GPTFuzzer** ✅ **(new)** 🔴 ⭐⭐ — *2023* — 100 auto-generated jailbreak prompts. Task `gptfuzzer` (adversarial, via RedBench). `arXiv:2309.10253`
- [ ] **AttaQ** 🔴 ⭐ — *EMNLP-BlackboxNLP 2023* — 1,402 adversarial harmful questions. `hf/ibm/AttaQ`
- [ ] **S-Eval** 🔴 ⭐ — *arXiv 2024* — ~20K EN+ZH comprehensive taxonomy + attacks. `github.com/IS2Lab/S-Eval`
- [x] **StealthGraph** ✅ **(new)** 🔴 — *arXiv 2026* — implicit domain-harm (med/finance/law/education). Task `stealth_graph` (3,163, adversarial; uses the obfuscated stealth-prompt variant). `github.com/ZJUIDG-AIVA/StealthGraph`
- [ ] **SEA-SafeguardBench / Taiwan Safety Benchmark** 🔴 ⭐ — *2025–2026* — newest regional sets (see Newest).
- ⏭️ **TeleAI-Safety** — evaluated, deferred (framework + only 342 prompts; overlaps existing jailbreak coverage; see Newest).

---

## Quick-wins backlog (in-repo, low coverage value but cheap)
From [datasets_in_repo_unused.csv](datasets_in_repo_unused.csv):
- [ ] **SafetyPrompt (Chinese)** 🟡 — fix invalid-JSON file (Python-dict repr), then enable (adds ZH volume).
- [ ] **GA Long-Context Jailbreak** 🟡 — `messages` override + import.
- [ ] **ControversialInstructions** 🟡 — needs `OPENAI_API_KEY` (OpenAI Moderation evaluator).
- [ ] **SycophancyEvalFeedback** 🟡 — debug "scores all identical".
- [ ] **TruthfulQA mc2/gen**, **QHarm**, **StrongREJECT** 🟡 — revise eval / curate / dedup, then enable.
- [ ] **AttackCiphering / MTBench / PersonalInfoLeak context+zero_shot** 🔴 — decode step / multi-turn / chat-format work.
- ⛔ **AnthropicHarmlessBase** — keep disabled (DPO pairs, not chat eval).

---

## Sources
- [Awesome-LLM-Safety datasets index](https://github.com/ydyjya/Awesome-LLM-Safety/blob/main/subtopic/Datasets%26Benchmark.md) · [SafetyPrompts.com](https://safetyprompts.com/)
- 2026: [IndicSafe (arXiv:2603.17915)](https://arxiv.org/html/2603.17915v1) · [RedBench (arXiv:2601.03699)](https://arxiv.org/html/2601.03699) · [Taiwan Safety Benchmark (arXiv:2603.07286)](https://arxiv.org/pdf/2603.07286) · [StealthGraph (arXiv:2601.04740)](https://arxiv.org/pdf/2601.04740)
- 2025: [OR-Bench (ICML 2025)](https://proceedings.mlr.press/v267/cui25a.html) · [FalseReject (COLM 2025, arXiv:2505.08054)](https://arxiv.org/pdf/2505.08054) · [CASE-Bench (ICML 2025, arXiv:2501.14940)](https://arxiv.org/pdf/2501.14940)
- 2024: [SALAD-Bench (ACL 2024)](https://github.com/OpenSafetyLab/SALAD-BENCH) · [WildGuard (NeurIPS 2024)](https://hf.co/datasets/allenai/wildguardmix) · [MedSafetyBench (NeurIPS 2024)](https://github.com/AI4LIFE-GROUP/med-safety-bench) · [PolygloToxicityPrompts (COLM 2024)](https://openreview.net/pdf?id=ootI3ZO6TJ)
