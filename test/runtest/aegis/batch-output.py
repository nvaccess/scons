#!/usr/bin/env python
#
# __COPYRIGHT__
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

"""
Test writing Aegis batch output to a file.
"""

import os

import TestRuntest

test_fail_py = os.path.join('test', 'fail.py')
test_no_result_py = os.path.join('test', 'no_result.py')
test_pass_py = os.path.join('test', 'pass.py')

test = TestRuntest.TestRuntest()

test.subdir('test')

test.write_failing_test(['test', 'fail.py'])

test.write_no_result_test(['test', 'no_result.py'])

test.write_passing_test(['test', 'pass.py'])

expect_stderr = """\
FAILING TEST STDERR
NO RESULT TEST STDERR
PASSING TEST STDERR
"""

test.run(arguments = '-k -o aegis.out --aegis test', stderr=expect_stderr)

expect = """\
test_result = [
    { file_name = "%(test_fail_py)s";
      exit_status = 1; },
    { file_name = "%(test_no_result_py)s";
      exit_status = 2; },
    { file_name = "%(test_pass_py)s";
      exit_status = 0; },
];
""" % locals()

# The mode is 'r' (not default 'rb') because QMTest opens the file
# description on which we write as non-binary.
test.must_match('aegis.out', expect, mode='r')

test.pass_test()

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
