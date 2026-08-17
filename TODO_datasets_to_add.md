# TODO — Improve Safety-Evaluation Coverage

Goal: **balanced coverage across the safety risk taxonomy** for **text chat** evaluation (single/multi-turn prompt → response). **Out of scope: multimodal (vision/audio) and agentic/tool-use datasets.**

Prioritization = **coverage gap × reputation × recency**.
- **Effort:** 🟢 minutes (already in repo) · 🟡 small code/format work · 🔴 download + new task class.
- **Reputation:** ⭐⭐⭐ top venue + standard/highly-cited · ⭐⭐ solid venue / well-used · ⭐ recent/emerging, few citations yet.

Inputs: [datasets_in_repo_unused.csv](datasets_in_repo_unused.csv), [datasets_not_available_in_repo.csv](datasets_not_available_in_repo.csv), and June-2026 research.

---

## Coverage scorecard (67 active datasets — 20 **(new)** added recently; WMDP & Chinese-only sets excluded)

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
| **Multi-turn escalation (Crescendo/many-shot)** | ✅ **(new)** MHJ added (537 human multi-turn jailbreaks); CoSafe/DiaSafety cover coreference | optional: SafeMTData, Crescendo (adaptive) |
| **CBRN uplift (bio/chem, graded)** | 🟨 proxy only (ClearHarm; WMDP excluded) | **P1** (SciSafeEval, ChemSafetyBench) |
| **Deception / honesty / eval-awareness** | ✅ **(new)** MASK added (honesty-under-pressure, provided+known facts); eval-awareness (SAD) still open | optional: SAD, MACHIAVELLI |
| **Mental-health / crisis response** | 🟥 **missing** (self-harm only as a harm tag) | **P2** (custom rubric; CLPsych/C-SSRS proxies) |
| **Insecure code generation** | 🟥 **missing** (`cyberseceval4_mitre` = offensive only) | **P2** (CyberSecEval insecure-code, SecurityEval) |
| **Persuasion / influence ops** | 🟨 partial (one_sided_statement, CASE) | **P3** (Anthropic Persuasion) |

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

## 🧭 Frontier-surface gaps (text-chat) — recommended next

Surfaces that current LLM-safety practice (2025–26) treats as important but the suite covers weakly or not at all. **Agentic/tool-use is intentionally excluded** (covered in a separate report); **multimodal** is out of scope (text-only model). Locators are best-effort — **verify before download**. Scoring fit noted per item (most slot into the existing generation + harmful-judge harness).

### Multi-turn escalation & many-shot jailbreaks — 🟨 partial
- [x] **MHJ (Multi-Turn Human Jailbreaks)** ✅ **(new)** 🔴 ⭐⭐ — *Scale AI, 2024* — 537 human multi-turn jailbreaks. Task `mhj` (multi, harmful judge; full escalation replayed as consecutive user turns, judge the final answer). `arXiv:2408.15221`, `hf/ScaleAI/mhj`
- [ ] **SafeMTData / ActorAttack** 🔴 ⭐⭐ — *"Derail Yourself", 2024* — multi-turn attack via self-discovered clue chains. *Fit: drop-in multi-turn.* `arXiv:2410.10700`, `hf/SafeMTData`
- [ ] **Crescendo** 🔴 ⭐⭐ — *Microsoft, 2024* — gradual benign→harmful escalation (a method + seed set; you run the escalation, judge final turn). `arXiv:2404.01833`
- [ ] **RedQueen** 🔴 ⭐ — *2024* — concealed multi-turn jailbreaking at scale. `arXiv:2409.17458`

### CBRN proxies (bio/chem refusal) — 🟨 proxy only
- [ ] **SciSafeEval** 🔴 ⭐⭐ — *2024* — safety/refusal across chemistry, biology, medicine, physics. *Fit: generation + harmful-judge — best direct fit.* `arXiv:2410.03769`
- [ ] **ChemSafetyBench** 🔴 ⭐ — *2024* — chemistry-specific harmful-request refusal. *Fit: refusal-judge.* `arXiv:2411.16736`
- [ ] **LAB-Bench** (dual-use subset) 🔴 ⭐⭐ — *FutureHouse, 2024* — biology protocol/reasoning; use the dual-use slice as a gated uplift proxy (capability, not refusal). `arXiv:2407.10362`
- [ ] **ChemBench** 🔴 ⭐⭐ — *2024* — chemistry knowledge incl. safety items; knowledge-style complement. `arXiv:2404.01475`
> ⚠️ These are **knowledge/refusal proxies, not human-uplift studies**, and should be gated. This is the surface WMDP was excluded from (knowledge probe, not refusal test).

### Deception / honesty / eval-awareness — 🟥 missing
- [x] **MASK** ✅ **(new)** 🔴 ⭐⭐ — *CAIS, 2025* — lying under pressure, **disentangled from accuracy**. Tasks `mask_provided_facts` (274, in-context truth → cleanest honesty) + `mask_known_facts` (209, world-fact). Custom `MASK_Honesty` judge (verdict honest/lie/evade → honesty score); single-pass version (belief-elicitation pass = future). `arXiv:2503.03750`
- [ ] **SAD (Situational Awareness Dataset)** 🔴 ⭐⭐ — *2024* — does the model know it's an AI / being tested. `arXiv:2407.04694`
- [ ] **MACHIAVELLI** 🔴 ⭐⭐⭐ — *ICML 2023* — power-seeking, deception, ethical violations in text games (larger harness, behavioral). `arXiv:2304.03279`
- [ ] **Apollo insider-trading / sandbagging scenarios** 🔴 ⭐⭐ — *2023–24* — strategic deception under incentive; scenario + custom judge. `arXiv:2311.07590`

### Mental-health / crisis response — 🟥 missing
- [ ] **Custom curated set + rubric** 🔴 — the behavior that matters (de-escalate + resource, *not* flat refusal) has no good off-the-shelf benchmark; build a small curated set with a support-quality rubric.
- [ ] **CLPsych shared-task data** 🔴 ⭐⭐ — suicide-risk severity (access-controlled; detection proxy).
- [ ] **Reddit C-SSRS** (Gaur et al.) 🔴 ⭐ — suicide-severity labels; detection proxy.
- [ ] **IMHI / MentaLLaMA** 🔴 ⭐⭐ — *WWW 2024* — mental-health reasoning/explanation (classification, not response-safety). `arXiv:2309.13567`

### Insecure code generation — 🟥 missing
- [ ] **CyberSecEval — insecure-code track** 🔴 ⭐⭐⭐ — *Meta Purple Llama* — whether normal coding answers introduce CWEs (complements offensive `cyberseceval4_mitre`). `arXiv:2312.04724` / v2 `2404.13161` / v3 `2408.01605`
- [ ] **SecurityEval** 🔴 ⭐⭐ — *MSR4P&S 2022* — CWE-tagged insecure generations; static-analysis scored. `github.com/s2e-lab/SecurityEval`
- [ ] **SALLM** 🔴 ⭐ — *2023* — security of LLM-generated code. `arXiv:2311.00889`
- [ ] **CWEval** 🔴 ⭐ — *2025* — security + functionality jointly. (verify locator)

### Persuasion / influence ops — 🟨 partial
- [ ] **Anthropic Persuasion** 🔴 ⭐⭐ — *Anthropic, 2024* — persuasiveness of generated arguments (capability-as-risk). `hf/Anthropic/persuasion`
- [ ] Targeted-disinfo prompts — construct from existing `case_bench` / propaganda subsets (reuse harness; no new download).

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
