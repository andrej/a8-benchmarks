#!/usr/bin/env python3

from remote_run import main, OrderedDict

nginx = OrderedDict({
    "var_name_func": [lambda e, c: f"results_nginx[{c["batch_size"]}]"],
	"target" :               ["nginx"],
	"leader_id" :            [0],
	"fault_prob" :           [0],
	"breakpoint" :           ["ngx_close_connection"],
	"breakpoint_interval":   [1],
	"policy" :               ["socket_rw_oc"],
	"batch_size" :           [0, 512, 1024, 2048, 4096, 8192],
	"restore_prob" :         [0]
})

lighttpd = OrderedDict({
    "var_name_func": [lambda e, c: f"results_lighttpd[{c["batch_size"]}]"],
	"target" :               ["lighttpd"],
	"leader_id" :            [0],
	"fault_prob" :           [0],
	"breakpoint" :           ["connection_close"],
	"breakpoint_interval":   [1],
	"policy" :               ["socket_rw_oc"],
	"batch_size" :           [0, 512, 1024, 2048, 4096, 8192],
	"restore_prob" :         [0]
})

redis = OrderedDict({
    "var_name_func": [lambda e, c: f"results_redis[{c["batch_size"]}]"],
	"target" :               ["redis"],
	"leader_id" :            [0],
	"fault_prob" :           [0],
	"breakpoint" :           ["aeMain"],
	"breakpoint_interval" :  [1],
	"policy" :               ["socket_rw_oc"],
	"batch_size" :           [0, 512, 1024, 2048, 4096, 8192],
	"restore_prob" :         [0]
})

experiments = [
	nginx,
	lighttpd, 
	redis, 
]

results_log_prefix = """
results_nginx = {}
results_lighttpd = {}
results_redis = {}
"""

main(experiments, "figure_7", results_log_prefix=results_log_prefix)
