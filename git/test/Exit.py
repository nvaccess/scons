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
Test the explicit Exit() function.
"""

import TestSCons

test = TestSCons.TestSCons()

test.subdir('subdir')

test.write('SConstruct', """\
print "SConstruct"
Exit()
""")

test.run(stdout = """\
scons: Reading SConscript files ...
SConstruct
""")

test.write('SConstruct', """\
print "SConstruct"
Exit(7)
""")

test.run(status = 7, stdout = """\
scons: Reading SConscript files ...
SConstruct
""")

test.write('SConstruct', """\
print "SConstruct"
SConscript('subdir/SConscript')
""")

test.write(['subdir', 'SConscript'], """\
print "subdir/SConscript"
Exit()
""")

test.run(stdout = """\
scons: Reading SConscript files ...
SConstruct
subdir/SConscript
""")

test.write(['subdir', 'SConscript'], """\
print "subdir/SConscript"
Exit(17)
""")

test.run(status = 17, stdout = """\
scons: Reading SConscript files ...
SConstruct
subdir/SConscript
""")

test.write('SConstruct', """\
SConscript('subdir/SConscript')
""")

test.write(['subdir', 'SConscript'], """\
def exit_builder(env, source, target):
    target = str(target[0])
    source = map(str, source)
    f = open(target, "wb")
    for src in source:
        f.write(open(src, "rb").read())
    f.close()
    Exit(27)
env = Environment(BUILDERS = {'my_exit' : Builder(action=exit_builder)})
env.my_exit('foo.out', 'foo.in')
""")

test.write(['subdir', 'foo.in'], "subdir/foo.in\n")

test.run(status = 27,
         stdout = test.wrap_stdout("""\
exit_builder("subdir/foo.out", "subdir/foo.in")
"""),
         stderr = "scons: *** [subdir/foo.out] Explicit exit, status 27\n")

test.fail_test(test.read(['subdir', 'foo.out']) != "subdir/foo.in\n")

test.write('SConstruct', """\
def exit_scanner(node, env, target):
    Exit(37)

exitscan = Scanner(function = exit_scanner, skeys = ['.k'])

def cat(env, source, target):
    target = str(target[0])
    source = map(str, source)

    outf = open(target, 'wb')
    for src in source:
        outf.write(open(src, "rb").read())
    outf.close()

env = Environment(BUILDERS={'Cat':Builder(action=cat)})
env.Append(SCANNERS = [exitscan])

env.Cat('foo', 'foo.k')
""")

test.write('foo.k', "foo.k\n")

test.run(status = 37,
         stdout = test.wrap_stdout(""),
         stderr = "scons: *** [foo] Explicit exit, status 37\n")

#
test.pass_test()
