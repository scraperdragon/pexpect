
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
from __future__ import print_function

import contextlib
import unittest
import signal
import sys
import os

class PexpectTestCase(unittest.TestCase):
    def setUp(self):
        self.PYTHONBIN = sys.executable
        self.original_path = os.getcwd()
        tests_dir = os.path.dirname(__file__)
        self.project_dir = project_dir = os.path.dirname(tests_dir)
        os.chdir(tests_dir)
        self.pid = os.getpid()
        os.environ['COVERAGE_PROCESS_START'] = os.path.join(project_dir, '.coveragerc')
        os.environ['COVERAGE_FILE'] = os.path.join(project_dir, '.coverage')
        print('\n', self.id(), end=' ')
        sys.stdout.flush()

        # If the test runner has chosen to ignore SIGHUP (as on Fedora's
        # build machines), we must temporarily set it for the default handler
        # for our test cases.  We will restore ignoring SIGHUP on tearDown.
        self.restore_sig_ign = (
            signal.getsignal(signal.SIGHUP) == signal.SIG_IGN)
        if self.restore_sig_ign:
            signal.signal(signal.SIGHUP, signal.SIG_DFL)
            self.restore_sig_ign = True

        unittest.TestCase.setUp(self)

    def tearDown(self):
        os.chdir (self.original_path)
        if self.restore_sig_ign:
            # return ignoring signal handler for our test runner
            signal.signal(signal.SIGHUP, signal.SIG_IGN)

        if self.pid != os.getpid():
            print('Test runner has forked! Exiting', file=sys.stderr)
            sys.exit(1)

    if sys.version_info < (2,7):
        # We want to use these methods, which are new/improved in 2.7, but
        # we are still supporting 2.6 for the moment. This section can be
        # removed when we drop Python 2.6 support.
        @contextlib.contextmanager
        def assertRaises(self, excClass):
            try:
                yield
            except Exception as e:
                assert isinstance(e, excClass)
            else:
                raise AssertionError("%s was not raised" % excClass)

        @contextlib.contextmanager
        def assertRaisesRegexp(self, excClass, pattern):
            import re
            try:
                yield
            except Exception as e:
                assert isinstance(e, excClass)
                assert re.match(pattern, str(e))
            else:
                raise AssertionError("%s was not raised" % excClass)
