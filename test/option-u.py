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
Test that the -u option only builds targets at or below
the current directory.
"""

import os.path
import sys

import TestSCons

test = TestSCons.TestSCons()

test.subdir('sub1',
            'sub2', ['sub2', 'dir'],
            'sub3',
            'sub4', ['sub4', 'dir'])

test.write('SConstruct', """
def cat(env, source, target):
    target = str(target[0])
    source = map(str, source)
    f = open(target, "wb")
    for src in source:
        f.write(open(src, "rb").read())
    f.close()
env = Environment()
env.Append(BUILDERS = {'Cat' : Builder(action=cat)})
env.Cat(target = 'sub1/f1a.out', source = 'sub1/f1a.in')
env.Cat(target = 'sub1/f1b.out', source = 'sub1/f1b.in')
Export('env')
SConscript('sub2/SConscript')
f3 = env.Cat(target = 'sub3/f3.out', source = 'sub3/f3.in')
env.Alias('my_alias', f3)
BuildDir('build', 'sub4')
SConscript('build/SConscript')
""")

test.write(['sub2', 'SConscript'], """
Import('env')
env.Cat(target = 'f2a.out', source = 'f2a.in')
env.Cat(target = 'dir/f2b.out', source = 'dir/f2b.in')
""")

test.write(['sub4', 'SConscript'], """
Import('env')
env.Cat(target = 'f4a.out', source = 'f4a.in')
env.Cat(target = 'dir/f4b.out', source = 'dir/f4b.in')
""")

test.write(['sub1', 'f1a.in'], "sub1/f1a.in")
test.write(['sub1', 'f1b.in'], "sub1/f1b.in")
test.write(['sub2', 'f2a.in'], "sub2/f2a.in")
test.write(['sub2', 'dir', 'f2b.in'], "sub2/dir/f2b.in")
test.write(['sub3', 'f3.in'], "sub3/f3.in")
test.write(['sub4', 'f4a.in'], "sub4/f4a.in")
test.write(['sub4', 'dir', 'f4b.in'], "sub4/dir/f4b.in")

# Verify that we only build the specified local argument.
test.run(chdir = 'sub1', arguments = '-u f1a.out')

test.fail_test(test.read(['sub1', 'f1a.out']) != "sub1/f1a.in")
test.fail_test(os.path.exists(test.workpath('sub1', 'sub1/f1b.out')))
test.fail_test(os.path.exists(test.workpath('sub2', 'f2a.out')))
test.fail_test(os.path.exists(test.workpath('sub2', 'dir', 'f2b.out')))
test.fail_test(os.path.exists(test.workpath('sub3', 'f3.out')))
test.fail_test(os.path.exists(test.workpath('sub4', 'f4a.out')))
test.fail_test(os.path.exists(test.workpath('sub4', 'dir', 'f4b.out')))
test.fail_test(os.path.exists(test.workpath('build', 'f4a.out')))
test.fail_test(os.path.exists(test.workpath('build', 'dir', 'f4b.out')))

# Verify that we build everything at or below our current directory.
test.run(chdir = 'sub2', arguments = '-u')

test.fail_test(os.path.exists(test.workpath('sub1', 'sub1/f1b.out')))
test.fail_test(test.read(['sub2', 'f2a.out']) != "sub2/f2a.in")
test.fail_test(test.read(['sub2', 'dir', 'f2b.out']) != "sub2/dir/f2b.in")
test.fail_test(os.path.exists(test.workpath('sub3', 'f3.out')))
test.fail_test(os.path.exists(test.workpath('sub4', 'f4a.out')))
test.fail_test(os.path.exists(test.workpath('sub4', 'dir', 'f4b.out')))
test.fail_test(os.path.exists(test.workpath('build', 'f4a.out')))
test.fail_test(os.path.exists(test.workpath('build', 'dir', 'f4b.out')))

# Verify that we build a specified alias, regardless of where.
test.run(chdir = 'sub2', arguments = '-u my_alias')

test.fail_test(os.path.exists(test.workpath('sub1', 'sub1/f1b.out')))
test.fail_test(test.read(['sub3', 'f3.out']) != "sub3/f3.in")
test.fail_test(os.path.exists(test.workpath('sub4', 'f4a.out')))
test.fail_test(os.path.exists(test.workpath('sub4', 'dir', 'f4b.out')))
test.fail_test(os.path.exists(test.workpath('build', 'f4a.out')))
test.fail_test(os.path.exists(test.workpath('build', 'dir', 'f4b.out')))

# Verify that we build things in a linked BuildDir.
f4a_in = os.path.join('build', 'f4a.in')
f4a_out = os.path.join('build', 'f4a.out')
f4b_in = os.path.join('build', 'dir', 'f4b.in')
f4b_out = os.path.join('build', 'dir', 'f4b.out')
test.run(chdir = 'sub4',
         arguments = '-u',
         stdout = "scons: Entering directory %s\n" % test.workpath() + \
                  test.wrap_stdout("""\
scons: building associated BuildDir targets: build
cat("%s", "%s")
cat("%s", "%s")
""" % (f4b_out, f4b_in, f4a_out, f4a_in)))

test.fail_test(os.path.exists(test.workpath('sub1', 'sub1/f1b.out')))
test.fail_test(os.path.exists(test.workpath('sub4', 'f4a.out')))
test.fail_test(os.path.exists(test.workpath('sub4', 'dir', 'f4b.out')))
test.fail_test(test.read(['build', 'f4a.out']) != "sub4/f4a.in")
test.fail_test(test.read(['build', 'dir', 'f4b.out']) != "sub4/dir/f4b.in")

test.pass_test()
