# Artifact Evaluation Instructions

Thank you for taking the time to evaluate our artifacts. We hope these
instructions make it as easy as possible to test the functionality of our 
system.

We have created an anonymous e-mail account to be able to assist if any 
troubleshooting is needed:

    a8-artifact-eval@outlook.com

## Overview

Our system replicates program execution across a set of distributed hosts and 
monitors their behavior. It does so through two components that are present
on each host
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

1. Instantiate three virtual machines. We will refer to those three machines
   as `vm1`, `vm2` and `vm3`. `vm1` and `vm2` will run the variants; `vm3` will
   be used as a client for benchmarking.
2. From your local machine (likely the machine you are reading this from), set
   up SSH keys to allow password-free authentication to all of `vm1`, `vm2` and
   `vm3`. **Important:** Our benchmarking script requires that SSH keys are set
   up. Password-based authentication will not work.
   - Please see [here on how to set up SSH keys](https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server).
   - Test that you can log into all VMs without passwords: `ssh user@vm1` should
     open a command prompt on that machine without any password prompt.
3. On `vm1` and `vm2`: (Identical)
   a. Copy the entirety of our artifact to both machines.
   b. Run the script `./bootstrap.sh` at the root. This will install 
      dependencies.
   c. Run the script `./benchmarks/bootstrap.sh`. This will fetch and compile
      our benchmarks: `nginx`, `lighttpd`, `redis` and the microbenchmarks. 
      This may take a while.
4. On `vm3`:
   a. Copy the subdirectory `benchmarks` onto the machine.
   b. Run the script `./benchmarks/bootstrap.sh`. This will fetch and compile
      the `wrk` and `redis-benchmark` utilities used for client-side 
      benchmarking, along with the other benchmarks (which won't be needed on 
      this machine).
5. On all machines, `vm1`, `vm2` and `vm3`:
   a. Ensure your user has sudo privileges, i.e. is part of the group 
       `sudoers`. **Ensure that the superuser password on all VMs is the same
       as our `remote_run.py` script for artifact evaluation assumes this.**
   b. Take note of the IP addresses of the public link of the machines:
       `ip addr`.
6. Locally, on your own machine, ensure you have all required Python packages
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

## To reproduce lower and upper bounds for a figure

1. Open the file `artifact_eval/remote_run.py`. 
   a. Replace `variant_0_addr` with the hostname or address of `vm1`.
   b. To produce a *lower bound*, replace `variant_1_addr` with the same
      address, i.e. that of `vm1`.
   c. To produce an *upper bound*, replace `variant_1_addr` with the hostname
      or address of `vm2`.
   d. Set the architecture of the corresponding variants. The *only* supported
      options are `x86_64` or `aarch64`.

2. Open the file `artifact_eval/config_template.ini`.
    a. Below the comment `# variant 0`, in the field `address`, put the IP
       address of `vm1` surrounded by double quotes. You can find the IP address
       of `vm1` by running `ip addr` on that machine.
    c. To produce a *lower bound*, insert the same IP address of `vm1` also
       in the lower `address` field, under `# variant 1`. When doing so, 
       ensure that the two variants have different port numbers.
    b. To produce an *upper bound*, insert the IP address of `vm2` in the field
       `address` below the comment `# variant 1`.

3. On `vm1` and `vm2`, compile the kernel module.
    a. `cd kernel_module`
    b. Adjust settings in `include/build_config.h` as outlined for the figure
       you are reproducing.
    c. Build: `make clean && VERBOSITY=0 make`. 
       > `VERBOSITY=0` turns off logging to get accurate performance measurements.
       > If you turn on logging to troubleshoot something, the logs will appear
       > in `/var/log/syslog` with the prefix `monmod: ` (the working title of
       > the system)
    d. Remove already-running kernel module, if any: `sudo rmmod monmod`
    e. Insert the newly built module: `sudo insmod build/monmod.ko`

4. On `vm1` and `vm2`, compile the preloadable shared library.
    a. `cd library`
    b. Adjust settings in `include/build_config.h` as outlined for the figure
       you are reproducing. 
    c. Build: `make clean && OPT=1 make`. 
       > `OPT=1` implies `VERBOSITY=0`, unless otherwise specified.
       > `VERBOSITY=0` turns off logging to get accurate performance measurements.
       > If you turn on logging to troubleshoot something, the logs will appear
       > in `monmod_{id}_{ancestry}.log` files.

