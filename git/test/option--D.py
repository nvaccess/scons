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

import sys
import TestSCons
import os

python = sys.executable

test = TestSCons.TestSCons()

test.subdir('sub1', 'sub2')

test.write('build.py', r"""
import sys
contents = open(sys.argv[2], 'rb').read()
file = open(sys.argv[1], 'wb')
file.write(contents)
file.close()
""")

test.write('SConstruct', """
import SCons.Defaults
B = Builder(name='B', action='%s build.py $TARGET $SOURCES')
env = Environment(BUILDERS = [B, SCons.Defaults.Alias])
env.B(target = 'sub1/foo.out', source = 'sub1/foo.in')
Export('env')
SConscript('sub1/SConscript')
SConscript('sub2/SConscript')
""" % python)

test.write(['sub1', 'SConscript'], """
Import('env')
env.B(target = 'foo.out', source = 'foo.in')
Default('.')
""")

test.write(['sub1', 'foo.in'], "sub1/foo.in")

test.write(['sub2', 'SConscript'], """
Import('env')
env.Alias('bar', env.B(target = 'bar.out', source = 'bar.in'))
Default('.')

""")

test.write(['sub2', 'bar.in'], "sub2/bar.in")

test.run(arguments = '-D', chdir = 'sub1')

test.fail_test(test.read(['sub1', 'foo.out']) != "sub1/foo.in")
test.fail_test(test.read(['sub2', 'bar.out']) != "sub2/bar.in")

test.unlink(['sub1', 'foo.out'])
test.unlink(['sub2', 'bar.out'])

test.run(arguments = '-D bar', chdir = 'sub1')

test.fail_test(os.path.exists(test.workpath('sub1', 'foo.out')))
test.fail_test(not os.path.exists(test.workpath('sub2', 'bar.out')))



test.pass_test()

