__revision__ = "EnivronmentTests.py __REVISION__ __DATE__ __DEVELOPER__"

import sys
import unittest

from scons.Environment import *



built_it = {}

class Builder:
    """A dummy Builder class for testing purposes.  "Building"
    a target is simply setting a value in the dictionary.
    """
    def __init__(self, name = None):
    	self.name = name

    def execute(self, target = None, source = None):
	built_it[target] = 1



class EnvironmentTestCase(unittest.TestCase):

    def test_Builders(self):
	"""Test the ability to execute simple builders through
	different environment, one initialized with a single
	Builder object, one with a list of a single Builder
	object, and one with a list of two Builder objects.
	"""
	global built_it

	b1 = Builder(name = 'builder1')
	b2 = Builder(name = 'builder2')

	built_it = {}
	env1 = Environment(BUILDERS = b1)
	env1.builder1.execute(target = 'out1')
	assert built_it['out1']

	built_it = {}
	env2 = Environment(BUILDERS = [b1])
	env1.builder1.execute(target = 'out1')
	assert built_it['out1']

	built_it = {}
	env3 = Environment(BUILDERS = [b1, b2])
	env3.builder1.execute(target = 'out1')
	env3.builder2.execute(target = 'out2')
	env3.builder1.execute(target = 'out3')
	assert built_it['out1']
	assert built_it['out2']
	assert built_it['out3']

    def test_Command(self):
	pass	# XXX

    def test_Copy(self):
	"""Test the ability to copy a construction Environment.
	Update the copy independently afterwards and check that
	the original remains intact (that is, no dangling
	references point to objects in the copied environment).
	Copy the original with some construction variable
	updates and check that the original remains intact
	and the copy has the updated values.
	"""
	env1 = Environment(XXX = 'x', YYY = 'y')
	env2 = env1.Copy()
	env1copy = env1.Copy()
	env2.Update(YYY = 'yyy')
	assert env1 != env2
	assert env1 == env1copy

	env3 = env1.Copy(XXX = 'x3', ZZZ = 'z3')
	assert env3.Dictionary['XXX'] == 'x3'
	assert env3.Dictionary['YYY'] == 'y'
	assert env3.Dictionary['ZZZ'] == 'z3'
	assert env1 == env1copy

    def test_Dictionary(self):
	"""Test the simple ability to retrieve known construction
	variables from the Dictionary and check for well-known
	defaults that get inserted.
	"""
	env = Environment(XXX = 'x', YYY = 'y')
	assert env.Dictionary['XXX'] == 'x'
	assert env.Dictionary['YYY'] == 'y'
	assert env.Dictionary.has_key('BUILDERS')

    def test_Environment(self):
	"""Test the simple ability to create construction
	Environments.  Create two with identical arguments
	and check that they compare the same.
	"""
	env1 = Environment(XXX = 'x', YYY = 'y')
	env2 = Environment(XXX = 'x', YYY = 'y')
	assert env1 == env2

    def test_Install(self):
	pass	# XXX

    def test_InstallAs(self):
	pass	# XXX

    def test_Scanners(self):
	pass	# XXX

    def test_Update(self):
	"""Test the ability to update a construction Environment
	with new construction variables after it was first created.
	"""
	env1 = Environment(AAA = 'a', BBB = 'b')
	env1.Update(BBB = 'bbb', CCC = 'ccc')
	env2 = Environment(AAA = 'a', BBB = 'bbb', CCC = 'c')
	assert env1 != env2

    def test_subst(self):
	"""Test the ability to substitute construction variables
	into a string.  Check various combinations, including
	recursive expansion of variables into other variables.
	"""
	env = Environment(AAA = 'a', BBB = 'b')
	str = env.subst("%AAA %{AAA}A %BBBB %BBB")
	assert str == "a aA  b", str
	env = Environment(AAA = '%BBB', BBB = 'b', BBBA = 'foo')
	str = env.subst("%AAA %{AAA}A %{AAA}B %BBB")
	assert str == "b foo  b", str
	env = Environment(AAA = '%BBB', BBB = '%CCC', CCC = 'c')
	str = env.subst("%AAA %{AAA}A %{AAA}B %BBB")
	assert str == "c   c", str



if __name__ == "__main__":
    suite = unittest.makeSuite(EnvironmentTestCase, 'test_')
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
	sys.exit(1)
