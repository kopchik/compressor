compressor
==========

A mutithreaded lzma/zlib-compressior (proof of concept). Was made to quickly compress
large disk images. It supports input buffering, output is in raw format.

TODO:

1. Currently outputs only to STDIN
1. Support of external compressors is very buggy
1. Many TODO's inside code :)


Benchmarks
----------

Very dirty tests that do not account CPU topology, dynamic clocking, cache settings, input buffering, etc, etc...
AMD FX-8120, 16G ram, Linux fx 3.7.10-1-custom

**LZMA**

~~~~
[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=300 | xz -1 | pv -ab > /dev/null
300+0 records in/s]
300+0 records out
314572800 bytes (315 MB) copied, 16.2312 s, 19.4 MB/s
42.5MiB [2.62MiB/s]

[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=300 | ./compressor.py --workers 1 --level 1 --method lzma  /dev/stdin | pv -ab > /dev/null
300+0 records in/s]
300+0 records out
314572800 bytes (315 MB) copied, 7.59138 s, 41.4 MB/s
42.9MiB [2.74MiB/s]

[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=300 | ./compressor.py --workers 2 --level 1 --method lzma  /dev/stdin | pv -ab > /dev/null
300+0 records in/s]
300+0 records out
314572800 bytes (315 MB) copied, 4.71207 s, 66.8 MB/s
42.9MiB [4.58MiB/s]

[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=300 | ./compressor.py --workers 4 --level 1 --method lzma  /dev/stdin | pv -ab > /dev/null
300+0 records in/s]
300+0 records out
314572800 bytes (315 MB) copied, 3.1411 s, 100 MB/s
42.9MiB [6.59MiB/s]

[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=300 | ./compressor.py --workers 8 --level 1 --method lzma  /dev/stdin | pv -ab > /dev/null
300+0 records in/s]
300+0 records out
314572800 bytes (315 MB) copied, 1.83598 s, 171 MB/s
42.9MiB [9.24MiB/s]
~~~~


**ZLIB**

~~~~
[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=3000 | gzip -1 | pv -ab > /dev/null
3000+0 records ins]
3000+0 records out
3145728000 bytes (3.1 GB) copied, 61.7914 s, 50.9 MB/s
 958MiB [15.5MiB/s]

[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=3000 | ./compressor.py --workers 1 --level 1 --method zlib  /dev/stdin | pv -ab > /dev/null
3000+0 records ins]
3000+0 records out
3145728000 bytes (3.1 GB) copied, 53.4365 s, 58.9 MB/s
 956MiB [17.8MiB/s]

[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=3000 | ./compressor.py --workers 2 --level 1 --method zlib  /dev/stdin | pv -ab > /dev/null
3000+0 records ins]
3000+0 records out
3145728000 bytes (3.1 GB) copied, 31.5229 s, 99.8 MB/s
 956MiB [30.1MiB/s]

[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=3000 | ./compressor.py --workers 4 --level 1 --method zlib  /dev/stdin | pv -ab > /dev/null
3000+0 records ins]
3000+0 records out
3145728000 bytes (3.1 GB) copied, 20.558 s, 153 MB/s
 956MiB [46.3MiB/s]

[exe@fx crm3]$ sudo dd if=/dev/sda2 bs=1M count=3000 | ./compressor.py --workers 8 --level 1 --method zlib  /dev/stdin | pv -ab > /dev/null
3000+0 records ins]
3000+0 records out
3145728000 bytes (3.1 GB) copied, 13.9575 s, 225 MB/s
 956MiB [68.2MiB/s]
~~~~
