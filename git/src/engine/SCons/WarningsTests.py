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

import sys
import unittest
import SCons.Warnings

class TestOutput:
    def __call__(self, x):
        self.out = str(x)

class WarningsTestCase(unittest.TestCase):
    def test_Warning(self):
        """Test warn function."""

        # Reset global state
        SCons.Warnings._enabled = []
        SCons.Warnings._warningAsException = 0
        
        to = TestOutput()
        SCons.Warnings._warningOut=to
        SCons.Warnings.enableWarningClass(SCons.Warnings.Warning)
        SCons.Warnings.warn(SCons.Warnings.DeprecatedWarning,
                            "Foo")
        assert to.out == "Foo", to.out
        SCons.Warnings.warn(SCons.Warnings.DependencyWarning,
                            "Foo", 1)
        assert to.out == "('Foo', 1)", to.out

    def test_WarningAsExc(self):
        """Test warnings as exceptions."""
        
        # Reset global state
        SCons.Warnings._enabled = []
        SCons.Warnings._warningAsException = 0

        SCons.Warnings.enableWarningClass(SCons.Warnings.Warning)
        SCons.Warnings.warningAsException()
        try:
            SCons.Warnings.warn(SCons.Warnings.Warning, "Foo")
        except:
            pass
        else:
            assert 0

        SCons.Warnings.warningAsException(0)
        SCons.Warnings.warn(SCons.Warnings.Warning, "Foo")

    def test_Disable(self):
        """Test disabling/enabling warnings."""

        # Reset global state
        SCons.Warnings._enabled = []
        SCons.Warnings._warningAsException = 0

        to = TestOutput()
        SCons.Warnings._warningOut=to
        to.out = None

        # No warnings by default
        SCons.Warnings.warn(SCons.Warnings.DeprecatedWarning,
                            "Foo")
        assert to.out is None, to.out

        SCons.Warnings.enableWarningClass(SCons.Warnings.Warning)
        SCons.Warnings.warn(SCons.Warnings.DeprecatedWarning,
                            "Foo")
        assert to.out == "Foo", to.out

        to.out = None
        SCons.Warnings.suppressWarningClass(SCons.Warnings.DeprecatedWarning)
        SCons.Warnings.warn(SCons.Warnings.DeprecatedWarning,
                            "Foo")
        assert to.out is None, to.out

        # Dependency warnings should still be enabled though
        SCons.Warnings.enableWarningClass(SCons.Warnings.Warning)
        SCons.Warnings.warn(SCons.Warnings.DependencyWarning,
                            "Foo")
        assert to.out == "Foo", to.out

        # Try reenabling all warnings...
        SCons.Warnings.enableWarningClass(SCons.Warnings.Warning)

        SCons.Warnings.enableWarningClass(SCons.Warnings.Warning)
        SCons.Warnings.warn(SCons.Warnings.DeprecatedWarning,
                            "Foo")
        assert to.out == "Foo", to.out

if __name__ == "__main__":
    suite = unittest.makeSuite(WarningsTestCase, 'test_')
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
	sys.exit(1)
