#!/usr/bin/env python

# Copyright (C) 2013, Carsten Juttner <carjay@gmx.net>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Parser for /proc/smaps information

import os
import re
import sys
import logging

lh = logging.getLogger(__name__)
info    = lh.info
debug   = lh.debug
error   = lh.error
warning = lh.warning


class MapEntry:
    VM_READ     = 1
    VM_WRITE    = 2
    VM_EXEC     = 4
    VM_MAYSHARE = 8

    startaddress = None # starting address of mapping
    stopaddress  = None # final address of mapping (exclusive)
    access       = None # one of the VM-flags
    offset       = None # offset into file (if it's a mapped file)
    devicemajor  = None # device major
    deviceminor  = None # device minor
    inode        = None # inode (of mapped file or of device file (not the device itself!))
    
    name         = None # name of mapping, can also be an empty string if not stated

    size           = None # total size
    rss            = None # resident set size
    pss            = None # proportional set size (estimate)
    shared_clean   = None
    shared_dirty   = None
    private_clean  = None
    private_dirty  = None
    referenced     = None
    anonymous      = None
    anonhugepages  = None
    swap           = None
    kernelpagesize = None
    mmupagesize    = None
    locked         = None

    
    def __repr__(self):
        '''
            dumps all information
        '''
        accesslist = []
        if self.access & self.VM_READ:
            accesslist.append("VM_READ")
        if self.access & self.VM_WRITE:
            accesslist.append("VM_WRITE")
        if self.access & self.VM_EXEC:
            accesslist.append("VM_EXEC")
        if self.access & self.VM_MAYSHARE:
            accesslist.append("VM_MAYSHARE")
        
        s = "<MapEntry start:%08x stop:%08x access:%s offset:%d dev:%d:%d inode:%d name:'%s'" % (
                self.startaddress, self.stopaddress, ','.join(accesslist),
                self.offset, self.devicemajor, self.deviceminor, self.inode, self.name)
        
        s += " size:%d rss:%d pss:%d shared_clean:%d shared_dirty:%d private_clean:%d private_dirty:%d referenced:%d" % (
                self.size, self.rss, self.pss, self.shared_clean, self.shared_dirty,
                self.private_clean, self.private_dirty, self.referenced)

        s += " anonymous:%d anonhugepages:%d swap:%d kernelpagesize:%d mmupagesize:%d locked:%d>" % (
                self.anonymous, self.anonhugepages, self.swap, self.kernelpagesize, self.mmupagesize, self.locked)
        return s


    def setAccess(self, accessstr):
        '''
            helper to parse textual access information to flags
            accesstr -- string as extracted from the procfs smaps line
        '''
        self.access = 0
        for letter in accessstr:
            if letter == 'r':
                self.access |= self.VM_READ
            elif letter == 'w':
                self.access |= self.VM_WRITE
            elif letter == 'x':
                self.access |= self.VM_EXEC
            elif letter == 's':
                self.access |= self.VM_MAYSHARE


    def setField(self, prop, value):
        '''
            helper to assign the texual field name to its property
            prop  -- property as extracted from the procfs smaps line
            value -- values in bytes(!) as extracted from the procfs smaps line
        '''
        bytecount = int(value) * (1<<10)
        if prop == 'Rss':
            self.rss = bytecount
        elif prop == 'Pss':
            self.pss = bytecount
        elif prop == 'Size':
            self.size = bytecount
        elif prop == 'Shared_Clean':
            self.shared_clean = bytecount
        elif prop == 'Shared_Dirty':
            self.shared_dirty = bytecount
        elif prop == 'Private_Clean':
            self.private_clean = bytecount
        elif prop == 'Private_Dirty':
            self.private_dirty = bytecount
        elif prop == 'Referenced':
            self.referenced = bytecount
        elif prop == 'Anonymous':
            self.anonymous = bytecount
        elif prop == 'AnonHugePages':
            self.anonhugepages = bytecount
        elif prop == 'Swap':
            self.swap = bytecount
        elif prop == 'KernelPageSize':
            self.kernelpagesize = bytecount
        elif prop == 'MMUPageSize':
            self.mmupagesize = bytecount
        elif prop == 'Locked':
            self.locked = bytecount
        else:
            warning("MapEntry.setField: unknown property '%s', ignored" % prop)



class SMaps:
    '''
        class to hold the information of the entire smaps entry for one pid
    '''
    maplist = None # list of MapEntries from the parsed file    
    
    #
    _filename      = None
    
    def __init__(self, pid):
        '''
            parse information from /proc filesystem for given pid
            result is written to self.maplist
            pid -- pid as a decimal number, can be a string or a number
        '''
        self._filename = "/proc/%d/smaps" % int(pid)
        if not os.path.exists(self._filename):
            errmsg = "SMaps: smaps file '%s' does not exist" % self._filename
            error(errmsg)
            raise IOError, errmsg

        try:
            with open(self._filename, 'rb') as fh:
                smapsbuffer = fh.read()
                self._parseFile(smapsbuffer)
            if len(self.maplist) == 0:
                error("SMaps: no mapping found in '%s'" % self._filename)
        except BaseException, exc:
            errmsg = "SMaps: error opening smaps file '%s': %s %s" % (self._filename, type(exc), str(exc))
            error(errmsg)
            raise


    def _parseFile(self, smapsbuffer):
        '''
            private helper function to parse the smaps buffer to the class fields
            buffer -- buffer containing the smaps file
        '''
        self.maplist = []
        currententry = None
        for l in smapsbuffer.splitlines():
            m = re.match(r'''([0-9a-f]+)-([0-9a-f]+)\s+([rwxsp-]+)\s+([0-9a-f]+)\s+([0-9a-f]+):([0-9a-f]+)\s+(\d+)(.+)''', l)
            if m != None:
                # mapping header, create a new MapEntry
                start, stop, access, offset, devmaj, devmin, inode, name = m.groups()
                
                currententry = MapEntry()
                currententry.name         = name.strip()
                currententry.startaddress = int(start,16)
                currententry.stopaddress  = int(stop,16)
                currententry.setAccess(access)
                currententry.offset       = int(offset,16)
                currententry.devicemajor  = int(devmaj,16)
                currententry.deviceminor  = int(devmin,16)
                currententry.inode        = int(inode)
                
                self.maplist.append(currententry)
            else:
                # see if it's a field line following MapEntry
                m = re.match(r'''(.+?):\s+(\d+)\s+kB''', l)
                if m != None:
                    if currententry:
                        prop, value = m.groups()
                        currententry.setField(prop, value)
                    else:
                        warning("_parseFile: missing mapping header line before field line '%s'" % l.strip())
                else:
                    warning("_parseFile: unable to parse line: %s" % l.strip())
                    continue # nothing found, shouldn't happen
   



if __name__ == '__main__':
    # enable logging
    logging.basicConfig(level = logging.DEBUG)
    
    # some simple tests
    try:   
        s = SMaps(-1)
        raise ValueError, "Error: success with incorrect name"
        sys.exit(1)
    except IOError, exc:
        print("SUCCESS: 'File does not exist' test")

    try:   
        s = SMaps(os.getpid())
    except BaseException, exc:
        print("unexpected exception: %s %s" % (exc, type(exc)))
        raise
        sys.exit(1)

