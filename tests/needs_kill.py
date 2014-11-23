#!/usr/bin/env python
"""This script can only be killed by SIGKILL."""
import signal
import time

# Ignore interrupt, hangup and continue signals - only SIGKILL will work
signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)
signal.signal(signal.SIGTERM, signal.SIG_IGN)

print('READY')
time.sleep(60)