5. Run the "run" script for the appropriate figure.
   You will be prompted for a password. This is the superuser 
   password on both `vm1` and `vm2`. The password is needed to load and reset 
   the kernel module, and to enable accelerated network access if enabled 
   using `libvma` 
   (privilege `CAP_NET_RAW`).

   > The commands that are being executed on each server will be printed 
     with a `>` prefixed. If there's an error during any of these commands,
     try running it manually and see if there is any error output.

6. Run the "plot" script for the appropriate figure.

## Figure 5, Figure 6, and Figure 7

### kernel_module configuration

``` 
#define MONMOD_MONITOR_PROTECTION        (MONMOD_MONITOR_FLAG_PROTECTED \
                                          | MONMOD_MONITOR_COMPARE_PROTECTED) 
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### library configuration

If your network card supports acceleration through libVMA, build with 
environment variable `USE_LIBVMA=2` set: `make clean && USE_LIBVMA=2 OPT=1 make`

```
#define ENABLE_CHECKPOINTING FORK_CHECKPOINTING 
```

 - Build with `OPT=1`
 - If libVMA is available, build with environment variable `USE_LIBVMA=2`

## Figure 8

### library configuration -- for all iterations

```
#define ENABLE_CHECKPOINTING NO_CHECKPOINTING 
#define MEASURE_TRACING_OVERHEAD 1
```

### iteration 0  -- native results

This iteration benchmarks the native system call execution baseline and does
not use our system.

Call the run script as follows:
```
python3 ./figure_8_run.py 0
```

Results will be stored in `figure_8_0_results.py`.


### iteration 1  -- unprotected results

Configure and build the kernel module with this setting in `kernel_module/include/build_config.h:
```
#define MONMOD_MONITOR_PROTECTION        MONMOD_MONITOR_UNPROTECTED
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### running
Run the run script as to generate results in `figure_8_1_results.py`:
```
python3 figure_8_run.py 1
```

### iteration 2  -- compare/flag protected results

Configure and build the kernel module with this setting in `kernel_module/include/build_config.h:
```
#define MONMOD_MONITOR_PROTECTION        (MONMOD_MONITOR_FLAG_PROTECTED | MONMOD_MONITOR_COMPARE_PROTECTED) 
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### running
Run the run script as to generate results in `figure_8_2_results.py`:
```
python3 figure_8_run.py 2
```

### iteration 3 -- mprotected results

Configure and build the kernel module with this setting in `kernel_module/include/build_config.h:
```
#define MONMOD_MONITOR_PROTECTION        MONMOD_MONITOR_FLAG_MPROTECTED 
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### running

Run the run script as to generate results in `figure_8_3_results.py`:
```
python3 figure_8_run.py 3
```

## Figure 9

**Note: The plotting script for this figure depends on results from figure 8, 
iterations 0 and 2, for the syscall interception baseline. Make sure to run it first.**

**Important Note: These benchmarks require VERBOSITY=1 to be set when compiling the library.**

### kernel_module configuration -- for all iterations

``` 
#define MONMOD_MONITOR_PROTECTION        (MONMOD_MONITOR_FLAG_PROTECTED \
                                          | MONMOD_MONITOR_COMPARE_PROTECTED) 
```

 - Build with `VERBOSITY=0`: `make clean && VERBOSITY=0 make`
 - Make sure to reload kernel module after rebuilding: `sudo rmmod monmod; sudo insmod build/monmod.ko`

### iteration 0 -- additional processing overhead

 library configuration in library/include/build_config.h

```
#define ENABLE_CHECKPOINTING FORK_CHECKPOINTING 
#define MEASURE_TRACING_OVERHEAD 0
```




## Troubleshooting

As mentioned above, if any errors occur, please first turn on logging. By
default, no messages are printed for performance reasons. Logging is turned
on by rebuilding the kernel module and the shared library with the
`VERBOSITY` environment variable set. You will need to clear your old build.
Logs are in `monmod_{id}_*.log` files for the shared library and in 
`/var/log/syslog` for the kernel module.

Connectivity errors: Lower-ID variants should always be started first. If you
try to start variant ID 1 before variant ID 0, it will not succeed. The
`remote_run.py` script takes care of this.

Please do not hesitate to contact us if there are any issues:

    a8-artifact-eval@outlook.com