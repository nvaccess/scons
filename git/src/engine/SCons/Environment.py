"""SCons.Environment

XXX

"""

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"



import copy
import re
import types
import SCons.Util
import SCons.Builder


def Command():
    pass	# XXX

def Install():
    pass	# XXX

def InstallAs():
    pass	# XXX



_cv = re.compile(r'%([_a-zA-Z]\w*|{[_a-zA-Z]\w*})')



def _deepcopy_atomic(x, memo):
	return x
copy._deepcopy_dispatch[types.ModuleType] = _deepcopy_atomic
copy._deepcopy_dispatch[types.ClassType] = _deepcopy_atomic
copy._deepcopy_dispatch[types.FunctionType] = _deepcopy_atomic
copy._deepcopy_dispatch[types.MethodType] = _deepcopy_atomic
copy._deepcopy_dispatch[types.TracebackType] = _deepcopy_atomic
copy._deepcopy_dispatch[types.FrameType] = _deepcopy_atomic
copy._deepcopy_dispatch[types.FileType] = _deepcopy_atomic



class Environment:
    """Base class for construction Environments.  These are
    the primary objects used to communicate dependency and
    construction information to the build engine.

    Keyword arguments supplied when the construction Environment
    is created are construction variables used to initialize the
    Environment.
    """

    def __init__(self, **kw):
	self._dict = {}
	if kw.has_key('BUILDERS'):
	    builders = kw['BUILDERS']
	    if not type(builders) is types.ListType:
		kw['BUILDERS'] = [builders]
	else:
	    import SCons.Defaults
	    kw['BUILDERS'] = SCons.Defaults.Builders[:]
	if not kw.has_key('ENV'):
	    import SCons.Defaults
	    kw['ENV'] = SCons.Defaults.ENV.copy()
	self._dict.update(copy.deepcopy(kw))

	class BuilderWrapper:
	    """Wrapper class that allows an environment to
	    be associated with a Builder at instantiation.
	    """
	    def __init__(self, env, builder):
		self.env = env
		self.builder = builder
	
	    def __call__(self, target = None, source = None):
		return self.builder(self.env, target, source)

	    # This allows a Builder to be executed directly
	    # through the Environment to which it's attached.
	    # In practice, we shouldn't need this, because
	    # builders actually get executed through a Node.
	    # But we do have a unit test for this, and can't
	    # yet rule out that it would be useful in the
	    # future, so leave it for now.
	    def execute(self, **kw):
	    	kw['env'] = self
	    	apply(self.builder.execute, (), kw)

	for b in kw['BUILDERS']:
	    setattr(self, b.name, BuilderWrapper(self, b))



    def __cmp__(self, other):
	return cmp(self._dict, other._dict)

    def Builders(self):
	pass	# XXX

    def Copy(self, **kw):
	"""Return a copy of a construction Environment.  The
	copy is like a Python "deep copy"--that is, independent
	copies are made recursively of each objects--except that
	a reference is copied when an object is not deep-copyable
	(like a function).  There are no references to any mutable
	objects in the original Environment.
	"""
	clone = copy.deepcopy(self)
	apply(clone.Update, (), kw)
	return clone

    def Scanners(self):
	pass	# XXX

    def	Update(self, **kw):
	"""Update an existing construction Environment with new
	construction variables and/or values.
	"""
	self._dict.update(copy.deepcopy(kw))

    def	Depends(self, target, dependency):
	"""Explicity specify that 'target's depend on 'dependency'."""
	tlist = SCons.Util.scons_str2nodes(target)
	dlist = SCons.Util.scons_str2nodes(dependency)
	for t in tlist:
	    t.add_dependency(dlist)

	if len(tlist) == 1:
	    tlist = tlist[0]
	return tlist

    def Dictionary(self, *args):
	if not args:
	    return self._dict
	dlist = map(lambda x, s=self: s._dict[x], args)
	if len(dlist) == 1:
	    dlist = dlist[0]
	return dlist

    def Command(self, target, source, action):
        """Builds the supplied target files from the supplied
        source files using the supplied action.  Action may
        be any type that the Builder constructor will accept
        for an action."""
        bld = SCons.Builder.Builder(name="Command", action=action)
        return bld(self, target, source)

    def subst(self, string):
	"""Recursively interpolates construction variables from the
	Environment into the specified string, returning the expanded
	result.  Construction variables are specified by a % prefix
	in the string and begin with an initial underscore or
	alphabetic character followed by any number of underscores
	or alphanumeric characters.  The construction variable names
	may be surrounded by curly braces to separate the name from
	trailing characters.
	"""
	def repl(m, _self=self):
	    key = m.group(1)
	    if key[:1] == '{' and key[-1:] == '}':
		key = key[1:-1]
	    if _self._dict.has_key(key): return _self._dict[key]
	    else: return ''
	n = 1
	while n != 0:
	    string, n = _cv.subn(repl, string)
	return string
