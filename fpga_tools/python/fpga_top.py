
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
    def __init__(self, chipid=0, use_uart=False):
        self.fpga_ip_addr = str(IPv4Address(int(IPv4Address(self.FPGA_IP)) + chipid))
        print("Connect to FPGA at %s:%d" % (self.fpga_ip_addr, self.FPGA_PORT))

        if not os.path.isdir("log"):
            os.mkdir("log")
        #self.jtagcomm = jtag.JTAGComm('th4')


        #periphery
        #self.fpgaif = fpgaif.FPGA_if(self.jtagcomm, self.noccomm)
        if use_uart:
            self.uart = uart.UART('/dev/ttyUSB1')

        #NOC
        self.nocif = noc.NoCethernet((self.fpga_ip_addr, self.FPGA_PORT))
        self.eth_rf = ethernet.EthernetRegfile(self.nocif, (chipid, modids.MODID_ETH))

        #regfile
        #self.regfile = regfile.REGFILE(self.nocif, (chipid, modids.MODID_PM5))

        #NoC router
        self.r0 = router.Router(self.nocif, (chipid, modids.MODID_ROUTER0), 0)
        self.r1 = router.Router(self.nocif, (chipid, modids.MODID_ROUTER1), 1)
        self.r2 = router.Router(self.nocif, (chipid, modids.MODID_ROUTER2), 2)
        self.r3 = router.Router(self.nocif, (chipid, modids.MODID_ROUTER3), 3)

        #DRAM
        self.dram1 = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM1))
        self.dram2 = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM2))

        #PMs
        self.pm6 = pm.PM(self.nocif, (chipid, modids.MODID_PM6), 1)
        self.pm7 = pm.PM(self.nocif, (chipid, modids.MODID_PM7), 2)
        self.pm3 = pm.PM(self.nocif, (chipid, modids.MODID_PM3), 3)
        self.pm5 = pm.PM(self.nocif, (chipid, modids.MODID_PM5), 4)


    def tear(self):
        self.noccomm.tear()
        self.uart.close()

    def read_posted(self, num):
        for i in range(count):
            p = self.recv_packet()
            if p is None:
                return
            yield "%016x" % p.data
