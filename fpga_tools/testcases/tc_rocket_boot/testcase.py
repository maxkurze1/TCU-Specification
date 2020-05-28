#!/usr/bin/env python

import traceback
from time import sleep

import modids
from noc import noc_packet
import fpga_top
from fpga_utils import FPGA_Error

TESTCASE_ADDR = 0x10071000
TESTCASE_RESULT_DATA = 0xE

memfile = "targets/rocket_boot.hex"



def main():
    print("init!")
    
    #get connection to FPGA, SW12=0000b -> chipid=0
    fpga_inst = fpga_top.FPGA_TOP(0)
    test_result = 0

    rocket_cores = [fpga_inst.pm6, fpga_inst.pm7, fpga_inst.pm3, fpga_inst.pm5]

    #test all 4 Rockets
    for rocket in rocket_cores:
        print("Test Rocket Core ", rocket.pm_num)

        #first disable core to start from initial state
        rocket.stop()

        print("Enable core")
        rocket.start()
        print("Core enabled: %d" % rocket.getEnable())
        
        #init mem (Rocket DRAM starts at 0x10000000)
        rocket.initMem(memfile, 0x10000000)

        #init test addr with random value
        rocket.mem[TESTCASE_ADDR] = 0x456fff

        #start core (via interrupt pin 0)
        print("Start core")
        rocket.rocket_setInt(0, 1)
        rocket.rocket_setInt(0, 0)


        #wait for core to complete
        sleep(1)


        print("Check at test addr")
        core_result = rocket.mem[TESTCASE_ADDR]
        print("core_result: 0x%x" % core_result)

        if (core_result & 0xF) != TESTCASE_RESULT_DATA:
            test_result += 1
        
        print("Disable core")
        rocket.stop()

        print("Core enabled: %d" % rocket.getEnable())
        print("")
    


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
