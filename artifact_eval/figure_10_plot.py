import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
from collections import defaultdict
import styling
from styling import mean, stddev, stddev_perc


import figure_8_0_results as fig_8_0
from figure_10_results import *

baseline = mean(fig_8_0.results_0_read)

data = {}
data[0]    =  results_0
data[512]  =  results_512
data[1024] =  results_1024
data[2048] =  results_2048
data[4096] =  results_4096
data[8192] =  results_8192
data[16384]=  results_16384

fig, ax, colors = styling.setup()
fig.set_figheight(2)


print("Max stddev: {:.02f}%".format(max(stddev_perc(data[x]) for x in data)))
data = [mean(data[x]) for x in data]

xs = (
    'none',
    '512',
    '1024',
    '2048',
    '4096',
    '8192',
    '16384'
)

ys = {
    "Replication" :  data 
}

for y_i, y in ys.items():
    ys[y_i] /= baseline

category_colors = [colors[0], colors[1], colors[3]]

width = 0.5

bottom = np.zeros(len(xs))

for y_i, (label, y) in enumerate(ys.items()):
    p = ax.bar(xs, y, width, label=label, bottom=bottom, color=category_colors[y_i])
    if label == "Replication":
        ax.bar_label(p, fmt='%.1fx', **styling.bar_label_styles)
    bottom += y

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel("Runtime Overhead")
ax.set_xlabel("Replication Batch Size (bytes)")
ax.set_title("Replicated System Call Overhead", **styling.titlefont)
ax.legend(ncols=3, bbox_to_anchor=(1, 1.05), **styling.legend)
ax.set_ylim([0,40])

sns.despine()
plt.tight_layout()
fig.savefig('figure_10.pdf')
# plt.show()
