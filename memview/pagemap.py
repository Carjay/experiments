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

import errno
import logging
import struct

lh = logging.getLogger(__name__)
info    = lh.info
debug   = lh.debug
error   = lh.error
warning = lh.warning


class PageInfo:
    '''
        holds info about one page
    '''
    virtualaddress = None
    
    present     = None
    swapped     = None
    pfn         = None
    swaptype    = None
    swapoffset  = None
    pgshift     = None
    reserved    = None

    # extra info that requires root permissions
    mapcount    = None
    pageflags   = None

    # pageflag bits
    KPF_LOCKED        = 0
    KPF_ERROR         = 1
    KPF_REFERENCED    = 2
    KPF_UPTODATE      = 3
    KPF_DIRTY         = 4
    KPF_LRU           = 5
    KPF_ACTIVE        = 6
    KPF_SLAB          = 7
    KPF_WRITEBACK     = 8
    KPF_RECLAIM       = 9
    KPF_BUDDY         = 10
    KPF_MMAP          = 11
    KPF_ANON          = 12
    KPF_SWAPCACHE     = 13
    KPF_SWAPBACKED    = 14
    KPF_COMPOUND_HEAD = 15
    KPF_COMPOUND_TAIL = 16
    KPF_HUGE          = 17
    KPF_UNEVICTABLE   = 18
    KPF_HWPOISON      = 19
    KPF_NOPAGE        = 20
    KPF_KSM           = 21
    KPF_THP           = 22
    
    def __repr__(self):
        '''
            return string representation of PageInfo fields
        '''
        s = "<PageInfo virtualaddress:0x%x" % self.virtualaddress
        if self.present:
            s+= " present shift:%d reserved %d" % (self.pgshift, self.reserved)
            if self.swapped == 0:
                s+= " pfn:%d" % (self.pfn)
            else:
                s+= " swapped type:%d offset:%d" % (self.swaptype, self.swapoffset)
        else:
            s += " not present"

        if self.mapcount:
            s += " mapcount:%d" % self.mapcount

        if self.pageflags:
            s += " %s" % self.getFlagString()

        s += ">"            
        return s
    
    
    def __init__(self, virtualaddress, val):
        '''
            initialises PageInfo
            virtualaddress -- virtual address for this pageinfo
            val            -- value as retrieved from the procfs pagemap
        '''
        self.virtualaddress = virtualaddress
        self.setInfo(val)
    
    
    def setInfo(self, val):
        '''
            set info fields from value taken from the procfs pagemap file
        '''
        #    * Bits 0-54  page frame number (PFN) if present
        #    * Bits 0-4   swap type if swapped
        #    * Bits 5-54  swap offset if swapped
        #    * Bits 55-60 page shift (page size = 1<<page shift)
        #    * Bit  61    reserved for future use
        #    * Bit  62    page swapped
        #    * Bit  63    page present
        
        self.swapped    = None
        self.pfn        = None
        self.swaptype   = None
        self.swapoffset = None
        self.pgshift    = None
        self.reserved   = None

        self.present            = (val & 0x8000000000000000) >> 63
        if self.present:
            self.swapped        = (val & 0x4000000000000000) >> 62
            if self.swapped == 0:
                self.pfn        = (val & 0x007fffffffffffff) >>  0
            else:
                self.swaptype   = (val & 0x000000000000001f) >>  0
                self.swapoffset = (val & 0x007fffffffffffe0) >>  5
            self.pgshift        = (val & 0x1f80000000000000) >> 55
            self.reserved       = (val & 0x2000000000000000) >> 61
    
      
    def getFlagString(self):
        '''
            return human readable string for flags
        '''
        flags = []
        if self.pageflags & (1 << self.KPF_LOCKED):
            flags.append("LOCKED")
        if self.pageflags & (1 << self.KPF_ERROR):
            flags.append("ERROR")            
        if self.pageflags & (1 << self.KPF_REFERENCED):
            flags.append("REFERENCED")            
        if self.pageflags & (1 << self.KPF_UPTODATE):
            flags.append("UPTODATE")            
        if self.pageflags & (1 << self.KPF_DIRTY):
            flags.append("DIRTY")            
        if self.pageflags & (1 << self.KPF_LRU):
            flags.append("LRU")            
        if self.pageflags & (1 << self.KPF_ACTIVE):
            flags.append("ACTIVE")            
        if self.pageflags & (1 << self.KPF_SLAB):
            flags.append("SLAB")            
        if self.pageflags & (1 << self.KPF_WRITEBACK):
            flags.append("WRITEBACK")            
        if self.pageflags & (1 << self.KPF_RECLAIM):
            flags.append("RECLAIM")            
        if self.pageflags & (1 << self.KPF_BUDDY):
            flags.append("BUDDY")            
        if self.pageflags & (1 << self.KPF_MMAP):
            flags.append("MMAP")            
        if self.pageflags & (1 << self.KPF_ANON):
            flags.append("ANON")            
        if self.pageflags & (1 << self.KPF_SWAPCACHE):
            flags.append("SWAPCACHE")            
        if self.pageflags & (1 << self.KPF_SWAPBACKED):
            flags.append("SWAPBACKED")            
        if self.pageflags & (1 << self.KPF_COMPOUND_HEAD):
            flags.append("COMPOUND_HEAD")            
        if self.pageflags & (1 << self.KPF_COMPOUND_TAIL):
            flags.append("COMPOUND_TAIL")            
        if self.pageflags & (1 << self.KPF_HUGE):
            flags.append("HUGE")            
        if self.pageflags & (1 << self.KPF_UNEVICTABLE):
            flags.append("UNEVICTABLE")            
        if self.pageflags & (1 << self.KPF_HWPOISON):
            flags.append("HWPOISON")            
        if self.pageflags & (1 << self.KPF_NOPAGE):
            flags.append("NOPAGE")            
        if self.pageflags & (1 << self.KPF_KSM):
            flags.append("KSM")            
        if self.pageflags & (1 << self.KPF_THP):
            flags.append("THP")
        return ','.join(flags)

    

