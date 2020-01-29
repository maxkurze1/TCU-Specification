#!/usr/bin/env python

import traceback

import time

import modids
from noc import noc_packet
import fpga_top
from fpga_utils import FPGA_Error



TESTCASE_ADDR = 0x41000
TESTCASE_PASSED = 0x1111_1111

memfile = "tc_dtu.hex"



def main():
    print("init!")
    
    fpga_inst = fpga_top.FPGA_TOP(0)
    fpga_inst.nocif.noclogging = True
    test_result = 0


    fpga_inst.pm6.stop()

    #init mem
    fpga_inst.pm6.initMem(memfile)
    
    

    #init test addr
    fpga_inst.pm6.mem[TESTCASE_ADDR] = 0xAFFE_AFFE


    #start core
    fpga_inst.pm6.start()


    time.sleep(1)

    
    core_result = fpga_inst.pm6.mem[TESTCASE_ADDR]
    print("core_result: 0x%08x_%08x" % (core_result >> 32, core_result & 0xFFFFFFFF))

    dbg_result = fpga_inst.pm6.mem[TESTCASE_ADDR+0x8]
    print("dbg_result: 0x%08x_%08x" % (dbg_result >> 32, dbg_result & 0xFFFFFFFF))

    if (core_result & 0xFFFF_FFFF) != TESTCASE_PASSED:
        test_result += 1
    


    #print("trap mode: %d" % fpga_inst.pm6.getTrap())
    #print("stack addr: 0x%x" % fpga_inst.pm6.getStackAddr())


    fpga_inst.pm6.stop()


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
