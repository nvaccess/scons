#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import TestSCons

test = TestSCons.TestSCons()

test.write('SConstruct', "")

test.run(arguments = '-Q --tree=prune',
         stdout = """scons: `.' is up to date.
+-.
  +-SConstruct
""")

test.run(arguments = '-Q --tree=foofoo',
         stderr = """usage: scons [OPTION] [TARGET] ...

SCons Error: `foofoo' is not a valid --tree option type, try:
    all, derived, prune, status
""",
         status = 2)

test.run(arguments = '--debug=tree',
         stderr = """
scons: warning: The --debug=tree option is deprecated; please use --tree=all instead.
.*
""",
         status = 0, match=TestSCons.match_re_dotall)


# Check that printing nodes won't fail with
# UnicodeDecodeError: 'ascii' codec ... ordinal not in range(128)
# https://bitbucket.org/scons/scons/pull-request/235

test.write('SConstruct', """\
# -*- coding: utf-8 -*-

Entry('русский юникод')
""")

test.run(arguments = '-Q --tree=all')


test.pass_test()

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
