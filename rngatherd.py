#!/usr/bin/python3
# -*- coding: utf-8 -*-

from multiprocessing import Process, Queue
import os
import sys
import time
import logging
from RandPiClient import get_random
from daemon import Daemon


READ_HWRNG = False
READ_RAND_PI = True


class RnGatherD(Daemon):
    def __init__(self, initialized_logger):
        super().__init__(os.path.join(os.path.sep, "var", "run", "rngatherd.pid"))
        self.logger = initialized_logger
        self.logger.info("Initializing ...")
        self.device = os.path.join(os.path.sep, "dev", "hwrandom")
        self.logger.info("Writing to " + self.device)
        self.q = Queue(1024)
        self.gather_hwrng_process = None
        self.gather_rand_pi_process = None

    @staticmethod
    def read_hwrng(q):
        while True:
            if q.full():
                time.sleep(0.1)
            else:
                with open(os.path.join(os.path.sep, "dev", "hwrng"), 'rb') as hwrng:
                    q.put(hwrng.read(8))

    @staticmethod
    def read_rand_pi(q):
        while True:
            if q.full():
                time.sleep(1)
            else:
                random_data = get_random(1024)
                for i in range((1024//8)-1):
                    q.put(random_data[i*8:(i+1)*8])

    def run(self):
        if not os.path.exists(self.device):
            os.mkfifo(self.device)
        if READ_HWRNG:
            self.gather_hwrng_process = Process(target=self.read_hwrng, args=(self.q,))
            self.gather_hwrng_process.daemon = True
            self.gather_hwrng_process.start()
            with open(self.pidfile, 'a') as pid_file:
                pid_file.write("%s\n" % self.gather_hwrng_process.pid)
            self.logger.info("Gathering from /dev/hwrng - process started.")
        if READ_RAND_PI:
            self.logger.info("Gathering from RandPi server - starting ...")
            self.gather_rand_pi_process = Process(target=self.read_rand_pi, args=(self.q,))
            self.gather_rand_pi_process.daemon = True
            self.gather_rand_pi_process.start()
            with open(self.pidfile, 'a') as pid_file:
                pid_file.write("%s\n" % self.gather_rand_pi_process.pid)
            self.logger.info("Gathering from RandPi server - process started.")
        self.logger.info("Startup finished.")
        while True:
            try:
                pipe = os.open(self.device, os.O_WRONLY)
                while True:
                    os.write(pipe, self.q.get())
            except BrokenPipeError:
                self.logger.info("Reader stopped reading from " + self.device)
            finally:
                try:
                    os.close(pipe)
                except OSError:
                    pass

    def __del__(self):
        if self.gather_hwrng_process and self.gather_hwrng_process.is_alive():
            self.gather_hwrng_process.join()
        if self.gather_rand_pi_process and self.gather_rand_pi_process.is_alive():
            self.gather_rand_pi_process.join()

    def stop(self, is_restart=False):
        if os.path.exists(self.device):
            os.remove(self.device)
        super().stop(is_restart)


if __name__ == '__main__':
    logger = logging.getLogger("RnGatherD")
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(os.path.join(os.path.sep, "var", "log", "rngatherd.log"))
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    rn_gather_d = RnGatherD(logger)

    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            rn_gather_d.start()
        elif 'stop' == sys.argv[1]:
            rn_gather_d.stop()
        elif 'restart' == sys.argv[1]:
            rn_gather_d.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)
