#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import atexit
from signal import SIGTERM, SIGKILL


class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self,
                 pidfile,
                 stdin=os.path.join(os.path.sep, "dev", "null"),
                 stdout=os.path.join(os.path.sep, "dev", "null"),
                 stderr=os.path.join(os.path.sep, "dev", "null")):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        with open(self.stdin, 'r') as si:
            os.dup2(si.fileno(), sys.stdin.fileno())
        with open(self.stdout, 'ab+') as so:
            os.dup2(so.fileno(), sys.stdout.fileno())
        with open(self.stderr, 'ab+', 0) as se:
            os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.del_pid)
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as pidfile:
            pidfile.write("%s\n" % pid)

    def del_pid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        pids = []
        try:
            with open(self.pidfile, 'r') as pf:
                for line in pf.readlines():
                    pids.append(int(line.strip()))
        except IOError:
            pass

        if len(pids) > 0:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self, is_restart=False):
        """
        Stop the daemon

        :param is_restart: True in case of a restart
        :type is_restart: bool
        """
        # Get the pids from the pidfile
        pids = []
        try:
            with open(self.pidfile, 'r') as pf:
                for line in pf.readlines():
                    pids.append(int(line.strip()))
        except IOError:
            pass

        if len(pids) <= 0:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            if is_restart:
                return  # not an error in a restart
            else:
                sys.exit(1)

        # Try killing the daemon process
        for pid in pids[1:]:
            os.kill(pid, SIGTERM)
        pid = pids[0]
        try:
            while True:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop(is_restart=True)
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
