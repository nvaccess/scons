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
Test various uses of the -c (clean) option.
"""

import os

import TestSCons

_python_ = TestSCons._python_

test = TestSCons.TestSCons()

test.write('build.py', r"""
import sys
contents = open(sys.argv[2], 'rb').read()
file = open(sys.argv[1], 'wb')
file.write(contents)
file.close()
""")

test.write('SConstruct', """
B = Builder(action = r'%(_python_)s build.py $TARGETS $SOURCES')
env = Environment(BUILDERS = { 'B' : B })
env.B(target = 'foo1.out', source = 'foo1.in')
env.B(target = 'foo2.out', source = 'foo2.xxx')
env.B(target = 'foo2.xxx', source = 'foo2.in')
env.B(target = 'foo3.out', source = 'foo3.in')
env.B(target = 'foo4.out', source = 'foo4.in')
env.NoClean('foo4.out')
import os
if hasattr(os, 'symlink'):
    def symlink1(env, target, source):
        # symlink to a file that exists
        os.symlink(str(source[0]), str(target[0]))
    env.Command(target = 'symlink1', source = 'foo1.in', action = symlink1)
    def symlink2(env, target, source):
        # force symlink to a file that doesn't exist
        os.symlink('does_not_exist', str(target[0]))
    env.Command(target = 'symlink2', source = 'foo1.in', action = symlink2)
# Test handling of Builder calls that have multiple targets.
env.Command(['touch1.out', 'touch2.out'],
            [],
            [Touch('${TARGETS[0]}'), Touch('${TARGETS[1]}')])
