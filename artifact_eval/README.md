# Artifact Evaluation Instructions

> Everything needed for artifact evaluation from the client side is located in
> the subdirectory
> `/monmod/benchmarks/artifact_eval/`.

Thank you for taking the time to evaluate our artifacts. We hope these
instructions make it as easy as possible to test the functionality of our 
system.

We have created an anonymous e-mail account to be able to assist if any 
troubleshooting is needed:

    a8-artifact-eval@outlook.com

> Note: **monmod** was the working title of the system that we refer to
  as A^8 in our paper. We will rename all occurences of "monmod" with
  A^8 before publication of the source code.

## Overview

Our system replicates program execution across a set of distributed hosts and 
monitors their behavior. It does so through two components that are present
on each host:

  - a kernel module, found in `/kernel_module/`
  - a preloadable shared library, found in `/library/`.

Both of those components need to be built individually. Different benchmarks
in the evaluation section of our paper use different build settings for these
components to demonstrate the tradeoffs of design decisions. Please take note
of the correct build flags in the figure-specific instructions.

All our benchmarks use two constituent variants, that is two distributed hosts.
A third machine is used as the 'client' to benchmark the running applications.

**The overall performance of our distributed system depends largely on the
latency and throughput of the link connecting constituent machines.** Please see
the section "hardware" below on details on the hardware we used for our
evaluation. We do not anticipate that our reviewers will have access to the
exact same hardware, especially the sophisticated network card we used, so some 
variability is to be expected. However, evaluators should be able to measure
an upper and a lower bound on performance, within which our measurements should
fall:

 - **Lower bound:** Instantiate both variants on the same machine, on different
   ports. This will underapproximate the cost of our system, as communication
   overheads will be much lower when both variants are located on the same
   machine. Our overheads should generally be larger than this.
 - **Upper bound:** Instantiate variants across separate machines, connected
   through a regular ethernet interface. Since we used a high-performance 
   network card with an extremely short InfiniBand-link between the two 
   machines, almost any other two connected hosts will likely experience higher
   network overheads. Thus, if you benchmark our system across two hosts 
   connected through 1Gbps ethernet, you will likely see higher overheads than
   in our paper.


## Preparing all three hosts

1. Instantiate three virtual machines running Ubuntu 22.04. We will refer to 
   those three machines as `vm1`, `vm2` and `vm3`. `vm1` and `vm2` will run the 
   variants; `vm3` will be used as a client for benchmarking. Ideally, one of 
   the machines should be an aarch64 machine, however it also works if all
   machines are of the same architecture. We made `vm1` the "odd one out" in our 
   tests. The others are `x86_64` machines in our tests.
2. On x86_64 machines, update the kernel. We require `v5.15.154` or possibly 
   newer (though newer kernels are untested).
   ```
   sudo add-apt-repository ppa:cappelikan/ppa
   sudo apt update
   sudo apt install mainline
   mainline check
   sudo mainline install 5.15.154
   sudo shutdown --reboot now
   ```
3. From your local machine (likely the machine you are reading this from), set
   up SSH keys to allow password-free authentication to all of `vm1`, `vm2` and
   `vm3`. **Important:** Our benchmarking script requires that SSH keys are set
   up. Password-based authentication will not work.
   - Please see [here on how to set up SSH keys](https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server).
   - Test that you can log into all VMs without passwords: `ssh user@vm1` should
     open a command prompt on that machine without any password prompt.
4. On all machines, `vm1`, `vm2` and `vm3`:
   1. Ensure your user has sudo privileges, i.e. is part of the group 
       `sudoers`. **Ensure that the superuser password on all VMs is the same
       as our `remote_run.py` script for artifact evaluation assumes this.** 
       Also ensure that the user name on each machine is the same. If not,
       set up a new account with `useradd` with the same name and password
       on all machines.
   2. Take note of the IP addresses of the public link of the machines:
       `ip addr`.
5. On `vm1` and `vm2`: (Identical)
   1. Copy the entirety of our artifact to both machines into the home directory
      `~`. All scripts expect things to be installed in the home directory.
   2. Run the script `./bootstrap.sh` inside `~/monmod`. This will install 
       dependencies.
   3. Run the script `benchmarks/bootstrap.sh` from within the 
      `~/monmod/benchmarks` directory. This will fetch and compile
      our benchmarks: `nginx`, `lighttpd`, `redis` and the microbenchmarks. 
      This may take a while.
6. On `vm3`:
   1. Copy the subdirectory `benchmarks` onto the machine.
   2. Run the script `./benchmarks/bootstrap.sh`. This will fetch and compile
      the `wrk` and `redis-benchmark` utilities used for client-side 
      benchmarking, along with the other benchmarks (which won't be needed on 
      this machine).
