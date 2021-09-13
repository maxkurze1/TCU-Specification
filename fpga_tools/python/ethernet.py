
from ipaddress import IPv4Address
from time import sleep

import noc
import memory
from tcu import TCU


class EthernetRegfile(memory.Memory):
    def __init__(self, nocif, nocid):
        self.shortname = "eth_rf"
        self.name = "Ethernet Regfile"
        self.rf = memory.Memory(nocif, nocid)
        self.nocarq = noc.NoCARQRegfile(nocid)

    def tcu_status(self):
        status = self.rf[TCU.TCU_REGADDR_TCU_STATUS]
        return (status & 0xFF, (status >> 8) & 0xFF, (status >> 16) & 0xFF)

    def tcu_reset(self):
        self.rf[TCU.TCU_REGADDR_TCU_RESET] = 1

    def tcu_ctrl_flit_count(self):
        flits = self.rf[TCU.TCU_REGADDR_TCU_CTRL_FLIT_COUNT]
        flits_rx = flits & 0xFFFFFFFF
        flits_tx = flits >> 32
        return (flits_tx, flits_rx)

    def tcu_byp_flit_count(self):
        flits = self.rf[TCU.TCU_REGADDR_TCU_BYP_FLIT_COUNT]
        flits_rx = flits & 0xFFFFFFFF
        flits_tx = flits >> 32
        return (flits_tx, flits_rx)

    def tcu_drop_flit_count(self):
        return self.rf[TCU.TCU_REGADDR_TCU_DROP_FLIT_COUNT] & 0xFFFFFFFF

    def tcu_error_flit_count(self):
        return self.rf[TCU.TCU_REGADDR_TCU_DROP_FLIT_COUNT] >> 32

    def system_reset(self):
        self.rf[TCU.TCU_REGADDR_CORE_CFG_START] = 1
        print("FPGA Reset...")
        sleep(5)   #need some time to get FPGA restarted

        #check if link is up
        link_check = 3
        while link_check > 0:
            eth_status = self.getStatusVector()
            intpyh_linkupandsync = eth_status & 0x3
            extphy_linkup = eth_status & 0x80 #for SGMII only
            if intpyh_linkupandsync == 0 or extphy_linkup == 0:
                #check again
                link_check -= 1
                sleep(1)
            else:
                link_check = -1

        if link_check != -1:
            print("Could not reset FPGA!")

    def getStatusVector(self):
        return self.rf[TCU.TCU_REGADDR_CORE_CFG_START+0x8]

    def getUDPstatus(self):
        return self.rf[TCU.TCU_REGADDR_CORE_CFG_START+0x10]

    def getRXUDPerror(self):
        return self.rf[TCU.TCU_REGADDR_CORE_CFG_START+0x18]

    def getMACstatus(self):
        return self.rf[TCU.TCU_REGADDR_CORE_CFG_START+0x20]

    def getFPGAIP(self):
        return IPv4Address(self.rf[TCU.TCU_REGADDR_CORE_CFG_START+0x28] & 0xFFFFFFFF)

    def getFPGAMAC(self):
        return self.rf[TCU.TCU_REGADDR_CORE_CFG_START+0x30]
