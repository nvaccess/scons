"""SCons.Tool.gnulink

Tool-specific initialization for the gnu linker.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

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

import SCons.Util
import SCons.Tool
import os
import sys
import re

import link


def generate(env):
    """Add Builders and construction variables for gnulink to an Environment."""
    link.generate(env)

    if env['PLATFORM'] == 'hpux':
        env['SHLINKFLAGS'] = SCons.Util.CLVar('$LINKFLAGS -shared -fPIC')

    # __RPATH is set to $_RPATH in the platform specification if that
    # platform supports it.
    env['RPATHPREFIX'] = '-Wl,-rpath='
    env['RPATHSUFFIX'] = ''
    env['_RPATH'] = '${_concat(RPATHPREFIX, RPATH, RPATHSUFFIX, __env__)}'

    # The $_SHLIBVERSIONFLAGS define extra commandline flags used when
    # building VERSIONED shared libraries. It's always set, but used only
    # when VERSIONED library is built (see __SHLIBVERSIONFLAGS).
    if sys.platform.startswith('openbsd'):
        # OpenBSD doesn't usually use SONAME for libraries
        env['_SHLIBVERSIONFLAGS'] = '$SHLIBVERSIONFLAGS'
        env['_LDMODULEVERSIONFLAGS'] = '$LDMODULEVERSIONFLAGS'
    else:
        env['_SHLIBVERSIONFLAGS'] = '$SHLIBVERSIONFLAGS -Wl,-soname=$_SHLINKSONAME'
        env['_LDMODULEVERSIONFLAGS'] = '$LDMODULEVERSIONFLAGS -Wl,-soname=$_LDMODULESONAME'
    env['SHLIBVERSIONFLAGS'] = SCons.Util.CLVar('-Wl,-Bsymbolic')
    env['LDMODULEVERSIONFLAGS'] = '$SHLIBVERSIONFLAGS'

    # libfoo.so.X.Y.Z -> libfoo.so.X
    env['_SHLINKSONAME']   = '${ShLibSonameGenerator(__env__,TARGET)}'
    env['_LDMODULESONAME'] = '${LdModSonameGenerator(__env__,TARGET)}'

    env['ShLibSonameGenerator'] = SCons.Tool.ShLibSonameGenerator
    env['LdModSonameGenerator'] = SCons.Tool.LdModSonameGenerator

    env['LINKCALLBACKS'] = {
        'VersionedShLibSuffix'   : link._versioned_lib_suffix,
        'VersionedLdModSuffix'   : link._versioned_lib_suffix,
        'VersionedShLibSymlinks' : link._versioned_shlib_symlinks,
        'VersionedLdModSymlinks' : link._versioned_ldmod_symlinks,
        'VersionedShLibName'     : link._versioned_shlib_name,
        'VersionedLdModName'     : link._versioned_ldmod_name,
        'VersionedShLibSoname'   : link._versioned_shlib_soname,
        'VersionedLdModSoname'   : link._versioned_ldmod_soname,
    }
    
def exists(env):
    # TODO: sync with link.smart_link() to choose a linker
    linkers = { 'CXX': ['g++'], 'CC': ['gcc'] }
    alltools = []
    for langvar, linktools in linkers.items():
        if langvar in env: # use CC over CXX when user specified CC but not CXX
            return SCons.Tool.FindTool(linktools, env)
        alltools.extend(linktools)
    return SCons.Tool.FindTool(alltools, env) # find CXX or CC

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