7. Locally, on your own machine, ensure you have all required Python packages
   to plot our figures and remotely run our system. The requirements are listed
   in `artifact_eval/requirements.txt`. You can install all of them using
   `pip install -r artifact_eval/requirements.txt`, or create a virtual
   environment.
   
   ```
   cd benchmarks/artifact_eval
   python3 -m venv venv
   source venv/bin/activate
   pip3 install -r requirements.txt
   ```
## To reproduce a figure

1. Open the file `artifact_eval/remote_run.py`. 
   1. Replace `variant_0_addr` and `variant_0_ip` with the hostname and address,
      respectively, of `vm1`.
   2. To produce a *lower bound*, replace `variant_1_addr` and `variant_1_ip`
      with the same address and IP, i.e. that of `vm1`.
   3. To produce an *upper bound*, replace `variant_1_addr` and `variant_1_ip` 
      with the hostname or address of `vm2`.
   4. Set the architecture of the corresponding variants. The *only* supported
      options are `x86_64` or `aarch64`.

2. On `vm1` and `vm2`, compile the kernel module.
    1. `cd kernel_module`
    2. Adjust settings in `include/build_config.h` as outlined for the figure
       you are reproducing. The build settings for each figure are given below.
    3. Build: `make clean && VERBOSITY=0 make`. 

       > `VERBOSITY=0` turns off logging to get accurate performance measurements.
       > If you turn on logging to troubleshoot something, the logs will appear
       > in `/var/log/syslog` with the prefix `monmod: ` (the working title of
       > the system)

    4. Remove already-running kernel module, if any: `sudo rmmod monmod`
    5. Insert the newly built module: `sudo insmod build/monmod.ko`

4. On `vm1` and `vm2`, compile the preloadable shared library.

    1. `cd library`
    2. Adjust settings in `include/build_config.h` as outlined for the figure
       you are reproducing. 
    3. Build: `make clean && OPT=1 make`. 

      > `OPT=1` implies `VERBOSITY=0`, unless otherwise specified.
      > `VERBOSITY=0` turns off logging to get accurate performance measurements.
      > If you turn on logging to troubleshoot something, the logs will appear
      > in `monmod_{id}_{ancestry}.log` files.
      > Note that some benchmarks below require `VERBOSITY=1`.

      **Note:** Changing build environment variables does not invalidate your
      build. If you set different environment variables, you **must** call
      `make clean` first.

5. Run the "run" script for the appropriate figure.
   You will be prompted for a password. This is the superuser 
   password on both `vm1` and `vm2`. The password is needed to load and reset 
   the kernel module, and to enable accelerated network access if enabled 
   using `libvma` 
   (privilege `CAP_NET_RAW`).

   > Depending on the figure, the run script does slightly different things,
   > but in most cases it
   >  1. Generates a configuration file for our system and stores it at
   >     `~/config_temp.ini` on all servers.
   >  2. Launches execution of the to-be-benchmarked application on one or
   >     two machines by running something like 
   >     `~/monmod/scripts/monmod_start.sh ~/config_temp.ini <id> <cmd>
   >  3. Launches a benchmarking command on `vm3`. For some benchmarks, instead
   >     of launching a benchmarking command on `vm3`, the script simply waits
   >     for the started program to terminate and measures the total execution
   >     time.
   >  4. Store the measurement results in a file named `figure_X_results.py`,
   >     which the plot script will include to create plot.

   > **Note:**
   > The commands that are being executed on each server will be printed 
     with a `>` prefixed. If there's an error during any of these commands,
     try running it manually and see if there is any error output.
   
   > **Note:**
   > If you have an unstable Internet connection, it may help to play around
   > with the various timeouts in the scripts, or just run the commands
   > manually.

6. Run the "plot" script for the appropriate figure. This should pick up the
   data stored by the run file, calculate relative overheads and plot a
   figure similar to the one in the paper. The plot will be generated as a
   PDF with the file name `figure_XX.pdf`.

## Figure 5, Figure 6, and Figure 7

### Baseline

To obtain a baseline, run
```
python3 ./figure_5_6_7_run_native.py
```

This runs the three benchmarks `nginx`, `lighttpd` and `redis` on `vm0` and 
benchmarks it from `vm3`. The results are stored in `./figure_5_6_7_native_results.py

You must run this before any of the plot scripts for figure 5, 6, 7, as those
figures use the baseline to calculate relative overheads.

### `kernel_module/include/build_config.h`

Ensure the following build flag is set as follows:

