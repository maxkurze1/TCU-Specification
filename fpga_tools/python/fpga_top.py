
import modids
import noc
import router
import ethernet
import dram
import pm
import uart
import regfile

import os
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
    def __init__(self, fpga_sw=0, use_uart=False):
        if fpga_sw >= 15:
            print("Invalid FPGA IP address selected! Only use 192.168.42.240-254")
            raise ValueError

        self.fpga_ip_addr = str(IPv4Address(int(IPv4Address(self.FPGA_IP)) + fpga_sw))

        #DIP switch determines Chip-ID - currently disabled
        #chipid = fpga_sw
        chipid = 0

        #periphery
        if use_uart:
            self.uart = uart.UART('/dev/ttyUSB1')

        #NOC
        self.nocif = noc.NoCethernet((self.fpga_ip_addr, self.FPGA_PORT))
        self.eth_rf = ethernet.EthernetRegfile(self.nocif, (chipid, modids.MODID_ETH))

        #regfile
        #self.regfile = regfile.REGFILE(self.nocif, (chipid, modids.MODID_PM5))

        #NoC router
        self.router_count = router.Router.ROUTER_CNT
        self.router = [router.Router(self.nocif, (chipid, modids.MODID_ROUTER[x]), x) for x in range(self.router_count)]

        #DRAM
        self.dram1 = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM1))
        self.dram2 = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM2))

        #PMs
        self.pm_count = len(modids.MODID_PMS)
        self.pms = [pm.PM(self.nocif, (chipid, modids.MODID_PMS[x]), x) for x in range(self.pm_count)]


    def tear(self):
        self.noccomm.tear()
        self.uart.close()
