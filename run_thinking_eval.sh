#!/usr/bin/env bash
# Thinking-vs-answer safety evaluation for the local k2moe reasoning model.
# Generates responses (with <think_fast> reasoning captured), then runs the
# harmful-check pipeline that judges thinking process vs final answer separately.
# Safety/adversarial subset only (tasks where refusal/jailbreak makes the
# thinking-vs-answer divergence meaningful). Designed to run unattended in tmux.
#
# N=200 is a CAP, not a target: full datasets yield 200, smaller ones yield their
# full size -- reproducing the same per-task counts (and rows) as outputs_full_200.
set -uo pipefail

REPO="/Users/sama/Documents/LIBRAI/libra-eval"
cd "$REPO" || exit 1

PY="$REPO/.venv/bin/python3"
MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUTDIR="$REPO/outputs_thinking_full"
N=200
LOG="$REPO/outputs_thinking_full_run.log"

# --- Safety / adversarial task subset ---------------------------------------
# Direct harmful requests
TASKS="advbench,harmfulq,harm_bench_new,malicious_instruct_new,malicious_instructions_new"
TASKS="$TASKS,do_not_answer,forbidden_questions,catqa,clearharm,hex_phi,salad_bench"
TASKS="$TASKS,red_eval_dangerous_qa,red_eval_harmful_qa,simple_safety_test,beavertails_bad"
TASKS="$TASKS,med_safety_bench,cyberattack_assistance,cyberseceval4_mitre,sorry_bench"
# Jailbreaks / adversarial prompting
TASKS="$TASKS,dan_jailbreak,dan_regular,ga_jailbreak,gptfuzzer,jailbreakbench,jbdistill_bench"
TASKS="$TASKS,jbshield,latent_jailbreak,wildjailbreak,tdc_red_teaming,hack_a_prompt"
TASKS="$TASKS,gandalf_ignore_instructions,prompt_injection,prompthijackingrobustness,prompt_extraction_robustness"
TASKS="$TASKS,librai_adv_deep_inception,librai_adv_do_anything_now,librai_adv_effect_to_cause"
TASKS="$TASKS,librai_adv_few_shots,librai_adv_multilingual,librai_adv_one_sided_statement"
TASKS="$TASKS,librai_adv_persona_modulation,librai_adv_prompt_injection,librai_adv_refusal_suppression,librai_adv_tense_change"
# Red-team / harmful dialogue
TASKS="$TASKS,aart,anthropic_redteam,aya_redteaming,bad,dialogue_safety,diasafety,cosafe,dices350"
TASKS="$TASKS,cona,case_bench,stealth_graph"
# Toxicity generation
TASKS="$TASKS,realtoxicityprompts,toxicchat,toxigen,or_bench_toxic"
# Privacy / PII harm
TASKS="$TASKS,confaide,decoding_trust_privacy,personalinfoleak_few_shot"
# Physical / multilingual safety + over-refusal
TASKS="$TASKS,physical_safety_instructions_unsafe,xsafety,xstest"

mkdir -p "$OUTDIR"
echo "=== START $(date) ===" | tee -a "$LOG"
echo "model=$MODEL  n=$N  outdir=$OUTDIR" | tee -a "$LOG"
echo "tasks=$TASKS" | tee -a "$LOG"

# 1. Generate responses (inference only; reasoning captured as <think_fast>)
"$PY" -m libra_eval.run_eval \
    --client local \
    --models "$MODEL" \
    --tasks "$TASKS" \
    --n_samples_per_task "$N" \
    --mode inference \
    --generation_params '{"max_tokens": 8192}' \
    --output_dir "$OUTDIR" \
    2>&1 | tee -a "$LOG"
GEN_RC=${PIPESTATUS[0]}
echo "=== GENERATION rc=$GEN_RC $(date) ===" | tee -a "$LOG"

# 2. Thinking-vs-answer harmful check
EVAL_KEY=$("$PY" -c "import json;print(json.load(open('$REPO/libra_eval/config/api_config.json'))['EVAL_API_KEY'])")
"$PY" "$REPO/batch_harmful_check.py" \
    --api_key "$EVAL_KEY" \
    --model "openai/gpt-4o" \
    --base_url "https://openrouter.ai/api/v1" \
    --input_dir "$OUTDIR/responses" \
    --output_dir "$OUTDIR/harmful_checks" \
    --max_concurrent 5 \
    --resume \
    2>&1 | tee -a "$LOG"
echo "=== HARMFUL CHECK done $(date) ===" | tee -a "$LOG"

# 3. Divergence analysis + HTML report
"$PY" "$REPO/analyze_harmful_checks.py" \
    --harmful_check_dir "$OUTDIR/harmful_checks" \
    --output_dir "$REPO/harmful_check_analysis_thinking" \
    2>&1 | tee -a "$LOG"
"$PY" "$REPO/generate_harmful_check_html.py" 2>&1 | tee -a "$LOG"

echo "DONE gen_rc=$GEN_RC $(date)" > "$OUTDIR/RUN_DONE.txt"
echo "=== ALL DONE $(date) ===" | tee -a "$LOG"
