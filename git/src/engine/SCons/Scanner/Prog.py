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

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import copy
import string

import SCons.Node
import SCons.Node.FS
import SCons.Scanner
import SCons.Util

def ProgScan(fs = SCons.Node.FS.default_fs):
    """Return a prototype Scanner instance for scanning executable
    files for static-lib dependencies"""
    ps = SCons.Scanner.Base(scan, "ProgScan", fs)
    return ps

def scan(node, env, target, fs):
    """
    This scanner scans program files for static-library
    dependencies.  It will search the LIBPATH environment variable
    for libraries specified in the LIBS variable, returning any
    files it finds as dependencies.
    """

    # This function caches information in target:
    # target.libpath - env['LIBPATH'] converted to nodes

    if not hasattr(target, 'libpath'):
        def Dir(x, dir=target.cwd, fs=fs): return fs.Dir(x,dir)
        try:
            target.libpath = tuple(SCons.Node.arg2nodes(env['LIBPATH'],Dir))
        except KeyError:
            target.libpath = ()
 
    libpath = target.libpath

    try:
        libs = env.Dictionary('LIBS')
    except KeyError:
        # There are no LIBS in this environment, so just return a null list:
        return []
    if SCons.Util.is_String(libs):
        libs = string.split(libs)

    try:
        prefix = env.Dictionary('LIBPREFIXES')
        if not SCons.Util.is_List(prefix):
            prefix = [ prefix ]
    except KeyError:
        prefix = [ '' ]

    try:
        suffix = env.Dictionary('LIBSUFFIXES')
        if not SCons.Util.is_List(suffix):
            suffix = [ suffix ]
    except KeyError:
        suffix = [ '' ]

    ret = []
    for suf in map(env.subst, suffix):
        for pref in map(env.subst, prefix):
            ret.extend(map(lambda x, s=suf, p=pref: p + x + s, libs))
    return SCons.Node.FS.find_files(ret, libpath, fs.File)
