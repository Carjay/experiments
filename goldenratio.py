#!/usr/bin/env python

# Copyright (C) 2012, Carsten Juttner <carjay@gmx.net>
# there are no restrictions on copying or usage
# feel free to explore

import os
import sys
import math

# how to compute the golden ratio using a (truncated) continued fraction:

# the golden ratio is the answer to the question:
# "for any given a, which b satisfies the equation:
#   (a+b)/a = a/b"


def usage():
    print("%s <iterations>" % os.path.basename(sys.argv[0]))


def main():
    iterations = 30 # default
    if len(sys.argv) > 1:
        try:
            iterations = int(sys.argv[1])
        except ValueError:
            usage()
            return

    # what we're doing here is generating a continued fraction
    # (by starting at the bottom!):
    #       1
    # 1 + -----
    #     1 +   1
    #         -----
    #         1 +   1
    #             -----
    #             1 +   1
    #                 -----
    #                 1 + ...

    phi = 1.0 # not important since it works for any a, so use 1.0
    #phi = (1+math.sqrt(5))/2  # the "real" value expressed as an irrational number
    prevphi = phi
    ulpiterations = iterations
    for i in range(iterations):
        print phi
        phi = 1.0/(1.0+phi)
        if prevphi == phi:
            ulpiterations = i-1
            break
        prevphi = phi
    phi += 1.0 # reached the top
    if ulpiterations != iterations:
        print("Golden ratio result after %d iterations (accuracy limit reached after %d):" % (iterations, ulpiterations))
    else:
        print("Golden ratio result after %d iterations:" % iterations)
    print("  phi:%.010f" % (phi))
    print("1/phi:%.010f" % (1.0/phi))
    print("if correctly calculated, both must differ only by 1\n")
    
    # proof
    print("test that the equation b=a/phi satisfies a/(a+b) for some given a:")
    print("if correctly calculated, both results must match (they are the golden ratio)")
    for a in (1,2,5,10,50,100):
        b = a / phi
        print("a:%.0f -> b: %.012f" % (a,b))
        print("  a/b    :   %.012f" % (a/b))
        print(" (a+b)/a :   %.012f\n" % ((a+b)/a))
        

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
