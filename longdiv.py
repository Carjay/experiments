#!/usr/bin/python

# Copyright (C) 2013, Carsten Juttner <carjay@gmx.net>
# there are no restrictions on copying or usage
# feel free to explore

# silly script to calculate a full (all numbers) division for two given
# integer input numbers.
# in case the result is periodic, it will display the period
# (which is basically why I wrote it)

import os
import sys

def usage():
    print("Usage: %s <numerator> <denominator>" % os.path.basename(sys.argv[0]))


def main():
    if len(sys.argv) != 3:
        usage()
        return 1
    try:
        num, denom = map(int,sys.argv[1:3])
    except ValueError:
        print("Error:input arguments %s are invalid integer numbers" % ','.join(sys.argv[1:3]))
        return 1
    
    if denom == 0:
        print("Error: denominator cannot be 0.")
        return 1
    print ("calculating %d/%d" % (num,denom))
   
    # (count, pos) of already returned remainders to get the period
    remdict = dict()
   
    fullnumlist = []
    pos = 0

    rem = 1
    curnum = num

    while (rem != 0) and (remdict.get(rem,[0,0])[0] <= 1):
        div = curnum / denom
        rem = curnum % denom
        fullnumlist.append(str(div))
        remdict[rem]     = remdict.get(rem, [0,pos])
        remdict[rem][0] += 1 # increment count
        pos += 1
        if rem != 0:
            curnum = rem * 10
    if len(fullnumlist) > 1:
        fullnumlist.insert(1, '.')
    number = ''.join(fullnumlist)
    sys.stdout.write(number)
    if rem != 0:
        period = ''.join(fullnumlist[remdict[rem][1]+2:])
        print("... (periodic part %s (%d digit%s)" % (period, len(period), ['','s'][len(period)>1]))
    else:
        print("")
        
 


try:
    main()
except KeyboardInterrupt:
    pass
