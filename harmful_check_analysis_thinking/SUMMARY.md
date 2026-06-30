# Thinking-vs-Answer Safety Evaluation — Summary

**Model:** k2moe375B-mid3_v3-checkpoint_0003500   **Judge:** openai/gpt-4o (OpenRouter)
**Scope:** 65 safety/adversarial tasks, 12,232 responses judged (thinking trace + final answer scored separately)

## Headline numbers
| Metric | Count | Rate |
|---|---:|---:|
| Overall harmful | 696 | 5.7% |
| Thinking harmful | 628 | 5.1% |
| Final-answer harmful | 683 | 5.6% |
| Both harmful | 616 | 5.0% |
| **Thinking-only** (think harmful → answer safe) | 12 | 0.10% |
| **Answer-only** (answer harmful → think safe) | 67 | 0.55% |

## Interpretation
- Thinking and answer are **highly consistent** (616 of 696 harmful cases harmful in both). The model rarely hides harmful intent in reasoning that it then suppresses.
- **Answer-only divergence (67) > thinking-only (12)**: the more common failure is a *safe-looking reasoning trace that still yields a harmful final answer* — not the reverse. Worth a closer look at those 67 cases.
- Per-task divergence detail: `thinking_vs_response.csv`.
