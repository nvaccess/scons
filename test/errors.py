#!/usr/bin/env python

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import TestSCons

test = TestSCons.TestSCons()

test.write('SConstruct1', """
a ! x
""")

test.run(arguments='-f SConstruct1', stderr = """  File "SConstruct1", line 2

    a ! x

      \^

SyntaxError: invalid syntax

""")


test.write('SConstruct2', """
raise UserError, 'Depends() require both sources and targets.'
""")
test.run(arguments='-f SConstruct2', stderr = """
SCons error: Depends\(\) require both sources and targets.
File "SConstruct2", line 2, in \?
""")

test.write('SConstruct3', """
raise InternalError, 'error inside'
""")
test.run(arguments='-f SConstruct3', stderr = r"""Traceback \((most recent call|innermost) last\):
  File ".*scons", line \d+, in \?
    main\(\)
  File ".*scons", line \d+, in main
    exec f in globals\(\)
  File "SConstruct3", line \d+, in \?
    raise InternalError, 'error inside'
InternalError: error inside
""")

test.pass_test()
