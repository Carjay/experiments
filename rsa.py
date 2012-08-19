#!/usr/bin/env python

# Copyright (C) 2011, Carsten Juttner <carjay@gmx.net>
# there are no restrictions on copying or usage
# feel free to explore

# python script that demonstrates how RSA actually works using a real ssh key
# (possible since python uses arbitrary integer representation).
#
# the string encryption/decryption part is only for demonstration purposes
# and would not be used like this in a real world application!

import math
import os
import re
import sys

try:
    import pyasn1
except ImportError:
    print("needs pyasn1 (available on PyPi)")
    sys.exit(1)

import base64

# RSA
# the string we will encrypt/decrypt
enc = "RSA encryption is pretty simple"


def gcd(a,b):
    # greatest common denominator, using the euclidean algorithm
    while b:
        a, b = b, a%b
    return a


def egcd(a,b):
    # extended greatest common denominator,
    # return a tuple (x,y) that solves a*x + b*y = gcd(a,b)
    if b == 0:
        return (1,0)
    else:
        q, r = a/b, a%b
        s, t = egcd(b,r)
        return (t, s-(q*t))
    

def main():
    # we need the unencrypted RSA key in "PEM" format here.
    # To get this from an ssh key in .ssh/id_rsa use the openssl command line tool:
    #
    # $ openssl rsa -in <path to id_rsa> > privatekey.txt
    #
    # !CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION!
    #   this will save the plain PRIVATE(!) ssh key to privatekey.txt, so do
    #   not keep this lying around if the key is important
    # !CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION!
        
    #rsafile = os.path.join(os.getenv("HOME"), ".ssh/id_rsa")
    rsafile = "privatekey.txt"
    keybuf = open(rsafile, 'rt').read()

    m = re.match('.*-----BEGIN RSA PRIVATE KEY-----(.*)-----END RSA PRIVATE KEY', keybuf, re.DOTALL)
    if m:
        basekey = m.group(1)
    else:
        print("unable to find RSA signature\n")
        return
    
    # leave this to the professionals, extract the data from
    # the ASN.1 BER encoded data using pyasn1
    binkey = base64.decodestring(basekey)
    from pyasn1.codec.ber import decoder
    asn1obj = decoder.decode(binkey)

    if len(asn1obj[0]) != 9:
        print("strange asn.1, expected 9 objects (only plaintext keys supported)")
        return
    
    # RSA only needs e,p and q, the rest is to make implementations
    # simpler by offering some precomputed values (n, d, dp, dq and invq)
    (_,n,e,d,p,q,dp,dq,invq) = [ int(v) for v in asn1obj[0] ]
    
    # sanity check, compare saved modulus to the calculated version.
    if n != p*q:
        print("error: n != p*q")
        return
        
    print("chosen modulus n=p*q: 0x%x = 0x%x * 0x%x" % (n, p ,q))

    # we can only recover the original if 0 < cryptval < n,
    # so for simplicity, let's only support ASCII without 0x00
    if n < 256:
        print("modulus is too small, choose p and q so that it is greater 256")
        return

    totient = (p-1)*(q-1)
    print("totient for product is %d" % totient)

    is_e_coprime = gcd(e, totient)
    sys.stdout.write("checking gcd of totient and e ")
    if is_e_coprime != 1:
        print("... no, e was chosen wrong!")  
        return
    else:
        print("... ok, they are coprime")

    # public key:  e (public exponent) and common modulus n
    # encryption: crypttext = plaintext^e (mod n)
    print("chosen encryption exponent: %d" % e)
    cryptvals = [ pow(ord(v),e,n) for v in enc ]
      
    # calculate e^(-1) mod totient (multiplicative inverse of e mod totient)
    # using the extended euclidean algorithm for gcd
    calcd, _ = egcd(e,totient)
    if calcd < 0: # need a positive d for exponentiation
        calcd %= totient

    if d != calcd:
        print("provided decryption exponent does not match calculated")
    
    # private key: d (private exponent) and common modulus n
    # decryption: crypttext^d (mod n)
    dectext = ''.join([chr(pow(v,d,n)) for v in cryptvals])
    print "decrypted text: '%s'" % dectext

    

try:
    main()
except KeyboardInterrupt:
    pass