``` 
#define MONMOD_MONITOR_PROTECTION        (MONMOD_MONITOR_FLAG_PROTECTED \
                                          | MONMOD_MONITOR_HASH_PROTECTED) 
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### `library/include/build_config.h`

If your network card supports acceleration through libVMA, build with 
environment variable `USE_LIBVMA=2` set: `make clean && USE_LIBVMA=2 OPT=1 make`

```
#define ENABLE_CHECKPOINTING FORK_CHECKPOINTING 
#define MEASURE_TRACING_OVERHEAD 0
```

 - Build with `OPT=1`
 - If libVMA is available, build with environment variable `USE_LIBVMA=2`

## Figure 8

### `library/include/build_config.h` -- for all iterations

```
#define ENABLE_CHECKPOINTING NO_CHECKPOINTING 
#define MEASURE_TRACING_OVERHEAD 1
```

**Note:** Please make sure to reset `MEASURE_TRACING_OVERHEAD` back to `0` after
this benchmark, as it needs to be unset for all other benchmarks. This is the
only benchmark that uses this flag!

### iteration 0  -- native results

This iteration benchmarks the native system call execution baseline and does
not use our system.

Call the run script as follows:
```
python3 ./figure_8_run.py 0
```

Results will be stored in `figure_8_0_results.py`.


### iteration 1  -- unprotected results

Configure and build the **kernel module** with this setting in `kernel_module/include/build_config.h:
```
#define MONMOD_MONITOR_PROTECTION        MONMOD_MONITOR_UNPROTECTED
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### Running

Run the run script as follows, with argument `1`, to generate results in 
`figure_8_1_results.py`:
```
python3 figure_8_run.py 1
```

### `kernel_module/include/build_config.h` for iteration 2 -- compare/flag protected results

Configure and build the kernel module with this setting in `kernel_module/include/build_config.h:
```
#define MONMOD_MONITOR_PROTECTION        (MONMOD_MONITOR_FLAG_PROTECTED \
                                          | MONMOD_MONITOR_COMPARE_PROTECTED) 
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### Running

Run the run script as follows, with argument `2`, to generate results in 
`figure_8_2_results.py`:
```
python3 figure_8_run.py 2
```

### `kernel_module/include/build_config.h` for iteration 3 -- mprotected results

Configure and build the kernel module with this setting in `kernel_module/include/build_config.h`:
```
#define MONMOD_MONITOR_PROTECTION        MONMOD_MONITOR_FLAG_MPROTECTED 
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### Running

Run the run script as follows, with argument `3`, to generate results in 
`figure_8_3_results.py`:

```
python3 figure_8_run.py 3
```

## Figure 9, Figure 10

**Note:** The plotting script for these figures depends on results from figure 8, 
iterations 0 and 2, for the syscall interception baseline. Make sure to run it first.

**Important Note: These benchmarks require VERBOSITY=1 to be set when compiling the library.**

### `kernel_module/include/build_config.h` -- configuration for all iterations

Make sure the following flags are set:

``` 
#define MONMOD_MONITOR_PROTECTION        (MONMOD_MONITOR_FLAG_PROTECTED \
                                          | MONMOD_MONITOR_HASH_PROTECTED) 
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### `library/include/build_config.h` -- configuration for all iterations

Make sure the following flags are set:

```
#define ENABLE_CHECKPOINTING FORK_CHECKPOINTING 
#define MEASURE_TRACING_OVERHEAD 0
```

Please make sure you build with `make clean && VERBOSITY=1 OPT=1 make`.

## Figure 11

Figure 10 depends on the results of figure 8, iteration 0, to establish a
baseline. Please make sure to run that benchmark before this one.

### `kernel_module/include/build_config.h` -- configuration for all iterations

``` 
#define MONMOD_MONITOR_PROTECTION        (MONMOD_MONITOR_FLAG_PROTECTED \
                                          | MONMOD_MONITOR_HASH_PROTECTED) 
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### `library/include/build_config.h` for iteration 0 

```
#define ENABLE_CHECKPOINTING FORK_CHECKPOINTING 
#define MEASURE_TRACING_OVERHEAD 0
```

Please make sure you build with `make clean && VERBOSITY=1 OPT=1 make`.

### Running

Note the argument `0` to the run function to indicate this is the first 
iteration.

```
python3 ./figure_11_run.py 0
```

The results will be stored in `./figure_11_0_results.py`.

### `library/include/build_config.h` for iteration 1

```
#define ENABLE_CHECKPOINTING CRIU_CHECKPOINTING   # <-- enable CRIU
#define MEASURE_TRACING_OVERHEAD 0
```

Please build using `make clean && VERBOSITY=1 OPT=1 make`.

### Running

Note the `1` argument.

```
python3 ./figure_11_run.py 1
```

The results will be stored in `./figure_11_1_results.py`.

### Troubleshooting for this step

On `x86_64`, you may have to adjust the breakpoint instruction size.
Open `figure_11_run.py` and navigate to the definition of the `config_template`
variable. If the default value does not work, try values between 1 - 4 for the
`instr_len` setting.

