"""SCons.Environment

Base class for construction Environments.  These are
the primary objects used to communicate dependency and
construction information to the build engine.

Keyword arguments supplied when the construction Environment
is created are construction variables used to initialize the
Environment 
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


import copy
import os
import os.path
import string
import re
import shutil
from UserDict import UserDict

import SCons.Action
import SCons.Builder
import SCons.Defaults
import SCons.Errors
import SCons.Node
import SCons.Node.FS
import SCons.Platform
import SCons.Tool
import SCons.Util
import SCons.Warnings

class _Null:
    pass

_null = _Null

DefaultTargets = None

def installFunc(target, source, env):
    """Install a source file into a target using the function specified
    as the INSTALL construction variable."""
    try:
        install = env['INSTALL']
    except KeyError:
        raise SCons.Errors.UserError('Missing INSTALL construction variable.')
    return install(target[0].path, source[0].path, env)

def installString(target, source, env):
    return 'Install file: "%s" as "%s"' % (source[0], target[0])

installAction = SCons.Action.Action(installFunc, installString)

InstallBuilder = SCons.Builder.Builder(action=installAction)

def our_deepcopy(x):
   """deepcopy lists and dictionaries, and just copy the reference
   for everything else."""
   if SCons.Util.is_Dict(x):
       copy = {}
       for key in x.keys():
           copy[key] = our_deepcopy(x[key])
   elif SCons.Util.is_List(x):
       copy = map(our_deepcopy, x)
   else:
       copy = x
   return copy

def apply_tools(env, tools):
    if tools:
        for tool in tools:
            if SCons.Util.is_String(tool):
                tool = SCons.Tool.Tool(tool)
            tool(env)

class BuilderWrapper:
    """Wrapper class that associates an environment with a Builder at
    instantiation."""
    def __init__(self, env, builder):
        self.env = env
        self.builder = builder

    def __call__(self, *args, **kw):
        return apply(self.builder, (self.env,) + args, kw)

    # This allows a Builder to be executed directly
    # through the Environment to which it's attached.
    # In practice, we shouldn't need this, because
    # builders actually get executed through a Node.
    # But we do have a unit test for this, and can't
    # yet rule out that it would be useful in the
    # future, so leave it for now.
    def execute(self, **kw):
        kw['env'] = self.env
        apply(self.builder.execute, (), kw)

class BuilderDict(UserDict):
    """This is a dictionary-like class used by an Environment to hold
    the Builders.  We need to do this because every time someone changes
    the Builders in the Environment's BUILDERS dictionary, we must
    update the Environment's attributes."""
    def __init__(self, dict, env):
        # Set self.env before calling the superclass initialization,
        # because it will end up calling our other methods, which will
        # need to point the values in this dictionary to self.env.
        self.env = env
        UserDict.__init__(self, dict)

    def __setitem__(self, item, val):
        UserDict.__setitem__(self, item, val)
        try:
            self.setenvattr(item, val)
        except AttributeError:
            # Have to catch this because sometimes __setitem__ gets
            # called out of __init__, when we don't have an env
            # attribute yet, nor do we want one!
            pass

    def setenvattr(self, item, val):
        """Set the corresponding environment attribute for this Builder.

        If the value is already a BuilderWrapper, we pull the builder
        out of it and make another one, so that making a copy of an
        existing BuilderDict is guaranteed separate wrappers for each
        Builder + Environment pair."""
        try:
            builder = val.builder
        except AttributeError:
            builder = val
        setattr(self.env, item, BuilderWrapper(self.env, builder))

    def __delitem__(self, item):
        UserDict.__delitem__(self, item)
        delattr(self.env, item)

    def update(self, dict):
        for i, v in dict.items():
            self.__setitem__(i, v)

