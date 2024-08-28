import sys
from remote_run import *

slower_variant_addr = variant_0_addr
slower_variant_id = 0
sudo = False

benchmarks = [0, 512, 1024, 2048, 4096, 8192, 16384]
setup_cmd = "cd ~/monmod/benchmarks/microbenchmarks/"
if not sudo:
    our_cmd_template = f"'{setup_cmd}; ~/monmod/scripts/monmod_run.sh {{0}} ~/{temp_config_name} ./build/read'"
else:
    our_cmd_template = f"'{setup_cmd}; sudo -S ~/monmod/scripts/monmod_run.sh {{0}} ~/{temp_config_name} ./build/read'"
kill_cmd = "'killall -9 read read_local getcwd sched_yield'"
config_template = f"""
policy = "socket_rw_oc";

replication_batch_size = %batch_size%;
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


# To get cross checking numbers, run the full thing. This will include the
# replication cost for read (device), so we have another benchmark to run
# just that one without cross-checking to isolate cross-checking cost there
def bench_func(benchmarks, results_log):
    for batch_size in benchmarks:
        results_log.write(f"results_{batch_size} = (");
        results_log.flush()
        create_config({
            "batch_size" : batch_size,
            "variant_0_ip" : variant_0_ip,
            "variant_1_ip" : variant_1_ip,
        }, config_template)
        rsync_config(variant_0_addr, user)
        rsync_config(variant_1_addr, user)
        for _ in range(repetitions):
            run_safely(kill_cmd, sudo=True, user=user, addr=variant_0_addr, ignore_nz=True, shell=True)
            if variant_0_addr != variant_1_addr:
                run_safely(kill_cmd, sudo=True, user=user, addr=variant_1_addr, ignore_nz=True, shell=True)
            cmd = our_cmd_template
            cmd_0 = cmd.format(0)
            cmd_1 = cmd.format(1)
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

main(benchmarks, f"figure_10", bench_func)