class PageMap:
    '''
        accessor class for the linux procfs pagemap file
    '''
    pid          = None # pid for which the information is retrieved
    
    _pagemapfile = None

    def __init__(self, pid):
        '''
            create PageMap instance
        '''
        self.pid = pid
        self._pagemapfile = "/proc/%d/pagemap" % self.pid
    

    def getPageInfo(self, startaddress, stopaddress, pagesize):
        '''
            queries info about the given range
            
            startaddress -- start address
            stopaddress  -- stop address

            returns a list of PageInfo instances
        '''
        ret = []

        mapsize  = stopaddress - startaddress
        startpfn = startaddress / pagesize
        stoppfn  = stopaddress / pagesize

        fhpgcnt   = None
        fhpgflags = None

        # get access to both count and flags files if possible
        try:
            fhpgcnt   = open("/proc/kpagecount", 'rb')
            fhpgflags = open("/proc/kpageflags", 'rb')
        except IOError, exc:
            if exc.errno == errno.EACCES:
                warning("getPageInfo: no permission to get extra page info from kernel, start with elevated privileges if you want that type of info")
       
        startoffset = startpfn * 8 # size of each entry
        try:
            with open(self._pagemapfile, 'rb') as fh:
                fh.seek(startoffset)
                readsize = (stoppfn-startpfn) * 8
                
                pagemapinfo = fh.read(readsize)
                if len(pagemapinfo) != readsize:
                    # the kernel did not give us what we want, e.g. the vsyscall page does not return valid info
                    error("only read %d bytes from pagemap '%s', expected %d" % (len(pagemapinfo), self._pagemapfile, readsize))
                else:
                    pagemapvals = struct.unpack("=%dQ" % (stoppfn-startpfn), pagemapinfo)

                    for idx, val in enumerate(pagemapvals):
                        vaddr = startaddress + (idx * pagesize)
                        pi = PageInfo(vaddr, val)
                        
                        if pi.pfn != None:
                            if fhpgcnt:
                                fhpgcnt.seek(pi.pfn * 8)
                                pgcnt = fhpgcnt.read(8)
                                if len(pgcnt):
                                    pgcnt, = struct.unpack('=Q', pgcnt)
                                    pi.mapcount = pgcnt
                                else:
                                    warning("unable to read mapcount for PFN %d" % pi.pfn)
                            if fhpgflags:
                                fhpgflags.seek(pi.pfn * 8)
                                pgflags = fhpgflags.read(8)
                                if len(pgflags):
                                    pgflags, = struct.unpack('=Q', pgflags)
                                    pi.pageflags = pgflags
                                else:
                                    warning("unable to read pageflags for PFN %d" % pi.pfn)
                        
                        ret.append(pi)
                
        except BaseException, exc:
            error("getPageInfo: error opening  pagemap file '%s': %s %s" % (self._pagemapfile, type(exc), str(exc)))
            raise

        return ret




