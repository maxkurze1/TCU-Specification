#!/usr/bin/env python

import traceback
from time import sleep

import modids
import fpga_top
from fpga_utils import FPGA_Error

TESTCASE_ADDR = 0x10071000
TESTCASE_PASSED = 0x1111_1111

memfile = "targets/standalone.hex"



def main():
    print("init!")

    #get connection to FPGA, SW12=0000b -> chipid=0
    fpga_inst = fpga_top.FPGA_TOP(0)
    test_result = 0


    #first disable core to start from initial state
    fpga_inst.pm7.stop()

    #start core
    fpga_inst.pm7.start()


    #init mem
    #SW is compiled for Rocket core at PM7
    fpga_inst.pm7.initMem(memfile, 0x10000000)

    #init test addr
    fpga_inst.pm7.mem[TESTCASE_ADDR] = 0x456fff

    #start core
    fpga_inst.pm7.rocket_start()


    #wait for core to complete
    sleep(1)


    core_result = fpga_inst.pm7.mem[TESTCASE_ADDR]
    print("core_result: 0x%x" % core_result)

    if (core_result & 0xFFFF_FFFF) != TESTCASE_PASSED:
        test_result += 1


    fpga_inst.pm7.stop()


    if (test_result == 0):
        print("TESTCASE PASSED!")
    else:
        print("TESTCASE FAILED!")





try:
    main()
except FPGA_Error as e:
    traceback.print_exc()
except Exception:
    traceback.print_exc()
except KeyboardInterrupt:
    print("interrupt")
