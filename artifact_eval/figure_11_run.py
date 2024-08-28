import sys
from remote_run import *

assert len(sys.argv) == 2
i = int(sys.argv[1])

variant_addr = variant_0_addr
sudo = False

setup_cmd = "cd ~/monmod/benchmarks/microbenchmarks/"
our_cmd_template = f"'{setup_cmd}; ~/monmod/scripts/monmod_run.sh 0 ~/{temp_config_name} ./build/read'"
kill_cmd = "'killall -9 read read_local getcwd sched_yield'"
delete_criu_images_cmd = 'rm -rf ~/monmod/benchmarks/microbenchmarks/criu_images'
kill_criu_cmd = "'killall -9 criu'"
start_criu_cmd = "'~/monmod/dependencies/criu-install/sbin/criu service --address /var/run/criu-service.socket'"

config_template = """
leader_id = 0;

policy = "full";
replication_batch_size = 0;

restore_probability = 0.00;
inject_fault_probability = 0;

variants = (
        { # eiger
                id = 0;
                address = "127.0.0.1";
                port = 7773;
                breakpoints = (
                    {
                        interval = %interval%;
                        symbol = "read";
                        instr_len = 4;
                    }
                ) 
        }
);
"""

def bench_func(benchmarks, results_log):
    if i == 0:
        bench_inner("fork", [1, 10, 100, 1000, 10000, 100000, 1000000], results_log)
    else:
        run_safely(kill_criu_cmd, sudo=True, user=user, addr=variant_addr, ignore_nz=True, shell=True)
        run_safely(start_criu_cmd, sudo=True, user=user, addr=variant_addr, ignore_nz=True, shell=True, dont_wait=True)
        time.sleep(5) # Give CRIU a chance to start before running the benchmark
        bench_inner("criu", [100, 1000, 10000, 100000, 1000000], results_log)
        run_safely(kill_criu_cmd, sudo=True, user=user, addr=variant_addr, ignore_nz=True, shell=True)

# To get processing number, we run full system with cross-checking, but only
# on one node (the slower one)
def bench_inner(b, benchmarks, results_log):
    results_log.flush()
    for interval in benchmarks:
        results_log.write(f"results_{b}_{interval} = (");
        create_config({
            "policy" : "full",
            "variant_0_ip" : variant_0_ip,
            "variant_1_ip" : variant_1_ip,
            "interval" : interval
        }, config_template)
        rsync_config(variant_addr, user)
        for _ in range(repetitions):
            run_safely(kill_cmd, sudo=True, user=user, addr=variant_addr, ignore_nz=True, shell=True)
            if b == "criu":
                run_safely(delete_criu_images_cmd, sudo=True, user=user, addr=variant_addr)
            cmd = our_cmd_template
            run_safely(cmd, user=user, addr=variant_addr, timeout=60, needs_pw=True, shell=True, ignore_nz=True)
            p = run_safely(f"'tail -n1 ~/monmod/benchmarks/microbenchmarks/monmod_0_0.log'",
                            user=user,
                            addr=variant_addr,
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
    run_safely(kill_criu_cmd, sudo=True, user=user, addr=variant_addr, ignore_nz=True, shell=True)

main([], f"figure_11_{i}", bench_func)
