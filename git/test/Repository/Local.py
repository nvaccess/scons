#!/usr/bin/env python
#
# Copyright (c) 2001, 2002 Steven Knight
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

import os.path
import sys
import TestSCons

test = TestSCons.TestSCons()

test.subdir('repository', 'work')

work_aaa_mid = test.workpath('work', 'aaa.mid')
work_aaa_out = test.workpath('work', 'aaa.out')

opts = "-Y " + test.workpath('repository')

#
test.write(['repository', 'SConstruct'], r"""
def copy(env, source, target):
    source = str(source[0])
    target = str(target[0])
    print 'copy() < %s > %s' % (source, target)
    open(target, "wb").write(open(source, "rb").read())

Build = Builder(action=copy)
env = Environment(BUILDERS={'Build':Build})
env.Build('aaa.mid', 'aaa.in')
env.Build('aaa.out', 'aaa.mid')
Local('aaa.out')
""")

test.write(['repository', 'aaa.in'], "repository/aaa.in\n")

#
test.run(chdir = 'repository', options = opts, arguments = '.')

# Make the entire repository non-writable, so we'll detect
# if we try to write into it accidentally.
test.writable('repository', 0)

test.up_to_date(chdir = 'repository', options = opts, arguments = '.')

#
test.run(chdir = 'work', options = opts, arguments = '.')

test.fail_test(os.path.exists(work_aaa_mid))
test.fail_test(test.read(work_aaa_out) != "repository/aaa.in\n")

#
test.write(['work', 'aaa.in'], "work/aaa.in\n")

#
test.run(chdir = 'work', options = opts, arguments = '.')

test.fail_test(test.read(work_aaa_mid) != "work/aaa.in\n")
test.fail_test(test.read(work_aaa_out) != "work/aaa.in\n")

test.up_to_date(chdir = 'work', options = opts, arguments = '.')

#
test.pass_test()
