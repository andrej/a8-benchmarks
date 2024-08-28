import sys
from remote_run import *

slower_variant_addr = variant_0_addr
slower_variant_id = 0
sudo = False

benchmarks = ["getcwd", "read", "read_local", "sched_yield"]
setup_cmd = "cd ~/monmod/benchmarks/microbenchmarks/"
if not sudo:
    our_cmd_template = f"'{setup_cmd}; ~/monmod/scripts/monmod_run.sh {{1}} ~/{temp_config_name} ./build/{{0}}'"
else:
    our_cmd_template = f"'{setup_cmd}; sudo -S ~/monmod/scripts/monmod_run.sh {{1}} ~/{temp_config_name} ./build/{{0}}'"
kill_cmd = "'killall -9 read read_local getcwd sched_yield'"
config_template_single = f"""
policy = "%policy%";

restore_probability = 0;
inject_fault_probability = 0;

leader_id = {slower_variant_id};
variants = (
	{{
		id = {slower_variant_id};
		address = "%variant_{slower_variant_id}_ip%";
		port = 7773;
	}}
);
"""

config_template_full = f"""
policy = "%policy%";

restore_probability = 0;
inject_fault_probability = 0;

leader_id = {slower_variant_id};
variants = (
	{{
		id = 0;
		address = "%variant_0_ip%";
		port = 7773;
	}},
	{{
		id = 1;
		address = "%variant_1_ip%";
		port = 7774;
	}}
);
"""

def bench_func(benchmarks, results_log):
    bench_processing(benchmarks, results_log)
    bench_full(benchmarks, results_log)
    bench_no_cc([], results_log)

# To get processing number, we run full system with cross-checking, but only
# on one node (the slower one)
def bench_processing(benchmarks, results_log):
    for b in benchmarks:
        results_log.write(f"results_{b}_single = (");
        results_log.flush()
        create_config({
            "policy" : "full",
            "variant_0_ip" : variant_0_ip,
            "variant_1_ip" : variant_1_ip,
        }, config_template_single)
        rsync_config(slower_variant_addr, user)
        for _ in range(repetitions):
            run_safely(kill_cmd, sudo=True, user=user, addr=slower_variant_addr, ignore_nz=True, shell=True)
            cmd = our_cmd_template
            cmd = cmd.format(b, slower_variant_id)
            run_safely(cmd, user=user, addr=slower_variant_addr, timeout=60, needs_pw=True, shell=True)
            p = run_safely(f"'tail -n1 ~/monmod/benchmarks/microbenchmarks/monmod_{slower_variant_id}_0.log'",
                           user=user,
                           addr=slower_variant_addr,
                           stdout=subprocess.PIPE, needs_pw=True, timeout=30,
                           shell=True)
            result = read_out(p.stdout)
            print(result)
            match = re.search(r"Terminated after (\d+.\d+)",  result)
            if not match:
                raise RuntimeError(result)
            results_log.write(f"{match.group(1)}, ")
            del p
        results_log.write(")\n")
        results_log.flush()

# To get cross checking numbers, run the full thing. This will include the
# replication cost for read (device), so we have another benchmark to run
# just that one without cross-checking to isolate cross-checking cost there
def bench_full(benchmarks, results_log):
    for b in benchmarks:
        results_log.write(f"results_{b}_full = (");
        results_log.flush()
        create_config({
            "policy" : "full",
            "variant_0_ip" : variant_0_ip,
            "variant_1_ip" : variant_1_ip,
        }, config_template_full)
        rsync_config(variant_0_addr, user)
        rsync_config(variant_1_addr, user)
        for _ in range(repetitions):
            run_safely(kill_cmd, sudo=True, user=user, addr=variant_0_addr, ignore_nz=True, shell=True)
            run_safely(kill_cmd, sudo=True, user=user, addr=variant_1_addr, ignore_nz=True, shell=True)
            cmd = our_cmd_template
            cmd_0 = cmd.format(b, 0)
            cmd_1 = cmd.format(b, 1)
            p0 = run_safely(cmd_0, user=user, addr=variant_0_addr, timeout=60, needs_pw=True, dont_wait=True, shell=True)
            time.sleep(4)  # give leader time to start so follower can connect
            p1 = run_safely(cmd_1, user=user, addr=variant_1_addr, timeout=60, needs_pw=True, dont_wait=True, shell=True)
            p0.wait()
            p = run_safely(f"'tail -n1 ~/monmod/benchmarks/microbenchmarks/monmod_{slower_variant_id}_0.log'",
                           user=user,
                           addr=slower_variant_addr,
                           stdout=subprocess.PIPE, needs_pw=True, timeout=30, shell=True)
            result = read_out(p.stdout)
            print(result)
            match = re.search(r"Terminated after (\d+.\d+)",  result)
            if not match:
                raise RuntimeError(result)
            results_log.write(f"{match.group(1)}, ")
            del p0
            del p1
            del p
        results_log.write(")\n")
        results_log.flush()

# Isolate replication overhead by not cross-checking read (device)
def bench_no_cc(benchmarks, results_log):
    b = "read"
    results_log.write(f"results_{b}_no_cc = (");
    results_log.flush()
    create_config({
        "policy" : "socket_rw_oc",
        "variant_0_ip" : variant_0_ip,
        "variant_1_ip" : variant_1_ip,
    }, config_template_full)
    rsync_config(variant_0_addr, user)
    rsync_config(variant_1_addr, user)
    for _ in range(repetitions):
        run_safely(kill_cmd, sudo=True, user=user, addr=variant_0_addr, ignore_nz=True, shell=True)
        run_safely(kill_cmd, sudo=True, user=user, addr=variant_1_addr, ignore_nz=True, shell=True)
        cmd = our_cmd_template
        cmd_0 = cmd.format(b, 0)
        cmd_1 = cmd.format(b, 1)
        p0 = run_safely(cmd_0, user=user, addr=variant_0_addr, timeout=60, needs_pw=True, dont_wait=True, shell=True)
        time.sleep(4)  # give leader time to start so follower can connect
        p1 = run_safely(cmd_1, user=user, addr=variant_1_addr, timeout=60, needs_pw=True, dont_wait=True, shell=True)
        p0.wait()
        p = run_safely(f"'tail -n1 ~/monmod/benchmarks/microbenchmarks/monmod_{slower_variant_id}_0.log'",
                        user=user,
                        addr=slower_variant_addr,
                        stdout=subprocess.PIPE, needs_pw=True, timeout=30,
                        shell=True)
        result = read_out(p.stdout)
        print(result)
        match = re.search(r"Terminated after (\d+.\d+)",  result)
        if not match:
            raise RuntimeError(result)
        results_log.write(f"{match.group(1)}, ")
        del p0
        del p1
        del p
    results_log.write(")\n")
    results_log.flush()

main(benchmarks, f"figure_9", bench_func)
