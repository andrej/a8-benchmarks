#!/usr/bin/env python3

import sys
import os.path
import subprocess
import getpass
import time
import re
from collections import OrderedDict
from textwrap import dedent


# Variant Configuration File
variant_0_addr = "eiger.ics.uci.edu"
variant_0_ip = "10.0.0.15"
variant_0_arch = "aarch64"
variant_1_addr = "blackforest.ics.uci.edu"
variant_1_ip = "10.0.0.30"
variant_1_arch = "x86_64"
client_addr = "dreamer.ics.uci.edu"

repetitions = 1


# List all values you want to test in a list for each key. All combinations
# will be benchmarked.

target_cmds = {
	"lighttpd" : "~/monmod/benchmarks/lighttpd/install/sbin/lighttpd -D "
	             "-f ~/monmod/benchmarks/lighttpd/config/static_4KB.conf",
	"nginx"    : "~/monmod/benchmarks/nginx/install/sbin/nginx "
	             "-p ~/monmod/benchmarks/nginx/ -c config/nginx.conf",
	"redis"    : "~/monmod/benchmarks/redis/install/bin/redis-server "
	             "~/monmod/benchmarks/redis/config/redis.conf"
}

client_cmds = {
	"lighttpd" : "~/monmod/benchmarks/wrk/wrk -d10s -t10 -c10 --timeout 10s "
	             "http://128.195.4.134:3000",
	"nginx"    : "~/monmod/benchmarks/wrk/wrk -d10s -t10 -c10 --timeout 10s "
	             "http://128.195.4.134:3000",
	"redis"    : "~/monmod/benchmarks/redis/install/bin/redis-benchmark -q "
	             "-n 10000 -h 128.195.4.134 -p 6379 -c 10 -t PING_INLINE",
	#"redis"    : "~/monmod/benchmarks/redis/install/bin/redis-benchmark -q "
	#             "-n 1000 -h 128.195.4.134 -p 6379 -c 1 -t PING_INLINE",
}

client_kill_cmd = ("killall -9 wrk redis-benchmark", True, True)

results_regexes = {
	"lighttpd": r"Requests/sec:\s*(\d+\.\d+)",
	"nginx":    r"Requests/sec:\s*(\d+\.\d+)",
	"redis":    r"PING_INLINE:\s*(\d+\.\d+)",
}

other_template_keys = {
	"variant_0_breakpoint" : "breakpoint", 
	"variant_1_breakpoint" : "breakpoint"
}

# For each architecture, the breakpoint definition is a tuple 
# (symbol, offset, len)
breakpoints = {
	"lighttpd" : {
		# most functions in lighttpd are static, thus their symbol not available at run time.
		# therefore we express those addresses as offsets from main (Which is available)
		"connection_close":             { "aarch64" : ('main', 0x136A8, 4),
		                                  "x86_64"  : ('main', 0x15685, 1)},
		"fdevent_linux_sysepoll_poll":  { "aarch64" : ('main', 0x16958, 4),
		                                  "x86_64"  : ('main', 0x180F5 + 4, 2)},
	},
	"nginx" : {
		"ngx_event_accept":             { "aarch64" : ('ngx_event_accept', 0, 4),
		                                   "x86_64" : ('ngx_event_accept', 4, 2)},
		"ngx_close_connection":         { "aarch64" : ('ngx_close_connection', 0, 4),
		                                  "x86_64"  : ('ngx_close_connection', 4, 2)},
		"ngx_epoll_process_events":     { "aarch64" : ('ngx_epoll_process_events', 0, 4),
		                                  "x86_64"  : ('ngx_epoll_process_events', 4, 2)},
		"ngx_epoll_init":               { "aarch64" : ('ngx_epoll_init', 0, 4),
		                                  "x86_64"  : ('ngx_epoll_init', 4, 2)},
	},
	"redis" : {
		"acceptTcpHandler":             { "aarch64" : ('acceptTcpHandler', 0, 4),
		                                  "x86_64"  : ('acceptTcpHandler', 4, 2)},
		"aeMain":                       { "aarch64" : ('aeMain', 0, 4),
								          "x86_64"  : ('aeMain', 4, 1)}
	}
}

# Commands / config
# Command, sudo, ignore_nz
variant_setup_cmds = [
	("~/monmod/scripts/stop_monmod.sh", True, True),
]

variant_after_start_cmds = [
	#("cset shield --cpu 10-12", True, True),
	#("cset shield --shield --pid $(pidof -s vma-server),$(pidof -s lighttpd),"
	# "$(pidof -s nginx),$(pidof -s redis-server)", True, True),
]

