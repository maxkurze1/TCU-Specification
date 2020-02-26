
import modids
import noc
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
    def __init__(self, chipid=0):
        self.fpga_ip_addr = str(IPv4Address(int(IPv4Address(self.FPGA_IP)) + chipid))
        print("Connect to FPGA at %s:%d" % (self.fpga_ip_addr, self.FPGA_PORT))

        if not os.path.isdir("log"):
            os.mkdir("log")
        #self.jtagcomm = jtag.JTAGComm('th4')

        
        #periphery
        #self.fpgaif = fpgaif.FPGA_if(self.jtagcomm, self.noccomm)
        self.uart = uart.UART('/dev/ttyUSB1')

        #NOC
        self.nocif = noc.NoCethernet((self.fpga_ip_addr, self.FPGA_PORT))
        self.nocif_rf = noc.EthernetRegfile(self.nocif, (chipid, modids.MODID_ETH))

        #regfile
        #self.regfile = regfile.REGFILE(self.nocif, (chipid, modids.MODID_PM5))

        #routers
        #self.routers = [jtag.JtagDev(self.jtagcomm, 'ROUTER%d' % x) for x in [0,1,2,3]]

        #DRAM
        self.dram1 = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM1))
        self.dram2 = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM2))
        
        #PMs
        #self.pms = [pm.PM(self.nocif, chipid, modids.MODID_PM3, 0)]
        self.pm6 = pm.PM(self.nocif, (chipid, modids.MODID_PM6), 0)
        self.pm7 = pm.PM(self.nocif, (chipid, modids.MODID_PM7), 0)
        
        #self.mods = [self.dram1, self.dram2] + self.pms

    def tear(self):
        self.noccomm.tear()
        self.uart.close()
        
    def read_posted(self, num):
        for i in range(count):
            p = self.recv_packet()
            if p is None:
                return
            yield "%016x" % p.data
