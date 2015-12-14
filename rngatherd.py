#!/usr/bin/python3
# -*- coding: utf-8 -*-

from multiprocessing import Process, Queue
import os
import time
from RandPiClient import get_random

DEVICE = os.path.join(os.path.sep, "dev", "hwrandom")
READ_HWRNG = True
READ_RAND_PI = False


def read_hwrng(q):
    while True:
        if q.full():
            time.sleep(0.1)
        else:
            with open(os.path.join(os.path.sep, "dev", "hwrng"), 'rb') as whrng:
                q.put(whrng.read(8))


def read_rand_pi(q):
    while True:
        if q.full():
            time.sleep(1)
        else:
            q.put(get_random(1024))


def write_to_pipe(q):
    pipe = os.open(DEVICE, os.O_WRONLY)
    while True:
        os.write(pipe, q.get())


if __name__ == '__main__':
    if not os.path.exists(DEVICE):
        os.mkfifo(DEVICE)
    q = Queue(1024)
    if READ_HWRNG:
        gather_hwrng_process = Process(target=read_hwrng, args=(q,))
        gather_hwrng_process.daemon = True
        gather_hwrng_process.start()
    if READ_RAND_PI:
        gather_rand_pi_process = Process(target=read_rand_pi, args=(q,))
        gather_rand_pi_process.daemon = True
        gather_rand_pi_process.start()
    while True:
        try:
            write_to_pipe(q)
        except BrokenPipeError:
            pass
