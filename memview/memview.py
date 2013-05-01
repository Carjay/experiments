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

import logging
import os
import pagemap
import smaps
import struct
import sys


lg = logging.getLogger("memview")
info = lg.info
logging.basicConfig(level = logging.DEBUG)

def getHumanReadableSize(size):
    '''
        return human readable size as string
    '''
    sz = float(size)
    
    if sz <= (1<<20):
        return "%.02f kByte" % (sz / (1<<10))
    if sz <= (1<<30):
        return "%.02f MByte" % (sz / (1<<20))
    if sz <= (1<<40):
        return "%.02f GByte" % (sz / (1<<30))
    else:
        return "%.02f TByte" % (sz / (1<<40))



def main():
    if len(sys.argv) > 1:
        pid = int(sys.argv[1])
    else:
        pid = os.getpid()

    # retrieve all process mapping information
    s = smaps.SMaps(pid)

    # look for the [heap] mapping
    for me in s.maplist:
        # vsyscall is above the task virtual address space so pagemap
        # does not return anything for it
        if me.name == "[vsyscall]":
            continue

        if me.name != "[heap]":
            continue

        print "mapping %x-%x '%s' %s:" % (me.startaddress, me.stopaddress, me.name, getHumanReadableSize(me.size))
        
        # hm, how does this relate to mmupagesize...
        pagesize = me.kernelpagesize
        
        # there me.size but I've seen it differ from the actual address range
        totalcnt   = 0
        presentcnt = 0
        swapcnt    = 0

        pm = pagemap.PageMap(pid)
        
        pageinfolist = pm.getPageInfo(me.startaddress, me.stopaddress, pagesize)
        totalcnt = len(pageinfolist)

        drawmap = [] # '.' = not mapped 'x' = active 's' = swapped

        for pi in pageinfolist:
            if pi.present:
                presentcnt += 1
                if pi.swapped:
                    swapcnt += 1
                    drawmap.append('s')
                else:
                    drawmap.append('x')
            else:
                drawmap.append('.')
               
            
        #print "present:%s swapped:%s pfn:%s swaptype:%s swapoffset:%s pgshift:%s reserved:%s" % (pi.present, pi.swapped, pi.pfn, pi.swaptype, pi.swapoffset, pi.pgshift, pi.reserved)
            
        totalsize     = totalcnt * pagesize
        presentsize   = presentcnt * pagesize
        notmappedsize = (totalcnt - presentcnt) * pagesize
        swapsize      = swapcnt * pagesize

        print ("  %d pages (%s), %d present (%s), %d not mapped (%s), %d swapped (%s)" % (totalcnt, getHumanReadableSize(totalsize),
                                                                                        presentcnt, getHumanReadableSize(presentsize),
                                                                                        totalcnt - presentcnt, getHumanReadableSize(notmappedsize),
                                                                                        swapcnt, getHumanReadableSize(swapsize)
                                                                                        ))
        # draw map
        width = 80
        pg    = len(drawmap) / width
        pgrem = len(drawmap) % width
        
        for idx in range(pg):
            mapstr = ''.join(drawmap[idx*width:(idx+1)*width])
            print("0x%08x: %s" % (me.startaddress + (idx*width*pagesize), mapstr))
        
        if pgrem > 0:
            mapstr = ''.join(drawmap[pg*width:])
            print("0x%08x: %s" % (me.startaddress + (pg*width*pagesize), mapstr))
        
        #for pi in pageinfolist:
        #    print pi



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass


