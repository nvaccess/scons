"""SCons.Sig

The Signature package for the scons software construction utility.

"""

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

import os
import os.path
import string
import SCons.Node

#XXX Get rid of the global array so this becomes re-entrant.
sig_files = []

def write():
    global sig_files
    for sig_file in sig_files:
        sig_file.write()

class SConsignFile:
    """
    Encapsulates reading and writing a .sconsign file.
    """

    def __init__(self, dir, module):
        """
        dir - the directory for the file
        module - the signature module being used
        """
        
        self.dir = dir
        self.module = module
        self.sconsign = os.path.join(dir.path, '.sconsign')
        self.entries = {}
        self.dirty = None
                    
        try:
            file = open(self.sconsign, 'rt')
        except:
            pass
        else:
            for line in file.readlines():
                filename, rest = map(string.strip, string.split(line, ":"))
                self.entries[filename] = rest

        global sig_files
        sig_files.append(self)

    def get(self, filename):
        """
        Get the .sconsign entry for a file

        filename - the filename whose signature will be returned
        returns - (timestamp, bsig, csig)
        """
        
        try:
            arr = map(string.strip, string.split(self.entries[filename], " "))
        except KeyError:
            return (None, None, None)
        try:
            if arr[1] == '-': bsig = None
            else:             bsig = self.module.from_string(arr[1])
        except IndexError:
            bsig = None
        try:
            if arr[2] == '-': csig = None
            else:             csig = self.module.from_string(arr[2])
        except IndexError:
            csig = None
        return (int(arr[0]), bsig, csig)

    def set(self, filename, timestamp, bsig = None, csig = None):
        """
        Set the .sconsign entry for a file

        filename - the filename whose signature will be set
        timestamp - the timestamp
        module - the signature module being used
        bsig - the file's build signature
        csig - the file's content signature
        """
        if bsig is None: bsig = '-'
        else:            bsig = self.module.to_string(bsig)
        if csig is None: csig = ''
        else:            csig = ' ' + self.module.to_string(csig)
        self.entries[filename] = "%d %s%s" % (timestamp, bsig, csig)
        self.dirty = 1

    def write(self):
        """
        Write the .sconsign file to disk.

        Try to write to a temporary file first, and rename it if we
        succeed.  If we can't write to the temporary file, it's
        probably because the directory isn't writable (and if so,
        how did we build anything in this directory, anyway?), so
        try to write directly to the .sconsign file as a backup.
        If we can't rename, try to copy the temporary contents back
        to the .sconsign file.  Either way, always try to remove
        the temporary file at the end.
        """
        if self.dirty:
            temp = os.path.join(self.dir.path, '.scons%d' % os.getpid())
            try:
                file = open(temp, 'wt')
                fname = temp
            except:
                file = open(self.sconsign, 'wt')
                fname = self.sconsign
            keys = self.entries.keys()
            keys.sort()
            for name in keys:
                file.write("%s: %s\n" % (name, self.entries[name]))
            file.close()
            if fname != self.sconsign:
                try:
                    mode = os.stat(self.sconsign)[0]
                    os.chmod(self.sconsign, 0666)
                    os.unlink(self.sconsign)
                except:
                    pass
                try:
                    os.rename(fname, self.sconsign)
                except:
                    open(self.sconsign, 'wb').write(open(fname, 'rb').read())
                    os.chmod(self.sconsign, mode)
            try:
                os.unlink(temp)
            except:
                pass


class Calculator:
    """
    Encapsulates signature calculations and .sconsign file generating
    for the build engine.
    """

    def __init__(self, module):
        """
        Initialize the calculator.

        module - the signature module to use for signature calculations
        """
        self.module = module

    def bsig(self, node):
        """
        Generate a node's build signature, the digested signatures
        of its dependency files and build information.

        node - the node whose sources will be collected
        returns - the build signature

        This no longer handles the recursive descent of the
        node's children's signatures.  We expect that they're
        already built and updated by someone else, if that's
        what's wanted.
        """
        if not node.use_signature:
            return None
        #XXX If configured, use the content signatures from the
        #XXX .sconsign file if the timestamps match.

        bsig = node.get_bsig()
        if not bsig is None:
            return bsig

        # Collect the signatures for ALL the nodes that this
        # node depends on. Just collecting the direct
        # dependants is not good enough, because
        # the signature of a non-derived file does
        # not include the signatures of its psuedo-sources
        # (e.g. the signature for a .c file does not include
        # the signatures of the .h files that it includes).

        # However, we do NOT want to walk dependencies of non-
        # derived files, because calling get_signature() on the
        # derived nodes will in turn call bsig() again and do that
        # for us.  Hence:
        sigs = []
        def non_derived(n, parent, myself=node):
            if not n.builder or n is myself:
                return filter(lambda x, i=myself.ignore: x not in i,
                              n.all_children(None))
            return []
        def get_sig(n, parent, self=self, myself=node, sigs=sigs):
            if not n is myself:
                sigs.append(self.get_signature(n))
        walker = SCons.Node.Walker(node, non_derived, eval_func=get_sig)
        child = walker.next()
        while child:
            child = walker.next()

        if node.builder:
            sigs.append(self.module.signature(node.builder_sig_adapter()))
        return self.module.collect(filter(lambda x: not x is None, sigs))

    def csig(self, node):
        """
        Generate a node's content signature, the digested signature
        of its content.

        node - the node
        returns - the content signature
        """
        if not node.use_signature:
            return None
        #XXX If configured, use the content signatures from the
        #XXX .sconsign file if the timestamps match.
        csig = node.get_csig()
        if not csig is None:
            return csig
        
        return self.module.signature(node)

    def get_signature(self, node):
        """
        Get the appropriate signature for a node.

        node - the node
        returns - the signature or None if the signature could not
        be computed.

        This method does not store the signature in the node and
        in the .sconsign file.
        """

        if not node.use_signature:
            # This node type doesn't use a signature (e.g. a
            # directory) so bail right away.
            return None
        elif node.builder:
            return self.bsig(node)
        elif not node.exists():
            return None
        else:
            return self.csig(node)

    def current(self, node, newsig):
        """
        Check if a signature is up to date with respect to a node.

        node - the node whose signature will be checked
        newsig - the (presumably current) signature of the file

        returns - 1 if the file is current with the specified signature,
        0 if it isn't
        """

        c = node.current()
        if not c is None:
            # The node itself has told us whether or not it's
            # current without checking the signature.  The
            # canonical uses here are a "0" return for a file
            # that doesn't exist, or a directory.
            return c

        oldtime, oldbsig, oldcsig = node.get_prevsiginfo()

        if not node.builder and node.get_timestamp() == oldtime:
            return 1
        
        return self.module.current(newsig, oldbsig)
