# Judge correlation: openai/gpt-4o vs openai/gpt-5.6-terra

- Tasks compared: **80** | items: **14,705**
- Per-task score correlation: Pearson **0.9293**, Spearman **0.7997**
- Mean |score delta| per task: **0.0250** (max 0.2175)
- Per-item score agreement: **95.16%** (Pearson 0.7206)
- Binary-verdict judges (11,425 items): agreement **96.96%**, Cohen's kappa **0.7122**

## Agreement by judge family

| evaluator                               |   n_items |   item_agreement |   pearson_item |
|:----------------------------------------|----------:|-----------------:|---------------:|
| Junjie Gao/Harmful_judge/V6             |     10579 |           0.968  |         0.547  |
| LibrAI/DoNotAnswer_Refusal_Detection/V4 |      1400 |           0.9514 |         0.8732 |
| Local/Answer_Correctness_Judge/V1       |       400 |           0.905  |         0.7188 |
| LibrAI/Label_Compare/V1                 |       200 |           1      |         1      |
| LibrAI/Last_Message_Harmful_Judger/V3   |       200 |           1      |       nan      |
| Local/Bias_Judge/V1                     |       200 |           1      |       nan      |
| Local/CoCoNot_Judge/V1                  |       200 |           0.895  |         0.5703 |
| Local/Harmscore_Judge/V1                |       200 |           0.98   |         0.603  |
| Local/Injection_Question_Judge/V1       |       200 |           0.855  |         0.7005 |
| Local/Mimicry_Correction                |       200 |           0.98   |         0.9027 |
| Local/MoralChoice_Action/V1             |       200 |           0.915  |         0.626  |
| Local/Offensiveness_Judge/V1            |       200 |           0.98   |         0.4427 |
| Local/Secret_Leak_Judge/V1              |       200 |           0.995  |         0.9872 |
| UAE_Controversial                       |       200 |           0.47   |         0.6049 |
| LibrAI/fastchat-vicuna-single/V1        |        80 |           0.0875 |         0.139  |
| Local/Confaide_Disclosure               |        46 |           0.8261 |       nan      |

## Tasks by |score delta| (new minus gpt-4o)

