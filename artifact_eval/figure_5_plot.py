import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import styling
from styling import mean, stddev, stddev_perc

from figure_5_6_7_native_results import *
from figure_5_results import *

# ##########################################################################
# Data
# ##########################################################################

data = {}

#  - breakpoint at ngx_close_connection
#  - policy socket_rw_oc
#  - batching 8192
data["nginx"] = {} 
data["nginx"]     ["native"] =  results_nginx_native
data["nginx"]         ["0%"] =  results_nginx[0]
data["nginx"]       ["0.1%"] =  results_nginx[0.001]
data["nginx"]       ["0.5%"] =  results_nginx[0.005]
data["nginx"]         ["1%"] =  results_nginx[0.01]
data["nginx"]         ["5%"] =  results_nginx[0.05]

#  - breakpoint at connection_close
#  - policy socket_rw_oc
#  - batching 8192
data["lighttpd"] = {}
data["lighttpd"]  ["native"] =  results_lighttpd_native
data["lighttpd"]      ["0%"] =  results_lighttpd[0]
data["lighttpd"]    ["0.1%"] =  results_lighttpd[0.001]
data["lighttpd"]    ["0.5%"] =  results_lighttpd[0.005]
data["lighttpd"]      ["1%"] =  results_lighttpd[0.01]
data["lighttpd"]      ["5%"] =  results_lighttpd[0.05]


#  - breakpoint at acceptTcpHandler
#  - policy socket_rw_oc
#  - batching 8192
data["redis"] = {}
data["redis"]     ["native"] = results_redis_native
data["redis"]         ["0%"] = results_redis[0]
data["redis"]       ["0.1%"] = results_redis[0.001]
data["redis"]       ["0.5%"] = results_redis[0.005]
data["redis"]         ["1%"] = results_redis[0.01]
data["redis"]         ["5%"] = (0,)

# For "theoretical maximum" bars
def n_successful_requests(n_requests, n_syscalls_per_req, syscall_failure_prob):
    syscall_success_prob = 1.0 - syscall_failure_prob
    return n_requests * ((syscall_success_prob)**n_syscalls_per_req)
max_bars = {}
#nginx_syscalls_per_req = 9
#max_bars["nginx"] = {}
#max_bars["nginx"]["native"] = mean(data["nginx"]["native"])
#max_bars["nginx"]    ["0%"] = max_bars["nginx"]["native"]
#max_bars["nginx"]   [".1%"] = n_successful_requests(max_bars["nginx"]["native"], nginx_syscalls_per_req, 0.001)
#max_bars["nginx"]   [".5%"] = n_successful_requests(max_bars["nginx"]["native"], nginx_syscalls_per_req, 0.005)
#max_bars["nginx"]    ["1%"] = n_successful_requests(max_bars["nginx"]["native"], nginx_syscalls_per_req, 0.01)
#max_bars["nginx"]    ["5%"] = n_successful_requests(max_bars["nginx"]["native"], nginx_syscalls_per_req, 0.05)
#lighttpd_syscalls_per_req = 12
#max_bars["lighttpd"] = {}
#max_bars["lighttpd"]["native"] = mean(data["lighttpd"]["native"])
#max_bars["lighttpd"]    ["0%"] = max_bars["lighttpd"]["native"]
#max_bars["lighttpd"]   [".1%"] = n_successful_requests(max_bars["lighttpd"]["native"], lighttpd_syscalls_per_req, 0.001)
#max_bars["lighttpd"]   [".5%"] = n_successful_requests(max_bars["lighttpd"]["native"], lighttpd_syscalls_per_req, 0.005)
#max_bars["lighttpd"]    ["1%"] = n_successful_requests(max_bars["lighttpd"]["native"], lighttpd_syscalls_per_req, 0.01)
#max_bars["lighttpd"]    ["5%"] = n_successful_requests(max_bars["lighttpd"]["native"], lighttpd_syscalls_per_req, 0.05)

# For "theoretical maximum" bars
def n_successful_requests(n_requests, n_syscalls_per_req, syscall_failure_prob):
    syscall_success_prob = 1.0 - syscall_failure_prob
    return n_requests * ((syscall_success_prob)**n_syscalls_per_req)
