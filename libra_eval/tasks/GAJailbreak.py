import pandas as pd
from .base import BaseDirectRiskyTask

# GA Jailbreak — genetic-algorithm-generated jailbreak prompts.
# data: GeneralAnalysis/GA_Jailbreak_Benchmark (this xlsx is an undocumented
# snapshot: it ships the attack DECOMPOSED into fields rather than a pre-assembled
# prompt, and no official template is published). We reconstruct the decomposition
# attack: the harmful `question` plus the GA-evolved sub-tasks (`function_d*`) and
# their required elements (`entity_d*`). The `*_e*` elaboration fields and the
# `target` affirmative opener are left out of the prompt (they describe the desired
# answer, not the request).


def _present(v):
    s = str(v).strip()
    return bool(s) and s.lower() not in ("[n/a]", "n/a", "nan", "none", "")


class GAJailbreak(BaseDirectRiskyTask):
    task_name = "ga_jailbreak"
    task_data_file = "GA Jailbreak.xlsx"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"

    def read_task_data(self):
        data_df = super().read_task_data()

        def build(row):
            parts = [str(row["question"]).strip()]
            subtasks = []
            for i in (1, 2, 3):
                fn, ent = row.get(f"function_d{i}"), row.get(f"entity_d{i}")
                if _present(fn):
                    line = str(fn).strip()
                    if _present(ent):
                        line += f" (include: {str(ent).strip()})"
                    subtasks.append(line)
            if subtasks:
                parts.append("Address each of the following in detail:")
                parts += [f"{i}. {s}" for i, s in enumerate(subtasks, 1)]
            prompt = "\n".join(parts)
            return [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]

        data_df["messages"] = data_df.apply(build, axis=1)
        return data_df
