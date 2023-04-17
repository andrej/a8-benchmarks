#!/usr/bin/env python3

import sys
import os.path
import subprocess
import getpass
import time
import re
from collections import OrderedDict


# Variant Configuration File
variant_0_addr = "eiger.ics.uci.edu"
variant_1_addr = "blackforest.ics.uci.edu"
client_addr = "dreamer.ics.uci.edu"

# List all values you want to test in a list for each key. All combinations
# will be benchmarked.

experiment = OrderedDict({
	"leader_id" :            [0],
	"fault_prob" :           [0],
	"variant_0_breakpoint" : [True],
	"variant_1_breakpoint" : [True],
	"policy" :               ["socket_rw_oc", "full"],
	"batch_size" :           [8192],
	"restore_prob" :         [0, 0.001, 0.005, 0.01, 0.05],
	"usleep" :               [0],
	"target" :               ["nginx"], #, "lighttpd"],
})

experiments = [experiment]

target_cmds = {
	"lighttpd" : "~/monmod-benchmarks/lighttpd/install/sbin/lighttpd -D -f ~/monmod-benchmarks/lighttpd/config/static_4KB.conf",
	"nginx" : "~/monmod-benchmarks/nginx/install/sbin/nginx -p ~/monmod-benchmarks/nginx/ -c config/nginx.conf"
}

repetitions = 5

# Commands / config
prev_kill_cmd = 'killall -9 read sched_yield getcwd lighttpd nginx monmod_run.sh sudo'
kill_cmd = 'sh -c "for pid in $(pidof monmod_run.sh); do pkill -9 -g $pid; done"'
sync_cmd = 'rsync {temp_conf_local} {user}@{addr}:~/{temp_conf_name}'
variant_cmd = '~/monmod/scripts/monmod_run.sh {variant_id} ~/{temp_config_name} {target}'
variant_cmd_sudo = False
client_cmd = '~/DMon/benchmarks/wrk/wrk -d10s -t1 -c10 http://128.195.4.134:3000'

template_path = os.path.join(os.path.dirname(__file__), "configs", "template.ini")
temp_config_dir = os.path.join(os.path.dirname(__file__), "configs")
temp_config_name = "temp_config.ini"


################################################################################

user = "andre"
password = None
stdout_log = None
stderr_log = None
results_log = None
config_template_str = ""


class Failed_DoNextIteration(BaseException):
	pass


def main():
	global config_template_str, password, stdout_log, stderr_log, results_log
	try:
		stdout_log = open("stdout.log", "w")
		stderr_log = open("stderr.log", "w")
		results_log = open("results.log", "w")
		password = getpass.getpass()
		with open(template_path) as f:
			config_template_str = f.read()
		iterate()
	finally:
		if stdout_log: stdout_log.close()
		if stderr_log: stderr_log.close()


def iterate():
	for i, experiment in enumerate(experiments):
		write_result_ln("# Experiment {}\n".format(i))
		write_header(experiment)
		for conf in iterate_configs({}, experiment):
			write_conf_header(experiment, conf)
			done = one_benchmark(conf)
			if done:
				return
		write_result_ln("")