CRIU takes a really long time especially at frequent checkpoint intervals.
If you run into issues (e.g. you are filling your VM's hard drive with checkpoint images),
you can reduce the number of iterations of the microbenchmark. Just adjust the
appropriate constant in `~/monmod/benchmarks/microbenchmarks/build_config.h` and
rebuild using `make`. You will of course have to re-run your baseline again
after doing this as well.


### After all iterations

Please run the plot command after all run iterations:
```
python3 ./figure_11_plot.py
```

Please make sure you build with `make clean && VERBOSITY=1 OPT=1 make`.


## Hardware

Our evaluation results as presented in the paper were obtained on one x86_64
machine and one aarch64 machine. Details of the CPUs:

x86_64:
```
Vendor ID:              GenuineIntel
  Model name:           Intel(R) Core(TM) i9-9900K CPU @ 3.60GHz
    CPU family:         6
    Model:              158
    Thread(s) per core: 2
    Core(s) per socket: 8
    Socket(s):          1
```

aarch64: 

```
Vendor ID:                Cavium
  Model name:             ThunderX 88XX
    Model:                1
    Thread(s) per core:   1
    Core(s) per cluster:  48
```

We used the following network interface cards:

```
Ethernet controller: Mellanox Technologies MT27800 Family [ConnectX-5]
```

Along with the interface cards, we used the `libVMA` messaging accelerator,
installable through `sudo apt install libvma`. This accelerator only works with
certain Mellanox network cards. If available, you can use these by setting
`USE_LIBVMA=2` during compilation. The messaging accelerator primarily reduces
our overheads for the examples with less batching.

## Troubleshooting

 - As mentioned above, if any errors occur, **please first turn on logging**. By
   default, no messages are printed for performance reasons. Logging is turned
   on by rebuilding the kernel module and the shared library with the
   `VERBOSITY` environment variable set. You will need to clear your old build.
   Logs are in `monmod_{id}_*.log` files for the shared library and in 
   `/var/log/syslog` for the kernel module. Each benchmark run on the user side
   also generates files `figure_X_stdout.log` and `figure_X_stderr.log` which 
   may be useful for troubleshooting.

 - Probably the **most common error** is related to the network configuration.
   Ensure that all hosts are reachable from one another, e.g. by trying to
   ping them. To rule out network issues as the source of a problem, you can
   edit the configuration file for the current benchmark once it has been
   generated into `~/config_temp.ini` and remove all but one variant. If you
   run a single variant, network communication shouldn't be an issue, and if the
   problem persists, you know to look elsewhere.

 - Similarly, some issues can be ruled out by editing the config file 
   `~/config_temp.ini`. For example, if checkpointing is causing issues, you can
   disable all checkpoints by removing the breakpoitnts in the config file.

 - Another **very common error** is running mismatched monitors/variants. Upon
   encountering an issue, please double-check that the libraries and kernel
   modules on each host have been compiled with exactly the same flags. Also
   ensure that all variants are using the same configuration by inspecting the
   `~/config_temp.ini` file.

 - Resetting: If things end up in a weird state, it doesn't hurt to reset
   everything. The `~/monmod/scripts/stop_monmod.sh` script does just that
   (requires root privileges). Unloading and reloading the kernel module is
   also a good idea: 
   `sudo rmmod monmod; sudo insmod ~/monmod/kernel_module/build/monmod.ko`.

 - `remote_run.py` scripts: The run scripts are supposed to make evaluation more
   straightforward, but may fail on unstable internet connections (there is
   a built-in retry mechanism but this may fail too). The script prints all
   commands that it attempts to execute; if those commands don't work, we 
   suggest you attempt to run the commands on the respective `vm1`, `vm2` and
   `vm3` machines manually. We are also happy to help debug the script if it
   does not work on your end.

 - If the system appears to not run at all -- that is, the overheads are near
   zero -- it is possible that the shared library is not being preloaded. Ensure
   that the benchmarked binary does not have any special capabilities set, as
   this disables preloading of libraries: `sudo setcap -r <benchmark-binary>`.
   Other issues could include not finding the library after it has been built;
   in that case you can hard-code the path to the library (should be in 
   `library/build/libmonmod.so`) in the run scripts (`/scripts/monmod_run.sh`).

 - Sometimes benign differences during program startup can cause the program
   to abort, for example if different shared libraries are loaded by the
   program depending on the architecture. To avoid issues with this, it is
   sometimes helpful to set the `ignore_first_n` configuration value, which
   will disable cross-checking on the first N specified system calls. You can
   set this setting in `config_template.ini` for figures 5, 6, and 7, or in
   the config template variables in the respective run scripts.

 - Connectivity errors: Lower-ID variants should always be started first. If you
try to start variant ID 1 before variant ID 0, it will not succeed. The
`remote_run.py` script takes care of this.

Please do not hesitate to contact us if there are any issues:

    a8-artifact-eval@outlook.com
