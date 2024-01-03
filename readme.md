# monmod benchmarks

Contains scripts and configurations to build the benchmarks/test cases for
monmod. See [main monmod repository](https://github.com/andrej/monmod).


## Getting Started

1. Install monmod as per the instructions in the main repository.

2. Run `bootstrap.sh` to build and install the benchmarks. They will be
   installed locally inside this folder.

3. ```export PATH="<path to monmod/scripts>:$PATH"```

4. Follow below instructions to run the benchmarks / test cases. The 
   following general instructions apply to all:

## Reducing Noise

To disable frequency scaling on the x86 machines:
```
sudo cpupower frequency-set -g performance
```

To isolate the benchmarked processes on dedicated cores so there is no resource
contention (makes a big difference on ARM):
```
sudo cset shield --cpu 10-12; sudo cset shield --shield --pid $(pidof -s lighttpd),$(pidof -s vma-server)
```

## General instructions

### To run benchmarks natively

```
time <target>
```

This will report native speeds. We are interested in the total. `<target>` can be `./microbenchmarks/build/getcwd`, `./microbenchmarks/build/read`, and `./microbenchmarks/build/sched_yield` when we run microbenchmarks. Also, `<target>` can be `main` test program in the main monmod repository.

### To run one variant locally

This will not be a true _multi-_ variant execution, since only one variant will
be started, but it is a useful test to assess the overheads associated with
system call tracing, serializing arguments. This also is a good "Hello World"
example to make sure the basics are installed and run correctly.

```
monmod_run.sh 0 ./configs/one_local.ini <command> <command arguments>
```

After that, examine the log file `monmod_0_0.log`; depending on the
`VERBOSITY` setting used while building monmod (`build_config.h`), more or
less (for lowest verbosity settings _no_) information is logged.

Sometimes, it can be nice to see the log file update while the program is
running. In a separate terminal:

```
tail -f monmod_0_0.log
```


### To run two variants locally

Additionally to testing the basics, this actually runs two variants; although
the variants will run locally, i.e. on the same machine, so the diversity will
be very limited (less security benefits). It is useful for debugging and making
sure that the cross-checking of arguments and netowrking components work.

Open two terminals.  In the first terminal:

```
monmod_run.sh 0 ./configs/two_local.ini <command> <command arguments>
```

### To run two variants remotely, across two machines

Finally, with this we arrive at a true multi-variant execution across diverse
platforms (as long as the two machines you chose are, in fact, diverse).

First, you must adjust the configuration file to use the IP addresses of the
machines you are using. You can leave the ports as-is, unless you are using
those ports, in which case you can chose an arbitrary other free port. On
one of the machines:

```
vim ./configs/two_remote.ini   # Adjust IP addresses
```

Then, on the other:

```
rsync <user>@<first machine IP>:<path>/configs/two_remote.ini \
	<path>/configs
```

This ensures that both machines are using identical configuration files.

_*Important Note:* When running across multiple physical machines, always make
sure both machines are using exactly the same configuration files, the same
version of monmod (including build configuration flags) and the same version of
the program you are benchmarking. This is a common source of issues!_

Then, on machine A:

```
monmod_run.sh 0 ./configs/two_remote.ini <command> <command arugments>
```

On the other:

```
monmod_run.sh 1 ./configs/two_remote.ini <command> <command arugments>
```


## Instructions for specific Benchmarks

Executing the benchmarks in monmod follows the general instructions above. In
the following, we will just document the `<command>` and `<command arguments>`
portions of the example commands given above, as well as the used configuration
files, as those are the only things that really change.

### Microbenchmarks

There are microbenchmarks for three system calls from previous work in
`experiments/microbenchmarks`. To time their native speed, use
the `time` command. 

Essentially, these benchmarks just run one simple system call in a busy loop
for a fixed number of iterations. The number of iterations can be configured
in `microbenchmarks/build_config.h`.

To build, run `make` in the microbenchmark folder.

To run, simply type `./build/getcwd`, `./build/read` or `./build/sched_yield` 
in the microbenchmark folder after building. There will be no output.
 
### Running lighttpd

We run lighttpd in non-daemon mode serving a 4KB static page:

```
./lighttpd/install/sbin/lighttpd -D -f ./lighttpd/config/static_4KB.conf
```

The sever will run until you terminate it with CTRL-C. From another machine,
for benchmarking, we use the `wrk` tool which opens some connections and
repeatedly sends HTTP requests, as follows:
   
```
./wrk/wrk -c10 -t1 -d10s http://<IP where you started server>:3000/index.html
```

The `-c` flag determines the number of connections for the benchmark, `-t` the
number of concurrent threads, and `-d` the duration.

#### Checkpointing configuration

Currently, we create checkpoints at each entry to the `connection_accept()`
function in lighttpd, i.e. whenever a new connection is established. Use
`objdump --disassemble` to see at which program counter this function starts,
sicne it may change between compilations.

See configuration file `cnofigs/two_remote_advanced.ini` for examples of
setting breakpoints and setting up checkpointing. 

### Running nginx

We use the following command to start nginx with our configuration file (the
configuration file ensures that the server is started in non-daemon mode and
points to our 4KB static HTML page for its document root):

```
./nginx/install/sbin/nginx -p ./nginx/ -c config/nginx.conf 
```

Then, as with lighttpd, we benchmark using `wrk`.

### Running redis

The command to start redis will look like:

```
./redis/install/bin/redis-server ./redis/config/redis.conf
```

Note the configuration file disables multi-threading to make it work in our
case. We benchmark using `redis-benchmark`:

```
./redis/install/bin/redis-benchmark -q -n 100000 -h <host> -p <port>
```