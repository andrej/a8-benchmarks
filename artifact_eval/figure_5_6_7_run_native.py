#!/usr/bin/env python3

from remote_run import main, OrderedDict

nginx = OrderedDict({
	"native" : [True],
    "var_name_func": [lambda e, c: f"results_nginx_native"],
	"target" :               ["nginx"],
	"leader_id" :            [0],
})

lighttpd = OrderedDict({
	"native" : [True],
    "var_name_func": [lambda e, c: f"results_lighttpd_native"],
	"target" :               ["lighttpd"],
	"leader_id" :            [0],
})

redis = OrderedDict({
	"native" : [True],
    "var_name_func": [lambda e, c: f"results_redis_native"],
	"target" :               ["redis"],
	"leader_id" :            [0],
})

experiments = [
	nginx,
	lighttpd, 
	redis, 
]

main(experiments, "figure_5_6_7_native") 