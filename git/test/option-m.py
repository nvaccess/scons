#!/usr/bin/env python

__revision__ = "test/option-m.py __REVISION__ __DATE__ __DEVELOPER__"

import TestSCons
import string
import sys

test = TestSCons.TestSCons()

test.write('SConstruct', "")

test.run(arguments = '-m')

test.fail_test(test.stderr() !=
		"Warning:  ignoring -m option\n")

test.pass_test()
 
