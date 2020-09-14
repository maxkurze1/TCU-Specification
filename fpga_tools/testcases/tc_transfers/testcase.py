#!/usr/bin/env python3

import traceback
import sys

import fpga_top
from noc import NoCmonitor
from fpga_utils import FPGA_Error

def small_transfers(mem):
    print("Testing small read and write transfers ... ", end="")

    # clear everything
    mem.write_words(0, [0] * 16)

    # write different amounts
    test_data = [1, 2, 3, 4, 5, 6, 7, 8]
    for i in range(1, len(test_data)):
        mem.write_words(0, test_data[0:i])
        words = mem.read_words(0, i)
        assert words == test_data[0:i]

    # read and write unaligned
    mem.write_words(0, [0] * 16)
    test_bytes = bytes(test_data + test_data)
    for i in range(0, len(test_bytes)):
        mem.write_bytes(i, test_bytes[i:])
        b = mem.read_bytes(i, len(test_bytes) - i)
        assert b == test_bytes[i:]
    for i in range(1, len(test_bytes)):
        mem.write_bytes(0, test_bytes[0:i])
        b = mem.read_bytes(0, i)
        assert b == test_bytes[0:i]

    print("SUCCESS")

def large_transfers(mem):
    print("Testing large read and write transfers ... ", end="")

    with open("pat.bin", "rb") as f:
        content = f.read()

    for amount in [512, 4 * 1024, 32 * 1024, 1024 * 1024]:
        mem.write_bytes_checked(0, content[0:amount], True)
        mem.write_bytes_checked(0, content[0:amount], False)

    # test unaligned offsets and sizes
    for amount in [511, 513, 1022, 1026, 1001]:
        for off in range(0, 16):
            # TODO unsupported mem.write_bytes_checked(off, content[0:amount], True)
            mem.write_bytes_checked(off, content[0:amount], False)

    print("SUCCESS")

def main():
    # get connection to FPGA, SW12=0000b -> chipid=0
    fpga_inst = fpga_top.FPGA_TOP(0)
    # fpga_inst.eth_rf.system_reset()

    mon = NoCmonitor()

    mem = fpga_inst.dram1.mem

    print("Starting test")

    small_transfers(mem)
    large_transfers(mem)

    print("All tests succeeded")

try:
    main()
except FPGA_Error as e:
    sys.stdout.flush()
    traceback.print_exc()
except Exception:
    sys.stdout.flush()
    traceback.print_exc()
except KeyboardInterrupt:
    print("interrupt")
