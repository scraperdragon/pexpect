#!/usr/bin/env python
'''
PEXPECT LICENSE

    This license is approved by the OSI and FSF as GPL-compatible.
        http://opensource.org/licenses/isc-license.txt

    Copyright (c) 2012, Noah Spurrier <noah@noah.org>
    PERMISSION TO USE, COPY, MODIFY, AND/OR DISTRIBUTE THIS SOFTWARE FOR ANY
    PURPOSE WITH OR WITHOUT FEE IS HEREBY GRANTED, PROVIDED THAT THE ABOVE
    COPYRIGHT NOTICE AND THIS PERMISSION NOTICE APPEAR IN ALL COPIES.
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

'''
from __future__ import division
import pexpect
import unittest
import signal
import time
import sys
import os
import re

from . import PexpectTestCase


class WaitTestCase(PexpectTestCase.PexpectTestCase):

    """ Test cases for wait() method of spawn. """

    def test_wait(self):
        """ Call wait() on a process that sleeps and exits 0. """
        given_command = 'sleep 1'
        expected_isalive = False
        expected_exitstatus = 0
        expected_duration_floor, expected_duration_ceil = 0.9, 2.5

        # given,
        proc = pexpect.spawn(given_command)
        _stime = time.time()

        # exercise,
        assert proc.wait() == expected_exitstatus

        # verify
        duration = time.time() - _stime
        assert expected_duration_floor < duration < expected_duration_ceil
        assert proc.isalive() == expected_isalive

    def test_wait_after_eof(self):
        """ Exception thrown when calling wait() on a terminated process. """
        # given,
        given_command = 'cat'
        given_expect_pattern = 'READY'
        expected_exception = pexpect.ExceptionPexpect

        # exercise,
        proc = pexpect.spawn(given_command, echo=False)
        proc.sendline(given_expect_pattern)
        proc.expect(given_expect_pattern)
        proc.kill(signal.SIGKILL) # kill -9
        proc.expect(pexpect.EOF)

        # verify
        with self.assertRaises(expected_exception):
            proc.wait()

    @unittest.skipIf(not hasattr(signal, 'SIGALRM'),
                     "Cannot test for SIGARLM.")
    def test_signal_wait(self):
        """ signalstatus set by wait() when child dies by signal. """
        if not hasattr(signal, 'SIGALRM'):
            return 'SKIP'

        # given,
        given_command = ('{0} alarm_die.py'.format(sys.executable))
        expected_signal = signal.SIGALRM

        # exercise,
        proc = pexpect.spawn(given_command)
        proc.wait()

        # verify
        assert proc.exitstatus is None
        assert proc.signalstatus == expected_signal


class IsAliveTestCase(PexpectTestCase.PexpectTestCase):

    """ Test cases for isalive() method of spawn. """

    def test_isalive_true(self):
        """ a running child command tests True for isalive(). """
        # given,
        given_command = 'cat'
        expected_alive = True
        expected_terminated = False

        # exercise
        proc = pexpect.spawn(given_command)

        # verify,
        assert proc.isalive() == expected_alive
        assert proc.terminated == expected_terminated

    def test_isalive_false_after_eof(self):
        """ after EOF is expected, isalive() tests False. """
        # given,
        given_command = 'id'
        given_expect_pattern = pexpect.EOF
        expected_alive = False
        expected_exitstatus = 0
        expected_terminated = True

        # exercise
        proc = pexpect.spawn(given_command)
        proc.expect(given_expect_pattern)

        # verify,
        assert proc.isalive() == expected_alive
        assert proc.exitstatus == expected_exitstatus
        assert proc.terminated == expected_terminated

    def test_expect_isalive_true_many_calls(self):
        """ Multiple calls to isalive() returns True. """
        # given,
        given_command = 'cat'
        expected_alive = True

        # exercise,
        proc = pexpect.spawn(given_command)

        # verify
        assert proc.isalive() == expected_alive
        assert proc.isalive() == expected_alive

    def test_expect_isalive_false_many_calls(self):
        """ Multiple calls to isalive() after SIGKILL returns False. """
        # given,
        given_command = 'cat'
        given_expect_pattern = 'READY'
        expected_alive = False

        # exercise,
        proc = pexpect.spawn(given_command, echo=False)
        proc.sendline(given_expect_pattern)
        proc.expect(given_expect_pattern)
        proc.kill(9)
        proc.expect(pexpect.EOF)

        # verify
        assert proc.isalive() == expected_alive
        assert proc.isalive() == expected_alive

    def test_sighup_ignored(self):
        """ SIGHUP is ignored by default, remaining alive. """
        # given,
        given_command = 'cat'
        given_expect_pattern = 'READY'
        given_expect_pattern2 = [pexpect.EOF, pexpect.TIMEOUT]
        expected_expect_result = 1
        expected_alive = True
        expected_terminated = False

        # exercise,
        proc = pexpect.spawn(given_command, echo=False)
        proc.sendline(given_expect_pattern)
        proc.expect(given_expect_pattern)
        proc.kill(signal.SIGHUP)
        expect_result = proc.expect(given_expect_pattern2, timeout=1)

        # verify,
        assert expect_result == expected_expect_result
        assert proc.isalive() == expected_alive
        assert proc.terminated == expected_terminated

    def test_someone_else_called_waitpid(self):
        " assert bad condition error in isalive(). "
        given_command = 'echo'
        expected_errmsg = '.*{0}'.format(re.escape(
            'Did someone else call waitpid() on our process?'))

        proc = pexpect.spawn(given_command)
        os.waitpid(proc.pid, 0)
        with self.assertRaisesRegexp(pexpect.ExceptionPexpect,
                                     expected_errmsg):
            proc.isalive()


