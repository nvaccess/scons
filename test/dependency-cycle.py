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

__revision__ = "test/dependency-cycle.py __REVISION__ __DATE__ __DEVELOPER__"

import TestSCons
import TestCmd

test = TestSCons.TestSCons(match = TestCmd.match_re)

test.write('SConstruct', """
env = Environment()
foo1 = env.Library(target = 'foo1', source = 'f1.c')
foo2 = env.Library(target = 'foo2', source = 'f1.c')
foo3 = env.Library(target = 'foo3', source = 'f1.c')
env.Depends(foo1, foo2)
env.Depends(foo2, foo3)
env.Depends(foo3, foo1)
""")

test.write('f1.c', r"""
void
f1(void)
{
        printf("f1.c\n");
} 
""")

test.run(arguments = ".", stderr=r"""
SCons error: Dependency cycle: .*foo1.* -> .*foo3.* -> .*foo2.* -> .*foo1.* -> \.
.*
""", status=2)

test.fail_test(test.stdout() == "")


test.pass_test()