max_bars = {}
#nginx_syscalls_per_req = 9
#max_bars["nginx"] = {}
#max_bars["nginx"]["native"] = mean(data["nginx"]["native"])
#max_bars["nginx"]    ["0%"] = max_bars["nginx"]["native"]
#max_bars["nginx"]   [".1%"] = n_successful_requests(max_bars["nginx"]["native"], nginx_syscalls_per_req, 0.001)
#max_bars["nginx"]   [".5%"] = n_successful_requests(max_bars["nginx"]["native"], nginx_syscalls_per_req, 0.005)
#max_bars["nginx"]    ["1%"] = n_successful_requests(max_bars["nginx"]["native"], nginx_syscalls_per_req, 0.01)
#max_bars["nginx"]    ["5%"] = n_successful_requests(max_bars["nginx"]["native"], nginx_syscalls_per_req, 0.05)
#lighttpd_syscalls_per_req = 12
#max_bars["lighttpd"] = {}
#max_bars["lighttpd"]["native"] = mean(data["lighttpd"]["native"])
#max_bars["lighttpd"]    ["0%"] = max_bars["lighttpd"]["native"]
#max_bars["lighttpd"]   [".1%"] = n_successful_requests(max_bars["lighttpd"]["native"], lighttpd_syscalls_per_req, 0.001)
#max_bars["lighttpd"]   [".5%"] = n_successful_requests(max_bars["lighttpd"]["native"], lighttpd_syscalls_per_req, 0.005)
#max_bars["lighttpd"]    ["1%"] = n_successful_requests(max_bars["lighttpd"]["native"], lighttpd_syscalls_per_req, 0.01)
#max_bars["lighttpd"]    ["5%"] = n_successful_requests(max_bars["lighttpd"]["native"], lighttpd_syscalls_per_req, 0.05)


# ##########################################################################
# Plotting
# ##########################################################################

groups   = [#"native", 
            "0%", "0.1%", "0.5%", "1%", "5%"]
x_labels = ["lighttpd", "nginx", "redis"]

# Turn into relative numbers
relative = True
bar_label_fmt = "{:.0f}"
if relative:
    bar_label_fmt = "{:.2f}×"
    for x_label in x_labels:
        baseline = mean(data[x_label]["native"])
        for group in groups:
            data[x_label][group] = np.array(data[x_label][group]) / baseline
            if x_label in max_bars and group in max_bars[x_label]:
                max_bars[x_label][group] /= baseline


print("Max stddev: {:02f}%\n".format(max(max(stddev_perc(data[x][failure_prob])
                                             for failure_prob in groups) 
                                         for x in x_labels)))

fig, ax, colors = styling.setup()
# a gradual color scale makes more sense for error rate
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
    xs      = [x + width*i for x, y in zip(x_coords, y_maxs)]
    # max bars
    #max_ys = [max_bars[x][group] 
    #          if x in max_bars and group in max_bars[x] else 0 
    #          for x in x_labels]
    #ax.bar(xs, max_ys, width, color=(0,0,0,0.5))
    # invisible bar to place a bar label at the max
    p = ax.bar(xs, y_maxs, width, color=(0,0,0,0))
    ax.bar_label(p, rotation='vertical', padding=3,
                 labels=[bar_label_fmt.format(y) if y > 0 else "" 
                         for y in y_means],
                 **styling.bar_label_styles)
    ax.bar(xs, y_means, width, label=group, color=colors[i])
    ax.boxplot(ys, positions=xs, widths=[.8*width]*len(xs), 
               **styling.boxplot_styles)

ax.set_xticks(x_coords + 0.5*(len(groups)-1)*width, x_labels)

# Add some text for labels, title and custom x-axis tick labels, etc.
legend_style = styling.legend
legend_style['loc'] = 'upper left'
legend_style['bbox_to_anchor'] = (0.7, 1)
ax.legend(title="Divergence Rate", ncols=2, **styling.legend)

ax.set_title("Performance Amid Divergences", **styling.titlefont)
ax.set_xlim([0-2*width, x_coords[-1]+len(groups)*width+2*width])
ax.tick_params(axis='x', which='both', bottom=False)
if not relative:
    ax.set_ylabel("× 1000 Requests per Second")
    yticks = list(range(2000, 30000+1, 4000))
    ytick_labels = ['{:.0f}'.format(y/1000) for y in yticks]
    ax.set_ylim([0,yticks[-1]])
else:
    ax.set_ylabel("Relative Throughput")
    ymax = 0.9
    yticks = np.linspace(0, ymax, 4) 
    ytick_labels = ['{:.1f}'.format(y) for y in yticks]
    ax.set_ylim([0, ymax])
ax.set_yticks(yticks, labels=ytick_labels)

sns.despine()
plt.tight_layout()
fig.savefig('figure_5.pdf')
# plt.show()
