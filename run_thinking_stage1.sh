#!/usr/bin/env bash
# Stage 1 only: generate responses (with <think_fast> reasoning captured) for the
# thinking-vs-answer safety eval. Safety/adversarial subset, N=200 (cap).
# Resumable: tasks with an existing response file are skipped.
set -uo pipefail

REPO="/Users/sama/Documents/LIBRAI/libra-eval"
cd "$REPO" || exit 1

PY="$REPO/.venv/bin/python3"
MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUTDIR="$REPO/outputs_thinking_full"
N=200
LOG="$REPO/outputs_thinking_full_gen.log"

TASKS="advbench,harmfulq,harm_bench_new,malicious_instruct_new,malicious_instructions_new,do_not_answer,forbidden_questions,catqa,clearharm,hex_phi,salad_bench,red_eval_dangerous_qa,red_eval_harmful_qa,simple_safety_test,beavertails_bad,med_safety_bench,cyberattack_assistance,cyberseceval4_mitre,sorry_bench,dan_jailbreak,dan_regular,ga_jailbreak,gptfuzzer,jailbreakbench,jbdistill_bench,jbshield,latent_jailbreak,wildjailbreak,tdc_red_teaming,hack_a_prompt,gandalf_ignore_instructions,prompt_injection,prompthijackingrobustness,prompt_extraction_robustness,librai_adv_deep_inception,librai_adv_do_anything_now,librai_adv_effect_to_cause,librai_adv_few_shots,librai_adv_multilingual,librai_adv_one_sided_statement,librai_adv_persona_modulation,librai_adv_prompt_injection,librai_adv_refusal_suppression,librai_adv_tense_change,aart,anthropic_redteam,aya_redteaming,bad,dialogue_safety,diasafety,cosafe,dices350,cona,case_bench,stealth_graph,realtoxicityprompts,toxicchat,toxigen,or_bench_toxic,confaide,decoding_trust_privacy,personalinfoleak_few_shot,physical_safety_instructions_unsafe,xsafety,xstest"

mkdir -p "$OUTDIR"
echo "=== STAGE1 (tmux) START $(date) ===" | tee -a "$LOG"

# Self-healing retry loop. run_eval exits 0 even when a server outage leaves a
# task saved as an all-empty file, and resume skips files that merely EXIST --
# so each pass first deletes missing/empty task files (_thinking_clean.py), then
# regenerates them. Loops until every expected task has a non-empty file, or
# MAX_ATTEMPTS is hit. Survives repeated transient server outages.
MAX_ATTEMPTS=50
REMAINING=999
for attempt in $(seq 1 $MAX_ATTEMPTS); do
    CLEAN=$("$PY" "$REPO/_thinking_clean.py" "$OUTDIR" "$TASKS" 2>>"$LOG")
    REMAINING=$(echo "$CLEAN" | sed -n 's/^REMAINING=//p')
    echo "--- attempt $attempt/$MAX_ATTEMPTS  tasks needing generation: $REMAINING  $(date) ---" | tee -a "$LOG"
    if [ "${REMAINING:-1}" -eq 0 ]; then
        echo "--- all tasks have non-empty responses ---" | tee -a "$LOG"
        break
    fi
    "$PY" -m libra_eval.run_eval \
        --client local --models "$MODEL" --tasks "$TASKS" \
        --n_samples_per_task "$N" --mode inference \
        --generation_params '{"max_tokens": 8192}' \
        --output_dir "$OUTDIR" >> "$LOG" 2>&1
    RC=$?
    echo "--- run_eval pass $attempt exited rc=$RC ---" | tee -a "$LOG"
    # brief pause so a flapping server can recover before the next clean+pass
    sleep 30
done

echo "=== STAGE1 DONE remaining=$REMAINING $(date) ===" | tee -a "$LOG"
echo "DONE remaining=$REMAINING $(date)" > "$OUTDIR/STAGE1_DONE.txt"