def one_benchmark(conf):
	variant_0 = None
	variant_1 = None
	create_config(conf)
	target = conf["target"]
	target_cmd = target_cmds[target]
	try:
		results = []
		for _ in range(repetitions):
			variant_0 = start_variant(variant_0_addr, user, target_cmd, 0)
			time.sleep(4)
			variant_1 = start_variant(variant_1_addr, user, target_cmd, 1)
			time.sleep(1)
			result = run_client(client_addr, user)
			stop_variant(variant_0_addr, user, variant_0)
			stop_variant(variant_1_addr, user, variant_1)
			results.append(result)
			write_result("{:7},  ".format(str(result)))
		results = list(map(float, results))
		results.sort()
		median = results[len(results)//2]
		write_result("Median: {:10}\n".format(median))
	except KeyboardInterrupt:
		return True
	except BaseException as e:
		write_result_ln("Error: {}".format(e))
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


def write_result(w):
	sys.stdout.write(w)
	results_log.write(w)
	results_log.flush()
	

def write_result_ln(w):
	print(w)
	results_log.write(w+"\n")
	results_log.flush()


def get_line_fmt(experiment):
	return ", ".join("{:%d}" % max(map(lambda x: len(str(x)), [k] + v)) for k, v in experiment.items())

def write_header(experiment):
	line_fmt = get_line_fmt(experiment)
	write_result_ln(line_fmt.format(*experiment.keys()))


def write_conf_header(experiment, conf):
	line_fmt = get_line_fmt(experiment)
	write_result_ln(line_fmt.format(*[conf[k] for k in experiment.keys()]))


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
			for conf in iterate_configs(conf, add_vars):
				yield conf


def create_config(conf):
	conf_str = config_template_str
	for k, v in conf.items():
		v = get_config_value(conf, k, v)
		conf_str = conf_str.replace('%'+k+'%', str(v))
	tmp_conf_local = os.path.join(temp_config_dir, temp_config_name)
	with open(tmp_conf_local, "w") as f:
		f.write(conf_str)


def get_config_value(conf, k, v):
	if k not in {'variant_0_breakpoint', 'variant_1_breakpoint'}:
		return v
	
	if v == False:
		return ''
	
	template = ('{{ interval = {interval};\n'
	            '  pc = {pc};\n'
		    '  instr_len = {instr_len};\n'
		    '}} \n')
	target = conf["target"]
	interval = (conf["breakpoint_interval"] 
	            if "breakpoint_interval" in conf else 1)
	
	# Below breakpoints only apply if targets are aarch64 on variant 0,
	# and x86 on variant 1. Otherwise update breakpoint addresses below.
	assert variant_0_addr == "eiger.ics.uci.edu"
	assert variant_1_addr == "blackforest.ics.uci.edu"

	if k == "variant_0_breakpoint":
		instr_len = 4
		if target == 'read': # read() in microbenchmarks/read:
			pc = '0x400664'
		elif target == 'lighttpd': # connection_accept() in lighttpd:
			pc = '0x40de50'
		elif target == 'nginx': # ngx_event_accept() in nginx:
			pc = '0x42f8d8'
		else:
			raise KeyError("target = {}".format(target))
	elif k == "variant_1_breakpoint":
		if target == 'read': # read() in microbenchmarks/read:
			pc = '0x4005b2'
			instr_len = 5
		elif target == 'lighttpd': # connection_accept() in lighttpd:
			pc = '0x40e0e0'
			instr_len = 1
		elif target == 'nginx': # ngx_event_accept() in nginx:
			pc = '0x42dff7'
			instr_len = 2
		else:
			raise KeyError("target = {}".format(target))
	else:
		raise RuntimeError()
	
	return template.format(interval=interval, pc=pc, instr_len=instr_len)


def run_safely(cmd, ignore_nz=False, sudo=False, dont_wait=False, timeout=10,
               user=None, addr=None, stdout=None, needs_pw=False, **kwargs):
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
	print("> " + cmd)
	p = None
	try:
		p = subprocess.Popen(cmd.split() if not shell else cmd, 
				     stdin=subprocess.PIPE,
				     stdout=stdout,
				     stderr=stderr_log,
				     **kwargs)
		if sudo or needs_pw:
			p.stdin.write((password + "\n").encode("ascii"))
			p.stdin.flush()
		if not dont_wait:
			p.wait(timeout=timeout)
			if not ignore_nz and p.returncode != 0:
				print("Returned non-zero {}.".format(p.returncode))
				raise Failed_DoNextIteration()
	except subprocess.TimeoutExpired:
		print("Timeout expired.")
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
		

def start_variant(addr, user, target, variant_id):
	# First, send over config file.
	temp_conf_local = os.path.join(temp_config_dir, temp_config_name)
	rsync_cmd = sync_cmd.format(temp_conf_local=temp_conf_local,
		                    addr=addr, user=user,
		                    temp_conf_name=temp_config_name)
	run_safely(rsync_cmd)

	# Kill any previous variants
	run_safely(prev_kill_cmd, user=user, addr=addr, ignore_nz=True, sudo=True)

	# Start variant
	cmd = (variant_cmd.format(variant_id=variant_id,
		                  temp_config_name=temp_config_name,
		                  target=target))
	p = run_safely(cmd, sudo=variant_cmd_sudo, needs_pw=True, user=user, addr=addr, dont_wait=True)
	return p


def stop_variant(addr, user, p):
	run_safely(kill_cmd, addr=addr, user=user, ignore_nz=True)


def run_client(addr, user):
	cmd = client_cmd
	p = run_safely(cmd, addr=addr, user=user, stdout=subprocess.PIPE,
	               timeout=15)
	results = p.stdout.read().decode("ascii", errors="ignore")
	match = re.search(r"Requests/sec:\s*(\d+\.\d+)", results)
	if not match:
		raise RuntimeError(results)
	return match.group(1)
	

if __name__ == "__main__":
	main()