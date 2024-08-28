import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
from collections import defaultdict
import styling 
from styling import mean, stddev, stddev_perc

import figure_8_0_results as fig_8_0
import figure_8_2_results as fig_8_2
from figure_9_results import *

# We use ARM64 numbers for relative overhead, since it is the slower machine;
# our system couldn't possibly be faster.
baselines = np.array([mean(fig_8_0.results_0_read),
                      mean(fig_8_0.results_0_read_local),
                      mean(fig_8_0.results_0_getcwd),
                      mean(fig_8_0.results_0_sched_yield) ])

interp = {
"read":        fig_8_2.results_2_read,
"read local":  fig_8_2.results_2_read_local,
"getcwd":      fig_8_2.results_2_getcwd,
"sched_yield": fig_8_2.results_2_sched_yield,
}
proc = {
"read":        [a-b for a,b in zip(results_read_single, fig_8_2.results_2_read)],
"read local":  [a-b for a,b in zip(results_read_local_single, fig_8_2.results_2_read_local)],
"getcwd":      [a-b for a,b in zip(results_getcwd_single, fig_8_2.results_2_getcwd)],
"sched_yield": [a-b for a,b in zip(results_sched_yield_single, fig_8_2.results_2_sched_yield)]
}
cross = {
"read local":  [a-b for a,b in zip(results_read_local_full, proc["read local"])] ,
"getcwd":      [a-b for a,b in zip(results_getcwd_full, proc["getcwd"])] ,
"sched_yield": [a-b for a,b in zip(results_sched_yield_full, proc["sched_yield"])] ,
}
cross["read"] = [a-b for a,b in zip(results_read_full, results_read_no_cc)]
replication = results_read_no_cc


print("Max stddev: {:0.2f}%".format(max([max(stddev_perc(dat[x]) for x in ["read", "read local", "getcwd", "sched_yield"])
                                        for dat in [proc, cross]]
                                        + [stddev_perc(replication)])))

interp = {x : mean(interp[x]) for x in proc}
proc = {x : mean(proc[x]) for x in proc}
cross = {x : mean(cross[x]) for x in cross}
replication = mean(replication)

fig, ax, colors = styling.setup()
fig.set_figheight(2)

xs = (
    "read\n(device)",
    "read\n(file)",
    "getcwd",
    "sched_yield"
)


ys = {
    "Interposition":  np.array([interp["read"], interp["read local"], interp["getcwd"], interp["sched_yield"]]),
    "Processing":     np.array([proc["read"] - interp["read"], proc["read local"] - interp["read local"], proc["getcwd"] - interp["getcwd"], proc["sched_yield"] - interp["sched_yield"]]),
    "Cross-Checking": np.array([cross["read"] - replication, cross["read local"] - proc["read local"] - interp["read local"], cross["getcwd"] - proc["getcwd"] - interp["getcwd"], cross["sched_yield"] - proc["sched_yield"] - interp["sched_yield"]]),
    "Replication":    np.array([replication, 0, 0, 0])
}

width = 0.5

for x_i in range(len(xs)):
    for y_i, y in ys.items():
        y[x_i] /= baselines[x_i]

bottom = np.zeros(4)

for y_i, (label, y) in enumerate(ys.items()):
    p = ax.bar(xs, y, width, label=label, bottom=bottom, color=colors[y_i])
    if y_i == len(ys)-1:
        ax.bar_label(p, fmt='%.1f×', **styling.bar_label_styles)
    bottom += y

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel("Runtime Overhead")
ax.set_xlabel("")
ax.set_title("Cross-Checked System Call Overhead", **styling.titlefont)
#ax.set_ylim([0, 65])

ax.legend(ncols=2, **styling.legend)

sns.despine()
plt.tight_layout()
fig.savefig('figure_9.pdf')
# plt.show()