| task                                    | evaluator                               |   n |   n_judged |   score_gpt4o |   score_new |   delta |   item_agreement |
|:----------------------------------------|:----------------------------------------|----:|-----------:|--------------:|------------:|--------:|-----------------:|
| vicuna_bench_200                        | LibrAI/fastchat-vicuna-single/V1        |  80 |         80 |        0.9938 |      0.7762 | -0.2175 |           0.0875 |
| prompt_injection_200                    | Local/Injection_Question_Judge/V1       | 200 |        200 |        0.78   |      0.635  | -0.145  |           0.855  |
| uae_controversial_200                   | UAE_Controversial                       | 200 |        200 |        0.955  |      0.815  | -0.14   |           0.47   |
| jbdistill_bench_200                     | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.88   |      0.76   | -0.12   |           0.85   |
| sycophancy_eval_answer_200              | Local/Answer_Correctness_Judge/V1       | 200 |        200 |        0.89   |      0.79   | -0.1    |           0.85   |
| ga_jailbreak_200                        | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.99   |      0.91   | -0.08   |           0.9    |
| stealth_graph_200                       | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.98   |      0.9    | -0.08   |           0.92   |
| coconot_original_200                    | Local/CoCoNot_Judge/V1                  | 200 |        200 |        0.835  |      0.9    |  0.065  |           0.895  |
| librai_adv_one_sided_statement_200      | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.895  |      0.95   |  0.055  |           0.875  |
| xsafety_200                             | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.93   |      0.98   |  0.05   |           0.92   |
| latent_jailbreak_200                    | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.955  |      1      |  0.045  |           0.955  |
| do_not_answer_fn_200                    | LibrAI/DoNotAnswer_Refusal_Detection/V4 | 200 |        200 |        0.79   |      0.835  |  0.045  |           0.915  |
| or_bench_hard_1k_200                    | LibrAI/DoNotAnswer_Refusal_Detection/V4 | 200 |        200 |        0.49   |      0.445  | -0.045  |           0.905  |
| confaide_200                            | Local/Confaide_Disclosure               | 200 |         46 |        0.9888 |      0.9487 | -0.04   |           0.8261 |
| harm_bench_new_200                      | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.96   |      0.925  | -0.035  |           0.955  |
| librai_adv_persona_modulation_200       | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.825  |      0.79   | -0.035  |           0.935  |
| clearharm_200                           | Junjie Gao/Harmful_judge/V6             | 179 |        179 |        0.9888 |      0.9553 | -0.0335 |           0.9665 |
| librai_adv_do_anything_now_200          | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.785  |      0.815  |  0.03   |           0.93   |
| librai_adv_deep_inception_200           | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.94   |      0.91   | -0.03   |           0.94   |
| tdc_red_teaming_200                     | Junjie Gao/Harmful_judge/V6             | 100 |        100 |        1      |      0.97   | -0.03   |           0.97   |
| jailbreakbench_200                      | Junjie Gao/Harmful_judge/V6             | 100 |        100 |        1      |      0.97   | -0.03   |           0.97   |
| xstest_200                              | LibrAI/DoNotAnswer_Refusal_Detection/V4 | 200 |        200 |        0.915  |      0.885  | -0.03   |           0.97   |
| case_bench_200                          | LibrAI/DoNotAnswer_Refusal_Detection/V4 | 200 |        200 |        0.75   |      0.725  | -0.025  |           0.955  |
| aya_redteaming_200                      | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.96   |      0.985  |  0.025  |           0.955  |
| do_not_answer_fp_200                    | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.995  |      0.97   | -0.025  |           0.965  |
| physical_safety_instructions_safe_200   | LibrAI/DoNotAnswer_Refusal_Detection/V4 | 100 |        100 |        0.99   |      0.97   | -0.02   |           0.98   |
| librai_adv_refusal_suppression_200      | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.915  |      0.935  |  0.02   |           0.94   |
| cyberseceval4_mitre_200                 | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.835  |      0.855  |  0.02   |           0.9    |
| sycophancy_eval_mimicry_200             | Local/Mimicry_Correction                | 200 |        200 |        0.88   |      0.9    |  0.02   |           0.98   |
| bad_200                                 | Local/Offensiveness_Judge/V1            | 200 |        200 |        0.995  |      0.975  | -0.02   |           0.98   |
| malicious_instruct_new_200              | Junjie Gao/Harmful_judge/V6             | 100 |        100 |        1      |      0.98   | -0.02   |           0.98   |
| diasafety_200                           | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.995  |      0.975  | -0.02   |           0.98   |
| false_reject_200                        | LibrAI/DoNotAnswer_Refusal_Detection/V4 | 200 |        200 |        0.415  |      0.395  | -0.02   |           0.96   |
| wildjailbreak_200                       | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.96   |      0.94   | -0.02   |           0.97   |
| do_not_answer_200                       | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.995  |      0.98   | -0.015  |           0.985  |
| or_bench_toxic_200                      | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      0.985  | -0.015  |           0.985  |
| librai_adv_prompt_injection_200         | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.975  |      0.99   |  0.015  |           0.975  |
| gptfuzzer_200                           | Junjie Gao/Harmful_judge/V6             | 100 |        100 |        1      |      0.99   | -0.01   |           0.99   |
| librai_adv_multilingual_200             | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.975  |      0.985  |  0.01   |           0.99   |
| physical_safety_instructions_unsafe_200 | Junjie Gao/Harmful_judge/V6             | 100 |        100 |        0.99   |      0.98   | -0.01   |           0.99   |
| realtoxicityprompts_200                 | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.98   |      0.99   |  0.01   |           0.98   |
| librai_adv_tense_change_200             | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.995  |      0.985  | -0.01   |           0.99   |
| catqa_200                               | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.98   |      0.99   |  0.01   |           0.98   |
| red_eval_dangerous_qa_200               | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      0.99   | -0.01   |           0.99   |
| librai_adv_effect_to_cause_200          | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      0.99   | -0.01   |           0.99   |
| salad_bench_200                         | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.99   |      0.98   | -0.01   |           0.98   |
| advbench_200                            | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      0.99   | -0.01   |           0.99   |
| cyberattack_assistance_200              | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.88   |      0.89   |  0.01   |           0.88   |
| forbidden_questions_200                 | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      0.99   | -0.01   |           0.99   |
| sycophancy_eval_are_you_sure_200        | Local/Answer_Correctness_Judge/V1       | 200 |        200 |        0.74   |      0.75   |  0.01   |           0.96   |
| anthropic_redteam_200                   | Local/Harmscore_Judge/V1                | 200 |        200 |        0.98   |      0.97   | -0.01   |           0.98   |
| toxicchat_200                           | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.99   |      0.98   | -0.01   |           0.98   |
| jbshield_200                            | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      0.99   | -0.01   |           0.99   |
| red_eval_harmful_qa_200                 | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.995  |      1      |  0.005  |           0.995  |
| sorry_bench_200                         | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.98   |      0.975  | -0.005  |           0.985  |
| beavertails_good_200                    | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.99   |      0.985  | -0.005  |           0.985  |
| aart_200                                | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.99   |      0.995  |  0.005  |           0.995  |
| moral_choice_200                        | Local/MoralChoice_Action/V1             | 200 |        200 |        0.765  |      0.76   | -0.005  |           0.915  |
| dan_regular_200                         | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.98   |      0.985  |  0.005  |           0.995  |
| gandalf_ignore_instructions_200         | Local/Secret_Leak_Judge/V1              | 200 |        200 |        0.74   |      0.735  | -0.005  |           0.995  |
| coconot_contrast_200                    | LibrAI/DoNotAnswer_Refusal_Detection/V4 | 200 |        200 |        0.965  |      0.96   | -0.005  |           0.995  |
| librai_adv_few_shots_200                | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      0.995  | -0.005  |           0.995  |
| harmfulq_200                            | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      0.995  | -0.005  |           0.995  |
| med_safety_bench_200                    | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.995  |      0.99   | -0.005  |           0.995  |
| hypothesis_stereotypes_200              | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      0.995  | -0.005  |           0.995  |
| bbq_200                                 | LibrAI/Label_Compare/V1                 | 200 |        200 |        0.985  |      0.985  |  0      |           1      |
| dan_jailbreak_200                       | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.91   |      0.91   |  0      |           0.97   |
| uae_safety_200                          | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.975  |      0.975  |  0      |           0.98   |
| toxigen_200                             | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.995  |      0.995  |  0      |           1      |
| hatexplain_200                          | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        1      |      1      |  0      |           1      |
| beavertails_bad_200                     | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.98   |      0.98   |  0      |           0.99   |
| hex_phi_200                             | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.995  |      0.995  |  0      |           1      |
| jailbreakbench_benign_200               | LibrAI/DoNotAnswer_Refusal_Detection/V4 | 100 |        100 |        0.86   |      0.86   |  0      |           0.94   |
| sp_misconceptions_200                   | Junjie Gao/Harmful_judge/V6             | 122 |        122 |        1      |      1      |  0      |           1      |
| cosafe_200                              | Junjie Gao/Harmful_judge/V6             | 200 |        200 |        0.92   |      0.92   |  0      |           0.95   |
| simple_safety_test_200                  | Junjie Gao/Harmful_judge/V6             | 100 |        100 |        1      |      1      |  0      |           1      |
| cona_200                                | Junjie Gao/Harmful_judge/V6             | 178 |        178 |        1      |      1      |  0      |           1      |
| malicious_instructions_new_200          | Junjie Gao/Harmful_judge/V6             | 100 |        100 |        1      |      1      |  0      |           1      |
| bold_200                                | Local/Bias_Judge/V1                     | 200 |        200 |        1      |      1      |  0      |           1      |
| dices350_200                            | LibrAI/Last_Message_Harmful_Judger/V3   | 200 |        200 |        1      |      1      |  0      |           1      |
