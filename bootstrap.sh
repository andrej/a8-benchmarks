#!/bin/bash -x

root=$(realpath $(dirname "$0"))
microbenchmark_root=$root/microbenchmarks
wrk_root=$root/wrk
nginx_root=$root/nginx
lighttpd_root=$root/lighttpd
redis_root=$root/redis

error_out () {
	printf "An error occured, see output above.\n"
	exit 1
}

sudo apt install -y rpl unzip autoconf || error_out

if [ ! -d "$wrk_root" ]
then
	git clone https://github.com/wg/wrk "$wrk_root" &&
	cd "$wrk_root" &&
	git reset --hard a211dd5a7050 &&
	make ||
	error_out
	cd "$root"
fi

if [ ! -d "$microbenchmark_root/build" ]
then
	cd "$microbenchmark_root" &&
	make ||
	error_out
	cd "$root"
fi

if [ ! -d "$nginx_root/logs" ]
then
	mkdir "$nginx_root/logs"
fi

if [ ! -d "$nginx_root/install" ]
then
	cd "$nginx_root" &&
	wget http://nginx.org/download/nginx-1.22.1.tar.gz &&
	tar -xzvf nginx-1.22.1.tar.gz &&
	mkdir "$nginx_root"/install &&
	cd nginx-1.22.1 &&
	./configure --prefix="$nginx_root/install" \
		--with-debug --without-http_rewrite_module &&
	make &&
	make install ||
	error_out
	cd "$root"
fi

if [ ! -d "$lighttpd_root/install" ]
then
	cd "$lighttpd_root" &&
	rpl -R "%%MONMOD_BENCHMARKS_ROOT%%" "$root" config/ &&
	wget https://download.lighttpd.net/lighttpd/releases-1.4.x/lighttpd-1.4.71.tar.gz &&
	tar -xvzf lighttpd-1.4.71.tar.gz &&
	cd "lighttpd-1.4.71" &&
	./configure --prefix "$lighttpd_root/install" --without-zlib --without-bzip2 --without-pcre --without-pcre2 &&
	make &&
	make install ||
	error_out
	cd "$root"
fi

if [ ! -d "$redis_root/install" ]
then
	cd "$redis_root" &&
	wget https://download.redis.io/releases/redis-6.2.12.tar.gz &&
	tar -xzf redis-6.2.12.tar.gz &&
	cd redis-6.2.12 &&
	patch -p1 -i ../patches.patch &&
	USE_JEMALLOC=no make distclean &&
	USE_JEMALLOC=no make &&
	mkdir -p "$redis_root/install" &&
	PREFIX="$redis_root/install" make install ||
	error_out
	cd "$root"
fi
