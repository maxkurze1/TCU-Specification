#!/usr/bin/env python3

from sys import argv


inhexfile = argv[1]
outhexfile = argv[2]
#inhexfile = "main.hex"
#outhexfile = "main.hex2"

inlinecount = 0
last_zero = False

with open(inhexfile, "r") as fin:
    with open(outhexfile, "w") as fout:
        fout.write("@00000000\n")
        for inhexline in fin:
            this_zero = True if inhexline == "0000000000000000\n" else False

            if last_zero and not this_zero:
                fout.write("@%08x\n" % inlinecount)

            if not this_zero:
                fout.write(inhexline)
                last_zero = False
            else:
                last_zero = True

            inlinecount += 1

