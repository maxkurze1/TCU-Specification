
import bic1_modids
import modids
import noc
import router
import ethernet
import dram
import pm
from tcu import TCU

import sys
from ipaddress import IPv4Address


class fpga:
    def getmod(self, ident):
        if isinstance(ident, int):
            for mod in self.mods:
                try:
                    if mod.thadr[1] == ident:
                        return mod
                except AttributeError:
                    pass
        if isinstance(ident, str):
            for mod in self.mods:
                try:
                    if mod.shortname == ident:
                        return mod
                except AttributeError:
                    pass
        return None


class FPGA_TOP(fpga):
    #dedicated addr range for FPGA: 192.168.42.240-254
    FPGA_IP = '192.168.42.240'
    FPGA_PORT = 1800
    def __init__(self, version, fpga_sw=0, reset=0):
        if fpga_sw >= 15:
            print("Invalid FPGA IP address selected! Only use 192.168.42.240-254")
            raise ValueError

        self.fpga_ip_addr = str(IPv4Address(int(IPv4Address(self.FPGA_IP)) + fpga_sw))

        print("Connect to FPGA (fpga_ip={}, fpga_port={})".format(self.fpga_ip_addr, self.FPGA_PORT))
        if reset: print("FPGA Reset...")
        sys.stdout.flush()

        #DIP switch determines Chip-ID of FPGA (z-coordinate of chip-is is unused)
        fpga_chipid = fpga_sw << 2

        #bic1_1 is south of FPGA (incr. y-coord)
        bic1_1_chipid = fpga_chipid + 4

        #bic1_2 is north of FPGA (decr. y-coord)
        bic1_2_chipid = fpga_chipid - 4

        tcu = TCU(version)

        #FPGA NOC
        self.nocif = noc.NoCethernet(tcu, (self.fpga_ip_addr, self.FPGA_PORT), fpga_chipid, reset)
        self.eth_rf = ethernet.EthernetRegfile(tcu, self.nocif, (fpga_chipid, modids.MODID_ETH))

        #FPGA NoC router
        self.router_count = router.Router.ROUTER_CNT
        self.router = [router.Router(self.nocif, (fpga_chipid, modids.MODID_ROUTER[x]), x) for x in range(self.router_count)]

        #Bic1 NoC router
        self.bic1_1_router_count = len(bic1_modids.MODID_ROUTER)
        self.bic1_1_router = [router.Router(self.nocif, (bic1_1_chipid, bic1_modids.MODID_ROUTER[x]), x) for x in range(self.bic1_1_router_count)]
        self.bic1_2_router_count = len(bic1_modids.MODID_ROUTER)
        self.bic1_2_router = [router.Router(self.nocif, (bic1_2_chipid, bic1_modids.MODID_ROUTER[x]), x) for x in range(self.bic1_2_router_count)]

        #DRAM (on FPGA)
        self.dram1 = dram.DRAM(tcu, self.nocif, (fpga_chipid, modids.MODID_DRAM1))
        self.dram2 = dram.DRAM(tcu, self.nocif, (fpga_chipid, modids.MODID_DRAM2))

        #Bic1 PMs
        self.pm_count = 2*len(bic1_modids.MODID_PMS)
        self.pms = [pm.PM(tcu, self.nocif, (bic1_1_chipid, bic1_modids.MODID_PMS[x]), x) for x in range(len(bic1_modids.MODID_PMS))] + [pm.PM(tcu, self.nocif, (bic1_2_chipid, bic1_modids.MODID_PMS[x]), x) for x in range(len(bic1_modids.MODID_PMS))]

        self.bic1_1_pms = self.pms[0:len(bic1_modids.MODID_PMS)-1]
        self.bic1_2_pms = self.pms[len(bic1_modids.MODID_PMS):self.pm_count-1]


    def tear(self):
        self.noccomm.tear()
