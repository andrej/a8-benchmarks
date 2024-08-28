import sys
from remote_run import *

assert(len(sys.argv) == 2)
i = int(sys.argv[1])

variant_addr = variant_0_addr  # OR variant_1_addr, whichever is slower

benchmarks = ["getcwd", "read", "read_local", "sched_yield"]
setup_cmd = "cd ~/monmod/benchmarks/microbenchmarks/"
native_cmd_template = f"{setup_cmd}; /usr/bin/time -f%e ./build/{{0}}"
our_cmd_template = f"{setup_cmd}; DOTIME=1 ~/monmod/scripts/monmod_run.sh 0 ~/{temp_config_name} ./build/{{0}}"
config_template = """
policy = "%policy%";

restore_probability = 0;
inject_fault_probability = 0;

leader_id = 0;
variants = (
	{
		id = 0;
		address = "127.0.0.1";
		port = 7773;
	}
);

"""
def bench_func(benchmarks, results_log):
    for b in benchmarks:
        results_log.write(f"results_{i}_{b} = (");
        results_log.flush()
        for _ in range(repetitions):
            if i > 0:
                create_config({
                    "policy" : "full",
                }, config_template)
                rsync_config(variant_addr, user)
            cmd = native_cmd_template if i == 0 else our_cmd_template
            cmd = cmd.format(b)

            p = run_safely(cmd, user=user, addr=variant_addr, stderr=subprocess.PIPE, timeout=60, needs_pw=i>0)
            result = read_out(p.stderr)
            print(result)
            match = re.search(r"(\d+.\d+)",  result)
            if not match:
                raise RuntimeError(result)
            results_log.write(f"{match.group(1)}, ")
        results_log.write(")\n");
        results_log.flush();
            

main(benchmarks, f"figure_8_{sys.argv[1]}", bench_func)
