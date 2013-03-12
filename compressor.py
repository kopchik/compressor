#!/usr/bin/env python3
from multiprocessing import cpu_count
from subprocess import Popen, PIPE
from threading import Thread
from select import select
from queue import Queue
import argparse
import shlex
import lzma
import zlib
import fcntl
import sys
import os

dbg = lambda *a: None
CPU_COUNT = cpu_count()
MB = 1024*1024
class EOF: pass

def set_nio(fd):
  flags = fcntl.fcntl (fd, fcntl.F_GETFL, 0)
  flags = flags | os.O_NONBLOCK
  fcntl.fcntl (fd, fcntl.F_SETFL, flags) 

def set_bio(fd):
  flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
  if flags | os.O_NONBLOCK:
    flags ^= os.O_NONBLOCK
  fcntl.fcntl (fd, fcntl.F_SETFL, flags) 


class Sucker(Thread):
  def __init__(self, fd=None, chunk_size=None, bufs=None):
    #TODO: check arguments
    self.fd = fd
    self.chunk_size = chunk_size
    self.queue = Queue(bufs)
    super().__init__()

  def run(self):
    while True:
      buf = bytearray()
      while len(buf) < self.chunk_size:
        data = self.fd.read(self.chunk_size-len(buf))
        if len(data) == 0:
          break
        dbg("IN: read", len(data), "bytes")
        buf.extend(data)
      if len(buf) == 0:
        dbg("IN: all data was read")
        self.queue.put(EOF)
        return
      self.queue.put(buf)

  def get(self):
    return self.queue.get()


# TODO: doesn't work
class PopenWorker(Thread):
  def __init__(self, chunk, cmd='gzip -1'):
    super().__init__()
    self.chunk = chunk
    self.cmd = cmd
    dbg("ARCH: chunk to send", len(self.chunk))

  def run(self):
    self.result = bytearray()
    p = Popen(shlex.split(self.cmd), stdin=PIPE, stdout=PIPE)
    r = bytearray()
    stdin = p.stdin.fileno()
    stdout = p.stdout.fileno()
    set_nio(stdin)
    set_nio(stdout)
    sent = 0
    while True:
      # TODO: catch exceptions here
      dbg("ARCH: waiting for select")
      rfds, wfds, err = select([stdout], [stdin], [stdin, stdout])
      dbg("ARCH select:", rfds, wfds, err)
      assert not err, "whoops: %s" % err
      if wfds:
          sent += os.write(stdin, self.chunk[sent:])
          dbg('so far sent', sent, 'bytes to', p)
          if sent == len(self.chunk):
            dbg("a whole chunk was sent, closing stdin")
            os.close(stdin)
            break
      if rfds:
        r = os.read(stdout, 100000)
        dbg('got', len(r), 'bytes')
        self.result.extend(bytearray(r))

    # read the rest
    while True:
      dbg("ARCH: waiting for select")
      rfds, wfds, err = select([stdout], [], [stdout])      
      dbg("ARCH select:", rfds, wfds, err)
      assert not err, "whoooops"
      r = p.stdout.read()
      dbg('got', len(r), 'bytes')
      if not r:
        dbg("read complete, closing stdout")
        os.close(stdout)
        break
      self.result.extend(bytearray(r))


class LZMAWorker(Thread):
  def __init__(self, chunk, level=0):
    super().__init__()
    self.chunk = chunk
    self.level = level
    dbg("ARCH: chunk to send", len(self.chunk))

  def run(self):
    self.result = bytearray()
    c = lzma.LZMACompressor(format=lzma.FORMAT_XZ, preset=self.level)
    self.result += c.compress(self.chunk)
    self.result += c.flush()


class ZLIBWorker(Thread):
  def __init__(self, chunk, level=1):
    super().__init__()
    self.chunk = chunk
    self.level = level
    dbg("ARCH: chunk to send", len(self.chunk))

  def run(self):
    self.result = bytearray()
    self.result = zlib.compress(self.chunk, self.level)


class DummyWorker(Thread):
  def __init__(self, chunk, level=1):
    super().__init__()
    self.chunk = chunk
    self.level = level
    dbg("ARCH: chunk to send", len(self.chunk))

  def run(self):
    self.result = self.chunk

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='privet, isden')
  parser.add_argument('-c', '--chunk-size', type=int,
    default=10*MB, help='chunk size')
  parser.add_argument('-w', '--workers', type=int, default=CPU_COUNT,
    help='number of workers, default=<cpunum>')
  parser.add_argument('-b', '--bufs', type=int,
                      default=CPU_COUNT, help='input buffer size, default=<cpunum>')
  parser.add_argument('-d', '--debug', action='store_true',
                      default=False, help="enable debug output")
  parser.add_argument('file', nargs=1, help='input file')
  parser.add_argument('-m', '--method',
                      default='lzma', help="Compress method (lzma|zlib|dummy)")
  parser.add_argument('-l', '--level', type=int,
                      default=1, help="compress level (lower faster)")
  args =  parser.parse_args()
  dbg(args)

  if args.method == 'lzma':
    Worker = LZMAWorker
  elif args.method == 'zlib':
    Worker = ZLIBWorker
  elif args.method == 'dummy':
    Worker = DummyWorker
  else:
    sys.exit('unknown compression algorithm %s' % args.method)

  if args.debug:
    dbg = lambda *a: print(*a, file=sys.stderr)
  fd=open(args.file[0], 'rb')
  bufs = max(args.bufs, args.workers)
  sucker = Sucker(fd=fd, chunk_size=args.chunk_size, bufs=bufs)
  sucker.start()
  
  # MAIN LOOP
  eof = False
  stdout = sys.stdout.fileno()
  while eof == False:
    workers = []
    for x in range(args.workers):
      chunk = sucker.get()
      if chunk == EOF:
        dbg("got eof")
        eof = True
        break
      worker = Worker(chunk, level=args.level)
      worker.start()
      workers += [worker]

    for worker in workers:
      worker.join()
      os.write(stdout, worker.result)