kill_cmd = '~/monmod/scripts/stop_monmod.sh'
sync_cmd = 'rsync {temp_conf_local} {user}@{addr}:~/{temp_conf_name}'
variant_cmd = '~/monmod/scripts/monmod_run.sh {variant_id} ~/{temp_config_name} {target}'
variant_cmd_sudo = False

template_path = os.path.join(os.path.dirname(__file__), "config_template.ini")
temp_config_dir = os.path.dirname(__file__)
temp_config_name = "config_temp.ini"


################################################################################

user = "andre"
password = None
stdout_log = None
stderr_log = None
results_log = None
config_template_str = ""


class Failed_DoNextIteration(BaseException):
	pass


def main(experiments, file_prefix, bench_func=None, results_log_prefix=""):
	global config_template_str, password, stdout_log, stderr_log, results_log
	if bench_func is None:
		bench_func = iterate
	try:
		stdout_log = open(f"{file_prefix}_stdout.log", "w")
		stderr_log = open(f"{file_prefix}_stderr.log", "w")
		results_log = open(f"{file_prefix}_results.py", "w")
		password = getpass.getpass()
		results_log.write(results_log_prefix)
		with open(template_path) as f:
			config_template_str = f.read()
		bench_func(experiments, results_log)
	finally:
		if stdout_log: stdout_log.close()
		if stderr_log: stderr_log.close()


def iterate(experiments, results_log):
	for i, experiment in enumerate(experiments):
		if "variant_0_ip" not in experiment:
			experiment["variant_0_ip"] = [variant_0_ip]
		if "variant_1_ip" not in experiment:
			experiment["variant_1_ip"] = [variant_1_ip]
		for conf in iterate_configs({}, experiment):
			results_log.write(f"{experiment["var_name_func"][0](experiment, conf)} = (")
			done = one_benchmark(conf)
			results_log.write(")\n")
			results_log.flush()
			if done:
				return


def one_benchmark(conf):
	variant_0 = None
	variant_1 = None
	create_config(conf)
	if "native" not in conf:
		rsync_config(variant_0_addr, user)
		rsync_config(variant_1_addr, user)
	target = conf["target"]
	target_cmd = target_cmds[target]
	client_cmd = client_cmds[target]
	try:
		results = []
		for _ in range(repetitions):
			if "native" not in conf:
				variant_0 = start_variant(variant_0_addr, user, target_cmd, 0)
				time.sleep(4)
				variant_1 = start_variant(variant_1_addr, user, target_cmd, 1)
				time.sleep(1)
			else:
				variant_0 = run_native(variant_0_addr, user, target_cmd)
			result = run_client(client_addr, user, client_cmd, target)
			results_log.write(f"{result},")
			results_log.flush()
			if "native" not in conf:
				stop_variant(variant_0_addr, user, variant_0)
				stop_variant(variant_1_addr, user, variant_1)
			else:
				run_safely("killall -9 redis-server lighttpd nginx", addr=variant_0_addr, user=user, sudo=True, ignore_nz=True)
			results.append(result)
	except KeyboardInterrupt:
		return True
	except BaseException as e:
		print("Error: {}".format(e))
		time.sleep(15)
		return False
	finally:
		try: 
			if variant_0: stop_variant(variant_0_addr, user, variant_0)
		except Failed_DoNextIteration: pass
		try: 
			if variant_1: stop_variant(variant_1_addr, user, variant_1)
		except Failed_DoNextIteration: pass
	return False


def iterate_configs(conf, add_vars):
	if not add_vars:
		yield conf
	else:
		k = list(add_vars.keys())[0]
		v_opts = add_vars[k]
		add_vars = add_vars.copy()
		del add_vars[k]
		for v in v_opts:
			conf[k] = v
			for c in iterate_configs(conf, add_vars):
				yield c


def create_config(conf, conf_str=None):
	if conf_str is None:
		conf_str = config_template_str
	for k, v in conf.items():
		v = get_config_value(conf, k, v)
		conf_str = conf_str.replace('%'+k+'%', str(v))
	for tk, k in other_template_keys.items():
		if k not in conf:
			continue
		v = get_config_value(conf, tk, conf[k])
		conf_str = conf_str.replace('%'+tk+'%', str(v))
	tmp_conf_local = os.path.join(temp_config_dir, temp_config_name)
	with open(tmp_conf_local, "w") as f:
		f.write(conf_str)


def get_config_value(conf, k, v):
	if k not in {'variant_0_breakpoint', 'variant_1_breakpoint'}:
		return v
	
	if not v:
		return ''
	
	arch = ""
	if k == "variant_0_breakpoint":
		arch = variant_0_arch
	else:
		arch = variant_1_arch
	
	template = dedent("""
		{{
		interval = {interval};
		symbol = "{symbol}";
		offset = {offset};
		instr_len = {instr_len};
		}}
	""")
	target = conf["target"]
	interval = (conf["breakpoint_interval"] 
	            if "breakpoint_interval" in conf else 1)
	
	# Below breakpoints only apply if targets are aarch64 on variant 0,
	# and x86 on variant 1. Otherwise update breakpoint addresses below.
	assert variant_0_addr == "eiger.ics.uci.edu"
	assert variant_1_addr == "blackforest.ics.uci.edu"

	symbol, offset, instr_len = breakpoints[target][v][arch]

	return template.format(interval=interval, symbol=symbol, offset=offset, instr_len=instr_len)


