#!/usr/bin/env python

import traceback
from time import sleep

import modids
import fpga_top
from fpga_utils import FPGA_Error

TESTCASE_ADDR = 0x10071000
TESTCASE_RESULT_DATA = 0xE

binfile = "targets/rocket_boot"



def main():
    print("init!")

    #get connection to FPGA, SW12=0000b -> chipid=0
    fpga_inst = fpga_top.FPGA_TOP(0)
    test_result = 0

    rocket_cores = fpga_inst.pms


    #test all Rockets
    for rocket in rocket_cores:
        print("Test Rocket Core %d" % rocket.pm_num)

        #first disable core to start from initial state
        rocket.stop()

        print("Enable core")
        rocket.start()
        print("Core enabled: %d" % rocket.getEnable())

        #init mem
        rocket.mem.write_elf(binfile)

        #init test addr with random value
        rocket.mem[TESTCASE_ADDR] = 0x456fff

        #start core
        print("Start core")
        rocket.rocket_start()


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
