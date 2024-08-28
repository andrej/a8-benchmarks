import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import styling
from styling import mean, stddev, stddev_perc

from figure_7_data import data

# ##########################################################################
# Plotting
# ##########################################################################

groups   = ["0 B", "512 B", "1 KB", "2 KB", "4 KB", "8 KB"]
x_labels = ["lighttpd", "nginx", "redis"]

relative = True
bar_label_fmt = "{:.0f}"
if relative:
    bar_label_fmt = "{:.2f}×"
    for x_label in x_labels:
        baseline = mean(data[x_label]["native"])
        for group in groups:
            data[x_label][group] = np.array(data[x_label][group]) / baseline

print("Max stddev: {:02f}%\n".format(max(max(stddev_perc(data[x][failure_prob])
                                             for failure_prob in groups) 
                                         for x in x_labels)))

fig, ax, colors = styling.setup()
colors = sns.color_palette(palette="mako_r")
fig.set_figheight(2)

#lighttpd_syscalls_per_req = 12
#nginx_syscalls_per_req = 9
#nginx_max_bars =    [nginx_native[0]    * (1-x)**nginx_syscalls_per_req    for x in (0, 0.001, 0.005, 0.01, 0.05)]
#lighttpd_max_bars = [lighttpd_native[0] * (1-x)**lighttpd_syscalls_per_req for x in (0, 0.001, 0.005, 0.01, 0.05)]
#
#max_bars = {
##    "nginx\n(protected)" :    nginx_max_bars,
##    "lighttpd\n(protected)" : lighttpd_max_bars
#}

width = 1.0/(len(groups) + 1) # + 1 for one bar width spacing between groups
x_coords = np.arange(len(x_labels))

for i, group in enumerate(groups):
    ys      = [data[x][group]       for x in x_labels]
    y_means = [mean(data[x][group]) for x in x_labels]
    y_maxs  = [max(data[x][group])  for x in x_labels]
    xs      = [x + width*i for x, y in zip(x_coords, y_maxs) if y > 0]
    # invisible bar to place a bar label at the max
    p = ax.bar(xs, y_maxs, width, color=(0,0,0,0))
    ax.bar_label(p, rotation='vertical', padding=3,
                 labels=[bar_label_fmt.format(y) for y in y_means],
                 **styling.bar_label_styles)
    ax.bar(xs, y_means, width, label=group, color=colors[i])
    #ax.boxplot(ys, positions=xs, widths=[.8*width]*len(xs), 
    #           **styling.boxplot_styles)

ax.set_xticks(x_coords + 0.5*(len(groups)-1)*width, x_labels)

# Add some text for labels, title and custom x-axis tick labels, etc.
legend_style = styling.legend
legend_style['loc'] = 'upper left'
legend_style['bbox_to_anchor'] = (0.9, 1)
ax.legend(title="Batch Size", ncols=1, **styling.legend)

ax.set_title("Performance By Batch Size (No Divergences)", **styling.titlefont)
ax.set_xlim([0-2*width, x_coords[-1]+len(groups)*width+2*width])
ax.tick_params(axis='x', which='both', bottom=False)
if not relative:
    ax.set_ylabel("× 1000 Requests per Second")
    yticks = list(range(2000, 30000+1, 4000))
    ytick_labels = ['{:.0f}'.format(y/1000) for y in yticks]
    ax.set_ylim([0,yticks[-1]])
else:
    ymax = 0.9
    ax.set_ylabel("Relative Throughput")
    yticks = np.linspace(0, ymax, 4) 
    ytick_labels = ['{:.1f}'.format(y) for y in yticks]
    ax.set_ylim([0, ymax])
ax.set_yticks(yticks, labels=ytick_labels)

sns.despine()
plt.tight_layout()
fig.savefig('figures/overall_batch_size.pdf')
# plt.show()
