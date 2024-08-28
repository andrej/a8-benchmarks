import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
from collections import defaultdict
import styling
from styling import mean, stddev, stddev_perc

import figure_8_0_results as fig_8_0
from figure_11_0_results import *
from figure_11_1_results import *

baseline = mean(fig_8_0.results_0_read)

fig, ax, colors = styling.setup()

fig.set_figheight(2)


fork = {}
fork[1000000] = results_fork_1000000
fork[100000]  = results_fork_100000
fork[10000]   = results_fork_10000
fork[1000]    = results_fork_1000
fork[100]     = results_fork_100
fork[10]      = results_fork_10
fork[1]       = results_fork_1
print("Max stddev: {}".format(max([stddev_perc(fork[x]) for x in fork]))) 

fork[1]       = results_fork_1
fork = {x : mean(fork[x]) for x in fork}

criu = {}
criu[1000000] = results_criu_1000000
criu[100000]  = results_criu_100000
criu[10000]   = results_criu_10000
criu[1000]    = results_criu_1000
criu[100]     = results_criu_100
criu[10]      = results_criu_10
criu = {x : mean(criu[x]) for x in criu}

groups = [
    "1",
    "10",
    "$\\mathregular{10^2}$",
    "$\\mathregular{10^3}$",
    "$\\mathregular{10^4}$",
    "$\\mathregular{10^5}$",
    "$\\mathregular{10^6}$",
]

per = {
    #"fork" : np.array([509.09, 95.01,   53.34,  49.34, 48.71, 48.86, 48.63]),
    "fork" : np.array([fork[1],
                       fork[10]     ,
                       fork[100]    ,
                       fork[1000]   ,
                       fork[10000]  ,
                       fork[100000] ,
                       fork[1000000]]),
    "CRIU" : np.array([0,
                       0     ,
                       criu[100]    ,
                       criu[1000]   ,
                       criu[10000]  ,
                       criu[100000] ,
                       criu[1000000]]),
}
per["fork"] /= baseline
per["CRIU"] /= baseline


# Geunwoo's numbers
#fork_base = 3.908
#criu_base = 7.456
#per = {
#    "fork checkpointing": (48.84/fork_base, 57.964/fork_base, 60.376/fork_base, 174.904/fork_base, 733.98/fork_base, 1097.908/fork_base),
#    "CRIU checkpointing": (120, 1100, 13592, 0, 0, 0)
#}

df_dict = defaultdict(list)
for method, perf_list in per.items():
    assert len(perf_list) == len(groups)
    for idx, perf in enumerate(perf_list):
        syscall_name = groups[idx]
        df_dict["syscall_name"].append(syscall_name)
        df_dict["method"].append(method)
        df_dict["perf"].append(perf)

df = pd.DataFrame(dict(df_dict))


sns.barplot(ax=ax, x='syscall_name', y='perf', hue="method", data=df) 

for bars in ax.containers:
    ax.bar_label(bars, fmt='%.0fx', rotation='vertical', 
                 **styling.bar_label_styles)


# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel("Runtime Overhead")
ax.set_xlabel("Checkpointing Period")
ax.set_title("Checkpointing Overhead", **styling.titlefont)
ax.set_yscale('log')
ax.set_ylim(ymin=1, top=10**5)

ax.legend(ncols=2, **styling.legend)

sns.despine()
plt.tight_layout()
fig.savefig('figure_11.pdf')