class Environment:
    """Base class for construction Environments.  These are
    the primary objects used to communicate dependency and
    construction information to the build engine.

    Keyword arguments supplied when the construction Environment
    is created are construction variables used to initialize the
    Environment.
    """

    #######################################################################
    # This is THE class for interacting with the SCons build engine,
    # and it contains a lot of stuff, so we're going to try to keep this
    # a little organized by grouping the methods.
    #######################################################################

    #######################################################################
    # Methods that make an Environment act like a dictionary.  These have
    # the expected standard names for Python mapping objects.  Note that
    # we don't actually make an Environment a subclass of UserDict for
    # performance reasons.  Note also that we only supply methods for
    # dictionary functionality that we actually need and use.
    #######################################################################

    def __init__(self,
                 platform=None,
                 tools=None,
                 options=None,
                 **kw):
        self.fs = SCons.Node.FS.default_fs
        self.lookup_list = SCons.Node.arg2nodes_lookups
        self._dict = our_deepcopy(SCons.Defaults.ConstructionEnvironment)

        self._dict['BUILDERS'] = BuilderDict(self._dict['BUILDERS'], self)

        if platform is None:
            platform = self._dict.get('PLATFORM', None)
            if platform is None:
                platform = SCons.Platform.Platform()
        if SCons.Util.is_String(platform):
            platform = SCons.Platform.Platform(platform)
        self._dict['PLATFORM'] = str(platform)
        platform(self)

        # Apply the passed-in variables before calling the tools,
        # because they may use some of them:
        apply(self.Replace, (), kw)
        
        # Update the environment with the customizable options
        # before calling the tools, since they may use some of the options: 
        if options:
            options.Update(self)

        if tools is None:
            tools = self._dict.get('TOOLS', None)
            if tools is None:
                tools = ['default']
        apply_tools(self, tools)

        # Reapply the passed in variables after calling the tools,
        # since they should overide anything set by the tools:
        apply(self.Replace, (), kw)

        # Update the environment with the customizable options
        # after calling the tools, since they should override anything
        # set by the tools:
        if options:
            options.Update(self)

    def __cmp__(self, other):
	return cmp(self._dict, other._dict)

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        if key in ['TARGET', 'TARGETS', 'SOURCE', 'SOURCES']:
            SCons.Warnings.warn(SCons.Warnings.ReservedVariableWarning,
                                "Ignoring attempt to set reserved variable `%s'" % key)
        elif key == 'BUILDERS':
            try:
                bd = self._dict[key]
                for k in bd.keys():
                    del bd[k]
            except KeyError:
                self._dict[key] = BuilderDict(kwbd, self)
            self._dict[key].update(value)
        else:
            if not SCons.Util.is_valid_construction_var(key):
                raise SCons.Errors.UserError, "Illegal construction variable `%s'" % key
            self._dict[key] = value

    def __delitem__(self, key):
        del self._dict[key]

    def items(self):
        "Emulates the items() method of dictionaries."""
        return self._dict.items()

    def has_key(self, key):
        return self._dict.has_key(key)

    def get(self, key, default=None):
        "Emulates the get() method of dictionaries."""
        return self._dict.get(key, default)

    #######################################################################
    # Utility methods that are primarily for internal use by SCons.
    # These begin with lower-case letters.  Note that the subst() method
    # is actually already out of the closet and used by people.
    #######################################################################

    def arg2nodes(self, args, node_factory=_null, lookup_list=_null):
        if node_factory is _null:
            node_factory = self.fs.File
        if lookup_list is _null:
            lookup_list = self.lookup_list

        if not args:
            return []

        if not SCons.Util.is_List(args):
            args = [args]

        nodes = []
        for v in args:
            if SCons.Util.is_String(v):
                n = None
                for l in lookup_list:
                    n = l(v)
                    if not n is None:
                        break
                if not n is None:
                    if SCons.Util.is_String(n):
                        n = self.subst(n, raw=1)
                        if node_factory:
                            n = node_factory(n)
                    nodes.append(n)
                elif node_factory:
                    v = self.subst(v, raw=1)
                    nodes.append(node_factory(v))
            else:
                nodes.append(v)
    
        return nodes

    def get_builder(self, name):
        """Fetch the builder with the specified name from the environment.
        """
        try:
            return self._dict['BUILDERS'][name]
        except KeyError:
            return None

    def get_scanner(self, skey):
        """Find the appropriate scanner given a key (usually a file suffix).
        Does a linear search. Could be sped up by creating a dictionary if
        this proves too slow.
        """
        if self._dict['SCANNERS']:
            for scanner in self._dict['SCANNERS']:
                if skey in scanner.skeys:
                    return scanner
        return None

    def subst(self, string, raw=0, target=None, source=None):
	"""Recursively interpolates construction variables from the
	Environment into the specified string, returning the expanded
	result.  Construction variables are specified by a $ prefix
	in the string and begin with an initial underscore or
	alphabetic character followed by any number of underscores
	or alphanumeric characters.  The construction variable names
	may be surrounded by curly braces to separate the name from
	trailing characters.
	"""
        if raw:
            mode = SCons.Util.SUBST_RAW
        else:
            mode = SCons.Util.SUBST_CMD
        return SCons.Util.scons_subst(string, self, mode,
                                      target, source)
    
    def subst_list(self, string, raw=0, target=None, source=None):
        """Calls through to SCons.Util.scons_subst_list().  See
        the documentation for that function."""
        if raw:
            mode = SCons.Util.SUBST_RAW
        else:
            mode = SCons.Util.SUBST_CMD
        return SCons.Util.scons_subst_list(string, self, mode,
                                           target, source)

    #######################################################################
    # Public methods for manipulating an Environment.  These begin with
    # upper-case letters.  The essential characteristic of methods in
    # this section is that they do *not* have corresponding same-named
    # global functions.  For example, a stand-alone Append() function
    # makes no sense, because Append() is all about appending values to
    # an Environment's construction variables.
    #######################################################################

    def Append(self, **kw):
        """Append values to existing construction variables
        in an Environment.
        """
        kw = our_deepcopy(kw)
        for key in kw.keys():
            if not self._dict.has_key(key):
                self._dict[key] = kw[key]
            elif SCons.Util.is_List(self._dict[key]) and not \
                 SCons.Util.is_List(kw[key]):
                self._dict[key] = self._dict[key] + [ kw[key] ]
            elif SCons.Util.is_List(kw[key]) and not \
                 SCons.Util.is_List(self._dict[key]):
                self._dict[key] = [ self._dict[key] ] + kw[key]
            elif SCons.Util.is_Dict(self._dict[key]) and \
                 SCons.Util.is_Dict(kw[key]):
                self._dict[key].update(kw[key])
            else:
                self._dict[key] = self._dict[key] + kw[key]

    def AppendENVPath(self, name, newpath, envname = 'ENV', sep = os.pathsep):
        """Append path elements to the path 'name' in the 'ENV'
        dictionary for this environment.  Will only add any particular
        path once, and will normpath and normcase all paths to help
        assure this.  This can also handle the case where the env
        variable is a list instead of a string.
        """

        orig = ''
        if self._dict.has_key(envname) and self._dict[envname].has_key(name):
            orig = self._dict[envname][name]

        nv = SCons.Util.AppendPath(orig, newpath, sep)
            
        if not self._dict.has_key(envname):
            self._dict[envname] = {}

        self._dict[envname][name] = nv

    def Copy(self, tools=None, **kw):
        """Return a copy of a construction Environment.  The
        copy is like a Python "deep copy"--that is, independent
        copies are made recursively of each objects--except that
        a reference is copied when an object is not deep-copyable
        (like a function).  There are no references to any mutable
        objects in the original Environment.
        """
        clone = copy.copy(self)
        clone._dict = our_deepcopy(self._dict)
        try:
            cbd = clone._dict['BUILDERS']
            clone._dict['BUILDERS'] = BuilderDict(cbd, clone)
        except KeyError:
            pass
        
        apply_tools(clone, tools)

        # Apply passed-in variables after the new tools.
        apply(clone.Replace, (), kw)
        return clone

    def Detect(self, progs):
        """Return the first available program in progs.
        """
        if not SCons.Util.is_List(progs):
            progs = [ progs ]
        for prog in progs:
            path = self.WhereIs(prog)
            if path: return prog
        return None

    def Dictionary(self, *args):
	if not args:
	    return self._dict
	dlist = map(lambda x, s=self: s._dict[x], args)
	if len(dlist) == 1:
	    dlist = dlist[0]
	return dlist

    def FindIxes(self, paths, prefix, suffix):
        """
        Search a list of paths for something that matches the prefix and suffix.

        paths - the list of paths or nodes.
        prefix - construction variable for the prefix.
        suffix - construction variable for the suffix.
        """

        suffix = self.subst('$%s'%suffix)
        prefix = self.subst('$%s'%prefix)

        for path in paths:
            dir,name = os.path.split(str(path))
            if name[:len(prefix)] == prefix and name[-len(suffix):] == suffix: 
                return path

    def Override(self, overrides):
        """
        Produce a modified environment whose variables
        are overriden by the overrides dictionaries.

        overrides - a dictionary that will override
        the variables of this environment.

        This function is much more efficient than Copy()
        or creating a new Environment because it doesn't do
        a deep copy of the dictionary, and doesn't do a copy
        at all if there are no overrides.
        """

        if overrides:
            env = copy.copy(self)
            env._dict = copy.copy(self._dict)
            env._dict.update(overrides)
            return env
        else:
            return self

    def Prepend(self, **kw):
        """Prepend values to existing construction variables
        in an Environment.
        """
        kw = our_deepcopy(kw)
        for key in kw.keys():
            if not self._dict.has_key(key):
                self._dict[key] = kw[key]
            elif SCons.Util.is_List(self._dict[key]) and not \
                 SCons.Util.is_List(kw[key]):
                self._dict[key] = [ kw[key] ] + self._dict[key]
            elif SCons.Util.is_List(kw[key]) and not \
                 SCons.Util.is_List(self._dict[key]):
                self._dict[key] = kw[key] + [ self._dict[key] ]
            elif SCons.Util.is_Dict(self._dict[key]) and \
                 SCons.Util.is_Dict(kw[key]):
                self._dict[key].update(kw[key])
            else:
                self._dict[key] = kw[key] + self._dict[key]

    def PrependENVPath(self, name, newpath, envname = 'ENV', sep = os.pathsep):
        """Prepend path elements to the path 'name' in the 'ENV'
        dictionary for this environment.  Will only add any particular
        path once, and will normpath and normcase all paths to help
        assure this.  This can also handle the case where the env
        variable is a list instead of a string.
        """

        orig = ''
        if self._dict.has_key(envname) and self._dict[envname].has_key(name):
            orig = self._dict[envname][name]

        nv = SCons.Util.PrependPath(orig, newpath, sep)
            
        if not self._dict.has_key(envname):
            self._dict[envname] = {}

        self._dict[envname][name] = nv

    def Replace(self, **kw):
        """Replace existing construction variables in an Environment
        with new construction variables and/or values.
        """
        try:
            kwbd = our_deepcopy(kw['BUILDERS'])
            del kw['BUILDERS']
            self.__setitem__('BUILDERS', kwbd)
        except KeyError:
            pass
        self._dict.update(our_deepcopy(kw))

    def ReplaceIxes(self, path, old_prefix, old_suffix, new_prefix, new_suffix):
        """
        Replace old_prefix with new_prefix and old_suffix with new_suffix.

        env - Environment used to interpolate variables.
        path - the path that will be modified.
        old_prefix - construction variable for the old prefix.
        old_suffix - construction variable for the old suffix.
        new_prefix - construction variable for the new prefix.
        new_suffix - construction variable for the new suffix.
        """
        old_prefix = self.subst('$%s'%old_prefix)
        old_suffix = self.subst('$%s'%old_suffix)

        new_prefix = self.subst('$%s'%new_prefix)
        new_suffix = self.subst('$%s'%new_suffix)

        dir,name = os.path.split(str(path))
        if name[:len(old_prefix)] == old_prefix:
            name = name[len(old_prefix):]
        if name[-len(old_suffix):] == old_suffix:
            name = name[:-len(old_suffix)]
        return os.path.join(dir, new_prefix+name+new_suffix)

    def WhereIs(self, prog):
        """Find prog in the path.  
        """
        path = None
        pathext = None
        if self.has_key('ENV'):
            if self['ENV'].has_key('PATH'):
                path = self['ENV']['PATH']
            if self['ENV'].has_key('PATHEXT'):
                pathext = self['ENV']['PATHEXT']
        path = SCons.Util.WhereIs(prog, path, pathext)
        if path: return path
        return None

    #######################################################################
    # Public methods for doing real "SCons stuff" (manipulating
    # dependencies, setting attributes on targets, etc.).  These begin
    # with upper-case letters.  The essential characteristic of methods
    # in this section is that they all *should* have corresponding
    # same-named global functions.
    #######################################################################

    def AlwaysBuild(self, *targets):
        tlist = []
        for t in targets:
            tlist.extend(self.arg2nodes(t, self.fs.File))

        for t in tlist:
            t.set_always_build()

        if len(tlist) == 1:
            tlist = tlist[0]
        return tlist

    def Command(self, target, source, action):
        """Builds the supplied target files from the supplied
        source files using the supplied action.  Action may
        be any type that the Builder constructor will accept
        for an action."""
        bld = SCons.Builder.Builder(action=action,
                                    source_factory=SCons.Node.FS.default_fs.Entry)
        return bld(self, target, source)

    def Depends(self, target, dependency):
        """Explicity specify that 'target's depend on 'dependency'."""
        tlist = self.arg2nodes(target, self.fs.File)
        dlist = self.arg2nodes(dependency, self.fs.File)
        for t in tlist:
            t.add_dependency(dlist)

        if len(tlist) == 1:
            tlist = tlist[0]
        return tlist

    def Ignore(self, target, dependency):
        """Ignore a dependency."""
        tlist = self.arg2nodes(target, self.fs.File)
        dlist = self.arg2nodes(dependency, self.fs.File)
        for t in tlist:
            t.add_ignore(dlist)

        if len(tlist) == 1:
            tlist = tlist[0]
        return tlist

    def Install(self, dir, source):
        """Install specified files in the given directory."""
        try:
            dnodes = self.arg2nodes(dir, self.fs.Dir)
        except TypeError:
            raise SCons.Errors.UserError, "Target `%s' of Install() is a file, but should be a directory.  Perhaps you have the Install() arguments backwards?" % str(dir)
        try:
            sources = self.arg2nodes(source, self.fs.File)
        except TypeError:
            if SCons.Util.is_List(source):
                raise SCons.Errors.UserError, "Source `%s' of Install() contains one or more non-files.  Install() source must be one or more files." % repr(map(str, source))
            else:
                raise SCons.Errors.UserError, "Source `%s' of Install() is not a file.  Install() source must be one or more files." % str(source)
        tgt = []
        for dnode in dnodes:
            for src in sources:
                target = SCons.Node.FS.default_fs.File(src.name, dnode)
                tgt.append(InstallBuilder(self, target, src))
        if len(tgt) == 1:
            tgt = tgt[0]
        return tgt

    def InstallAs(self, target, source):
        """Install sources as targets."""
        sources = self.arg2nodes(source, self.fs.File)
        targets = self.arg2nodes(target, self.fs.File)
        ret = []
        for src, tgt in map(lambda x, y: (x, y), sources, targets):
            ret.append(InstallBuilder(self, tgt, src))
        if len(ret) == 1:
            ret = ret[0]
        return ret

    def Precious(self, *targets):
        tlist = []
        for t in targets:
            tlist.extend(self.arg2nodes(t, self.fs.File))

        for t in tlist:
            t.set_precious()

        if len(tlist) == 1:
            tlist = tlist[0]
        return tlist

    def SideEffect(self, side_effect, target):
        """Tell scons that side_effects are built as side 
        effects of building targets."""
        side_effects = self.arg2nodes(side_effect, self.fs.File)
        targets = self.arg2nodes(target, self.fs.File)

        for side_effect in side_effects:
            # A builder of 1 means the node is supposed to appear
            # buildable without actually having a builder, so we allow
            # it to be a side effect as well.
            if side_effect.has_builder() and side_effect.builder != 1:
                raise SCons.Errors.UserError, "Multiple ways to build the same target were specified for: %s" % str(side_effect)
            side_effect.add_source(targets)
            side_effect.side_effect = 1
            self.Precious(side_effect)
            for target in targets:
                target.side_effects.append(side_effect)
        if len(side_effects) == 1:
            return side_effects[0]
        else:
            return side_effects

    def SourceCode(self, entry, builder):
        """Arrange for a source code builder for (part of) a tree."""
        entries = self.arg2nodes(entry, self.fs.Entry)
        for entry in entries:
            entry.set_src_builder(builder)
        if len(entries) == 1:
            return entries[0]
        return entries