""" % locals())

test.write('foo1.in', "foo1.in\n")

test.write('foo2.in', "foo2.in\n")

test.write('foo3.in', "foo3.in\n")

test.write('foo4.in', "foo4.in\n")

test.run(arguments = 'foo1.out foo2.out foo3.out foo4.out')

test.must_match(test.workpath('foo1.out'), "foo1.in\n")
test.must_match(test.workpath('foo2.xxx'), "foo2.in\n")
test.must_match(test.workpath('foo2.out'), "foo2.in\n")
test.must_match(test.workpath('foo3.out'), "foo3.in\n")
test.must_match(test.workpath('foo4.out'), "foo4.in\n")

test.run(arguments = '-c foo1.out',
         stdout = test.wrap_stdout("Removed foo1.out\n", cleaning=1))

test.must_not_exist(test.workpath('foo1.out'))
test.must_exist(test.workpath('foo2.xxx'))
test.must_exist(test.workpath('foo2.out'))
test.must_exist(test.workpath('foo3.out'))
test.must_exist(test.workpath('foo4.out'))

test.run(arguments = '--clean foo2.out foo2.xxx',
         stdout = test.wrap_stdout("Removed foo2.xxx\nRemoved foo2.out\n",
                                   cleaning=1))

test.must_not_exist(test.workpath('foo1.out'))
test.must_not_exist(test.workpath('foo2.xxx'))
test.must_not_exist(test.workpath('foo2.out'))
test.must_exist(test.workpath('foo3.out'))
test.must_exist(test.workpath('foo4.out'))

test.run(arguments = '--remove foo3.out',
         stdout = test.wrap_stdout("Removed foo3.out\n", cleaning=1))

test.must_not_exist(test.workpath('foo1.out'))
test.must_not_exist(test.workpath('foo2.xxx'))
test.must_not_exist(test.workpath('foo2.out'))
test.must_not_exist(test.workpath('foo3.out'))
test.must_exist(test.workpath('foo4.out'))

test.run(arguments = '.')

test.must_match(test.workpath('foo1.out'), "foo1.in\n")
test.must_match(test.workpath('foo2.xxx'), "foo2.in\n")
test.must_match(test.workpath('foo2.out'), "foo2.in\n")
test.must_match(test.workpath('foo3.out'), "foo3.in\n")
test.must_match(test.workpath('foo3.out'), "foo3.in\n")
test.must_match(test.workpath('foo4.out'), "foo4.in\n")
test.must_exist(test.workpath('touch1.out'))
test.must_exist(test.workpath('touch2.out'))

if hasattr(os, 'symlink'):
    test.fail_test(not os.path.islink(test.workpath('symlink1')))
    test.fail_test(not os.path.islink(test.workpath('symlink2')))

test.run(arguments = '-c foo2.xxx',
         stdout = test.wrap_stdout("Removed foo2.xxx\n", cleaning=1))

test.must_match(test.workpath('foo1.out'), "foo1.in\n")
test.must_not_exist(test.workpath('foo2.xxx'))
test.must_match(test.workpath('foo2.out'), "foo2.in\n")
test.must_match(test.workpath('foo3.out'), "foo3.in\n")
test.must_match(test.workpath('foo4.out'), "foo4.in\n")
test.must_exist(test.workpath('touch1.out'))
test.must_exist(test.workpath('touch2.out'))

test.run(arguments = '-c .')

test.must_not_exist(test.workpath('foo1.out'))
test.must_not_exist(test.workpath('foo2.out'))
test.must_not_exist(test.workpath('foo3.out'))
test.must_exist(test.workpath('foo4.out'))
test.must_not_exist(test.workpath('touch1.out'))
test.must_not_exist(test.workpath('touch2.out'))

if hasattr(os, 'symlink'):
    test.fail_test(os.path.islink(test.workpath('symlink1')))
    test.fail_test(os.path.islink(test.workpath('symlink2')))

args = 'foo1.out foo2.out foo3.out touch1.out'

expect = test.wrap_stdout("""\
Removed foo1.out
Removed foo2.xxx
Removed foo2.out
Removed foo3.out
Removed touch1.out
Removed touch2.out
""", cleaning=1)

test.run(arguments = args)

test.run(arguments = '-c -n ' + args, stdout = expect)

test.run(arguments = '-n -c ' + args, stdout = expect)

test.must_match(test.workpath('foo1.out'), "foo1.in\n")
test.must_match(test.workpath('foo2.xxx'), "foo2.in\n")
test.must_match(test.workpath('foo2.out'), "foo2.in\n")
test.must_match(test.workpath('foo3.out'), "foo3.in\n")
test.must_match(test.workpath('foo4.out'), "foo4.in\n")
test.must_exist(test.workpath('touch1.out'))
test.must_exist(test.workpath('touch2.out'))


expect1 = "scons: Could not remove 'foo1.out': Permission denied\n"
expect2 = "scons: Could not remove 'foo1.out': The process cannot access the file because it is being used by another process\n"

expect = [
    test.wrap_stdout(expect1, cleaning=1),
    test.wrap_stdout(expect2, cleaning=1),
]

test.writable('.', 0)
f = open(test.workpath('foo1.out'))
test.run(arguments = '-c foo1.out')
stdout = test.stdout()
matched = None
for e in expect:
    if stdout == e:
        matched = 1
        break
if not matched:
    print stdout
    test.fail_test()
test.must_exist(test.workpath('foo1.out'))
f.close()
test.writable('.', 1)

test.subdir('subd')
test.write(['subd', 'foon.in'], "foon.in\n")
test.write(['subd', 'foox.in'], "foox.in\n")
test.write('aux1.x', "aux1.x\n")
test.write('aux2.x', "aux2.x\n")
test.write('SConstruct', """
B = Builder(action = r'%(_python_)s build.py $TARGETS $SOURCES')
env = Environment(BUILDERS = { 'B' : B }, FOO = 'foo2')
env.B(target = 'foo1.out', source = 'foo1.in')
env.B(target = 'foo2.out', source = 'foo2.xxx')
foo2_xxx = env.B(target = 'foo2.xxx', source = 'foo2.in')
env.B(target = 'foo3.out', source = 'foo3.in')
SConscript('subd/SConscript')
Clean(foo2_xxx, ['aux1.x'])
env.Clean(['${FOO}.xxx'], ['aux2.x'])
Clean('.', ['subd'])
""" % locals())

test.write(['subd', 'SConscript'], """
Clean('.', 'foox.in')
""")

expect = test.wrap_stdout("""Removed foo2.xxx
Removed aux1.x
Removed aux2.x
""", cleaning=1)
test.run(arguments = '-c foo2.xxx', stdout=expect)
test.must_match(test.workpath('foo1.out'), "foo1.in\n")
test.must_not_exist(test.workpath('foo2.xxx'))
test.must_match(test.workpath('foo2.out'), "foo2.in\n")
test.must_match(test.workpath('foo3.out'), "foo3.in\n")

expect = test.wrap_stdout("Removed %s\n" % os.path.join('subd', 'foox.in'),
                          cleaning = 1)
test.run(arguments = '-c subd', stdout=expect)
test.must_not_exist(test.workpath('foox.in'))

expect = test.wrap_stdout("""Removed foo1.out
Removed foo2.xxx
Removed foo2.out
Removed foo3.out
Removed %s
Removed %s
Removed directory subd
""" % (os.path.join('subd','SConscript'), os.path.join('subd', 'foon.in')),
                          cleaning = 1)
test.run(arguments = '-c -n .', stdout=expect)

expect = test.wrap_stdout("""Removed foo1.out
Removed foo2.out
Removed foo3.out
Removed %s
Removed %s
Removed directory subd
""" % (os.path.join('subd','SConscript'), os.path.join('subd', 'foon.in')),
                          cleaning = 1)
test.run(arguments = '-c .', stdout=expect)
test.must_not_exist(test.workpath('subdir', 'foon.in'))
test.must_not_exist(test.workpath('subdir'))


# Ensure that Set/GetOption('clean') works correctly:
test.write('SConstruct', """
B = Builder(action = r'%(_python_)s build.py $TARGETS $SOURCES')
env = Environment(BUILDERS = { 'B' : B })
env.B(target = 'foo.out', source = 'foo.in')

assert not GetOption('clean')
""" % locals())

test.write('foo.in', '"Foo", I say!\n')

test.run(arguments='foo.out')
test.must_match(test.workpath('foo.out'), '"Foo", I say!\n')

test.write('SConstruct', """
B = Builder(action = r'%(_python_)s build.py $TARGETS $SOURCES')
env = Environment(BUILDERS = { 'B' : B })
env.B(target = 'foo.out', source = 'foo.in')

assert GetOption('clean')
SetOption('clean', 0)
assert GetOption('clean')
""" % locals())

test.run(arguments='-c foo.out')
test.must_not_exist(test.workpath('foo.out'))

test.write('SConstruct', """
B = Builder(action = r'%(_python_)s build.py $TARGETS $SOURCES')
env = Environment(BUILDERS = { 'B' : B })
env.B(target = 'foo.out', source = 'foo.in')
""" % locals())

test.run(arguments='foo.out')
test.must_match(test.workpath('foo.out'), '"Foo", I say!\n')

test.write('SConstruct', """
B = Builder(action = r'%(_python_)s build.py $TARGETS $SOURCES')
env = Environment(BUILDERS = { 'B' : B })
env.B(target = 'foo.out', source = 'foo.in')

assert not GetOption('clean')
SetOption('clean', 1)
assert GetOption('clean')
""" % locals())

test.run(arguments='foo.out')
test.must_not_exist(test.workpath('foo.out'))

test.pass_test()


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
