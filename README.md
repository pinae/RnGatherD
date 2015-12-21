RnGatherD
=========

Random number gathering daemon.

While running the daemon creates a pseudo device /dev/hwrandom which can be used as input device for rngd. The daemon
supports reading from a local device or loads the random data from a [RandPi](https://github.com/pinae/RandPi) entropy 
server. If reading from the server the daemon decrypts the random data and checks the signature. You have to use the 
same secret and salt on the server and the client.

Installation
------------

You can install the daemon via pip: `pip3 install rngatherd`

You can also checkout this repository and run `python3 setup.py install`.

Both methods install the script `rngatherdaemon.py` as a system wide executable and create a init script: 
`/etc/init.d/rngatherd`.

Configuration
-------------

Running `sudo rngatherdaemon.py config` creates a basic configuration in `/etc/rngatherd.conf`. You probably need
to change the `secret` and `salt` in the **[RandPi]** section to match the server. The encryption key is derived from 
these so the settings on server and all clients have to match.

If settings are missing default values are used. There has to be a **[Hwrng]** or a **[RandPi]** section to activate
at least one random source.

The daemon logs to `/var/vog/rngatherd.log`. The log level can be specified in the settings by choosing one of `ERROR`,
`WARN` or `INFO`.

Usage
-----

Just read from `/dev/hwrandom`.

You can test the daemon with `cat /dev/hwrandom`. This should produce a lot of weird looking output because most of
the random bytes are not printable.
