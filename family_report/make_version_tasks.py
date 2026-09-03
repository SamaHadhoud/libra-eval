"""fam_version_tasks: per-task grouped bars, anchor vs the version-comparison
model (K2-V2), across all shared main-suite tasks, split over two stacked rows.
Used by BOTH the condensed cross-surface report (K2-V3-Family-Red-Teaming) and
the family chat report (K2-V3-Family-Chat-Red-Teaming, section 9, alongside the
by-domain fam_version_comparison).

Run AFTER generate_family.py (which clears figures/fam_*.pdf on each run):
    python3 make_version_tasks.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_lib as F
from family_lib import FamilyData

import generate_family as G  # rcParams styling + save()

fd = FamilyData()
anchor = fd.anchor
comp = fd.comparisons[0]

tasks = [t for t in fd.main_tasks
         if fd.score(anchor, t) is not None and fd.score(comp, t) is not None]
half = (len(tasks) + 1) // 2
rows = [tasks[:half], tasks[half:]]

fig, axes = plt.subplots(2, 1, figsize=(11.5, 6.4))
w = 0.38
for ax, row in zip(axes, rows):
    xs = np.arange(len(row))
    a_vals = [fd.score(anchor, t) for t in row]
    c_vals = [fd.score(comp, t) for t in row]
    ax.bar(xs - w / 2, a_vals, width=w, color=anchor.color, label=anchor.label)
    ax.bar(xs + w / 2, c_vals, width=w, color=comp.color, label=comp.label)
    ax.set_xticks(xs)
    ax.set_xticklabels([F.pretty_task(t) for t in row],
                       rotation=60, ha="right", fontsize=5.2)
    ax.set_ylim(0, 1.02)
    ax.set_xlim(-0.7, len(row) - 0.3)
    ax.set_ylabel("Score", fontsize=8)
    ax.tick_params(axis="y", labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)
axes[0].legend(frameon=False, fontsize=8, ncol=2,
               loc="lower left", bbox_to_anchor=(0.0, 1.02))
fig.tight_layout(h_pad=1.4)
G.save(fig, "fam_version_tasks")