def run_safely(cmd, ignore_nz=False, sudo=False, dont_wait=False, timeout=30,
               user=None, addr=None, stdout=None, needs_pw=False, retries=2, **kwargs):
	orig_cmd = cmd
	if sudo:
		cmd = "sudo -S " + cmd;
	if addr and user:
		cmd = ('ssh {user}@{addr} {cmd}'
			.format(user=user, addr=addr, cmd=cmd))
	if not stdout:
		stdout = stdout_log
	shell = False
	if "shell" in kwargs and kwargs["shell"]:
		shell = True
	if "stderr" not in kwargs:
		kwargs["stderr"] = stderr_log
	print("> " + cmd)
	p = None
	try:
		time.sleep(1)
		p = subprocess.Popen(cmd.split() if not shell else cmd, 
				             stdin=subprocess.PIPE,
				             stdout=stdout,
				             **kwargs)
		if sudo or needs_pw:
			time.sleep(0.5)
			p.stdin.write((password + "\n").encode("ascii"))
			p.stdin.flush()
		if not dont_wait:
			p.wait(timeout=timeout)
			if not ignore_nz and p.returncode != 0:
				print("Returned non-zero {}.".format(p.returncode))
				raise Failed_DoNextIteration()
	except subprocess.TimeoutExpired:
		print(f"Timeout expired, retries={retries}.")
		if retries > 0:
			return run_safely(orig_cmd, ignore_nz, sudo, dont_wait, timeout, user, addr, stdout, needs_pw, retries-1, **kwargs)
		raise Failed_DoNextIteration()
	except KeyboardInterrupt as e:
		raise e
	except BaseException as e:
		print("Runtime error: {}".format(e))
		raise Failed_DoNextIteration()
	finally:
		if p and not dont_wait:
			p.kill()
			p.wait()
	return p
		

def rsync_config(addr, user):
	# First, send over config file.
	temp_conf_local = os.path.join(temp_config_dir, temp_config_name)
	rsync_cmd = sync_cmd.format(temp_conf_local=temp_conf_local,
		                    addr=addr, user=user,
		                    temp_conf_name=temp_config_name)
	run_safely(rsync_cmd)


def start_variant(addr, user, target, variant_id):

	# Kill any previous variants
	for variant_setup_cmd, sudo, ignore_nz in variant_setup_cmds:
		run_safely(variant_setup_cmd, user=user, addr=addr, ignore_nz=ignore_nz, 
		           sudo=sudo)
	time.sleep(1)

	# Start variant
	cmd = (variant_cmd.format(variant_id=variant_id,
		                  temp_config_name=temp_config_name,
		                  target=target))
	p = run_safely(cmd, sudo=variant_cmd_sudo, needs_pw=True, user=user, 
	               addr=addr, dont_wait=True)
	
	# After start commands
	time.sleep(1)
	for cmd, sudo, ignore_nz in variant_after_start_cmds:
		run_safely(cmd, user=user, addr=addr, ignore_nz=ignore_nz, sudo=sudo,
		           dont_wait=False)

	return p

def run_native(addr, user, target):
	# Kill any previous variants
	for variant_setup_cmd, sudo, ignore_nz in variant_setup_cmds:
		run_safely(variant_setup_cmd, user=user, addr=addr, ignore_nz=ignore_nz, 
		           sudo=sudo)
	time.sleep(1)

	# Start variant
	p = run_safely(target, sudo=False, needs_pw=False, user=user, 
	               addr=addr, dont_wait=True)
	
	return p


def stop_variant(addr, user, p):
	run_safely(kill_cmd, addr=addr, user=user, ignore_nz=True, sudo=True)


def read_out(p):
	return p.read().decode("ascii", errors="ignore")

def run_client(addr, user, client_cmd, target):
	kill_cmd, kill_sudo, kill_ignore_nz = client_kill_cmd
	run_safely(kill_cmd, addr=addr, user=user, sudo=kill_sudo, 
			   ignore_nz=kill_ignore_nz)
	p = run_safely(client_cmd, addr=addr, user=user, stdout=subprocess.PIPE,
	               timeout=20)
	results = read_out(p.stdout)
	match = re.search(results_regexes[target], results)
	if not match:
		raise RuntimeError(results)
	return match.group(1)
	