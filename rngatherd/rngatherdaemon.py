#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import sys
import time
import configparser
from multiprocessing import Process, Queue
from rngatherd.RandPi.RandPiClient import RandPiClient
from rngatherd.Daemon.BaseDaemon import BaseDaemon

READ_HWRNG = False
READ_RAND_PI = True


class RnGatherD(BaseDaemon):
    def __init__(self, initialized_logger):
        super().__init__(os.path.join(os.path.sep, "var", "run", "rngatherd.pid"))
        self.logger = initialized_logger
        self.logger.info("Initializing ...")
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(os.path.sep, "etc", "rngatherd.conf"))
        if "Settings" in self.config.sections():
            self.device = self.config['Settings'].get('Device', os.path.join(os.path.sep, "dev", "hwrandom"))
            queue_size = int(self.config['Settings'].get('QueueSize', '1024'))
        else:
            self.device = os.path.join(os.path.sep, "dev", "hwrandom")
            queue_size = 1024
        self.logger.info("Writing to " + self.device)
        self.q = Queue(queue_size)
        self.gather_hwrng_process = None
        self.gather_rand_pi_process = None
        self.use_hwrng = False
        self.use_rand_pi = False
        if "Hwrng" in self.config.sections():
            self.hwrng_device = self.config['Hwrng'].get('Device', os.path.join(os.path.sep, "dev", "hwrng"))
            try:
                self.hwrng_bytes = int(self.config['Hwrng'].get('Bytes', '8'))
            except ValueError:
                self.logger.error("Invalid bytes length. Setting to 8 instead.")
                self.hwrng_bytes = 8
            if self.hwrng_bytes <= 0:
                self.logger.error("Invalid bytes length: " + str(self.hwrng_bytes) + ". Setting to 8 instead.")
                self.hwrng_bytes = 8
            self.use_hwrng = True
        if "RandPi" in self.config.sections():
            self.rand_pi_url = self.config['RandPi'].get('Url', 'http://127.0.0.1/entropy/random')
            self.rand_pi_secret = self.config['RandPi'].get('Secret', '123456')
            self.rand_pi_salt = self.config['RandPi'].get('Salt', 'pepper')
            try:
                self.rand_pi_bytes = int(self.config['RandPi'].get('Bytes', '1024'))
            except ValueError:
                self.logger.error("Invalid bytes length. Setting to 1024 instead.")
                self.rand_pi_bytes = 1024
            if self.rand_pi_bytes <= 0:
                self.logger.error("Invalid bytes length: " + str(self.rand_pi_bytes) + ". Setting to 1024 instead.")
                self.rand_pi_bytes = 1024
            self.use_rand_pi = True
        if not (self.use_hwrng or self.use_rand_pi):
            print("No Random Source specified. Define a [Hwrng] or [RandPi] section in /etc/rngatherd.conf.")
            exit(1)

    @staticmethod
    def read_hwrng(device, length, q):
        while True:
            if q.full():
                time.sleep(0.1)
            else:
                with open(device, 'rb') as hwrng:
                    q.put(hwrng.read(length))

    @staticmethod
    def read_rand_pi(url, secret, salt, length, q):
        client = RandPiClient(url, secret, salt)
        while True:
            if q.full():
                time.sleep(1)
            else:
                random_data = client.get_random(length)
                if len(random_data) == length:
                    for i in range((length//8)-1):
                        q.put(random_data[i*8:(i+1)*8])
                else:
                    time.sleep(1)

    def run(self):
        if not os.path.exists(self.device):
            os.mkfifo(self.device)
        if self.use_hwrng:
            self.gather_hwrng_process = Process(target=self.read_hwrng, args=(
                self.hwrng_device,
                self.hwrng_bytes,
                self.q,
            ))
            self.gather_hwrng_process.daemon = True
            self.gather_hwrng_process.start()
            with open(self.pidfile, 'a') as pid_file:
                pid_file.write("%s\n" % self.gather_hwrng_process.pid)
            self.logger.info("Gathering from " + self.hwrng_device + " - process started.")
        if self.use_rand_pi:
            self.logger.info("Gathering from RandPi server - starting ...")
            self.gather_rand_pi_process = Process(target=self.read_rand_pi, args=(
                self.rand_pi_url,
                self.rand_pi_secret,
                self.rand_pi_salt,
                self.rand_pi_bytes,
                self.q,
            ))
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


def make_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.sep, "etc", "rngatherd.conf"))
    if "Settings" not in config.sections():
        config['Settings'] = {
            "Device": os.path.join(os.path.sep, "dev", "hwrandom"),
            "QueueSize": str(1024)
        }
    if "Hwrng" not in config.sections() and os.path.exists(os.path.join(os.path.sep, "dev", "hwrng")):
        config['Hwrng'] = {
            "Device": os.path.join(os.path.sep, "dev", "hwrng"),
            "Bytes": str(8)
        }
    if "RandPi" not in config.sections():
        server_url = input("Url of the RandPi server (Empty if you do not want to use one):")
        if len(server_url) > 0:
            config['RandPi'] = {
                "Url": server_url,
                "Secret": "123456",
                "Salt": "pepper",
                "Bytes": str(1024)
            }
    with open(os.path.join(os.path.sep, "etc", "rngatherd.conf"), 'w') as configfile:
        config.write(configfile)


def get_logger():
    logger = logging.getLogger("RnGatherD")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(os.path.join(os.path.sep, "var", "log", "rngatherd.log"))
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def main():
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            rn_gather_d = RnGatherD(get_logger())
            rn_gather_d.start()
        elif 'stop' == sys.argv[1]:
            rn_gather_d = RnGatherD(get_logger())
            rn_gather_d.stop()
        elif 'restart' == sys.argv[1]:
            rn_gather_d = RnGatherD(get_logger())
            rn_gather_d.restart()
        elif 'config' == sys.argv[1]:
            make_config()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)


if __name__ == '__main__':
    main()