class TerminateTestCase(PexpectTestCase.PexpectTestCase):
    """ Test cases for terminate() method of spawn. """

    def test_default_terminate_by_sigint(self):
        """ terminate() should succeed by SIGINT by default. """
        # given,
        given_command = 'cat'
        given_expect_pattern = 'READY'
        expected_result = True
        expected_alive = False
        expected_exitstatus = None
        expected_signalstatuses = (signal.SIGINT,)

        # exercise,
        proc = pexpect.spawn(given_command, echo=False)
        proc.sendline(given_expect_pattern)
        proc.expect(given_expect_pattern)
        termination_result = proc.terminate()

        # verify,
        assert termination_result == expected_result
        assert proc.isalive() == expected_alive
        assert proc.exitstatus == expected_exitstatus
        assert proc.signalstatus in expected_signalstatuses

    @unittest.skipIf(pexpect.which('mailx') is None,
                     "Requires Heirloom mailx(1) derived from Berkeley Mail")
    def test_some_may_terminate_by_sigterm(self):
        """ terminate() may succeed by SIGTERM if child ignores SIGINT. """
        # mail(1) will NOT exit on ^C.  Instead, it will read:
        # (Interrupt -- one more to kill letter), ending on SIGTERM.

        # given,
        given_command = 'mailx pexpect@example.com'
        given_expect_pattern = 'ubject:'
        expected_result = True
        expected_alive = False
        expected_exitstatus = None
        expected_signalstatuses = (signal.SIGTERM,)

        # exercise,
        proc = pexpect.spawn(given_command)
        proc.expect(given_expect_pattern)
        termination_result = proc.terminate()

        # verify,
        assert termination_result == expected_result
        assert proc.isalive() == expected_alive
        assert proc.exitstatus == expected_exitstatus
        assert proc.signalstatus in expected_signalstatuses

    def test_may_terminate_by_sighup(self):
        """ terminate() may optionally succeed by SIGHUP.  """
        # given,
        given_command = 'cat'
        given_expect_pattern = 'READY'
        expected_result = True
        expected_alive = False
        expected_exitstatus = None
        expected_signalstatuses = (signal.SIGHUP,)

        # exercise,
        proc = pexpect.spawn(given_command, ignore_sighup=False, echo=False)
        proc.sendline(given_expect_pattern)
        proc.expect(given_expect_pattern)
        termination_result = proc.terminate()

        # verify,
        assert termination_result == expected_result
        assert proc.isalive() == expected_alive
        assert proc.exitstatus == expected_exitstatus
        assert proc.signalstatus in expected_signalstatuses

    def test_terminate_force_not_necessary(self):
        """ terminate() by force shouldn't have to. """
        # given,
        given_command = 'cat'
        given_expect_pattern = 'READY'
        expected_result = True
        expected_alive = False
        expected_signalstatuses = (signal.SIGINT,)

        # exercise,
        proc = pexpect.spawn(given_command, echo=False)
        proc.sendline(given_expect_pattern)
        proc.expect(given_expect_pattern)
        termination_result = proc.terminate(force=True)

        # verify,
        assert termination_result == expected_result
        assert proc.isalive() == expected_alive
        assert proc.signalstatus in expected_signalstatuses

    def test_soft_terminate_may_fail(self):
        """ terminate() fails if SIGINT and SIGTERM are ignored by process. """
        # given,
        given_command = '{0} needs_kill.py'.format(sys.executable)
        given_expect_pattern = 'READY'
        expected_result = False
        expected_alive = True

        # exercise,
        proc = pexpect.spawn(given_command)
        proc.sendline(given_expect_pattern)
        proc.expect(given_expect_pattern)
        termination_result = proc.terminate()

        # verify,
        assert termination_result == expected_result
        assert proc.isalive() == expected_alive

    def test_terminate_force_if_necessary(self):
        """ terminate() a child process that ignores SIGINT and SIGTERM. """
        # given,
        given_command = '{0} needs_kill.py'.format(sys.executable)
        given_expect_pattern = 'READY'
        expected_result = True
        expected_alive = False
        expected_signalstatuses = (signal.SIGKILL,)

        # exercise,
        proc = pexpect.spawn(given_command)
        proc.sendline(given_expect_pattern)
        proc.expect(given_expect_pattern)
        termination_result = proc.terminate(force=True)

        # verify,
        assert termination_result == expected_result
        assert proc.isalive() == expected_alive
        assert proc.signalstatus in expected_signalstatuses

if __name__ == '__main__':
    unittest.main()

suite = unittest.makeSuite(IsAliveTestCase, 'test')
