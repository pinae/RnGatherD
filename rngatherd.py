#!/usr/bin/python3
# -*- coding: utf-8 -*-

from multiprocessing import Process, Queue
import os
import time

DEVICE = os.path.join(os.path.sep, "dev", "hwrandom")


def read_hwrng(q):
    while True:
        if q.full():
            time.sleep(0.1)
        else:
            with open(os.path.join(os.path.sep, "dev", "hwrng"), 'rb') as whrng:
                q.put(whrng.read(8))


def write_to_pipe(q):
    pipe = os.open(DEVICE, os.O_WRONLY)
    while True:
        os.write(pipe, q.get())


if __name__ == '__main__':
    if not os.path.exists(DEVICE):
        os.mkfifo(DEVICE)
    q = Queue(1024)
    gather_process = Process(target=read_hwrng, args=(q, ))
    gather_process.daemon = True
    gather_process.start()
    while True:
        try:
            write_to_pipe(q)
        except BrokenPipeError:
            pass
