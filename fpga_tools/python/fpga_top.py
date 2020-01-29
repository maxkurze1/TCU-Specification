
import modids
import noc
import dram
import pm
import uart
import regfile
#from . import jtag
#from .mod import pe
#from .mod import app
#from .mod import cm
#from .mod import ddr
#from .mod import fec
#from .mod import sphdec
#from .mod import uart
#from .mod import fpgaif
import os
#from  thdk_config import THDKConfig





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
    def __init__(self, chipid=0):
        print("fpga_top started")
        if not os.path.isdir("log"):
            os.mkdir("log")
        #self.jtagcomm = jtag.JTAGComm('th4')

        
        #periphery
        #self.fpgaif = fpgaif.FPGA_if(self.jtagcomm, self.noccomm)
        #self.uart = uart.UART('/dev/ttyUSB1')

        #NOC
        self.nocif = noc.NoCethernet([('192.168.1.10', 1800), ('192.168.1.10', 1801)], ("192.168.1.1", 1800))
        self.nocif_rf = noc.EthernetRegfile(self.nocif, (chipid, modids.MODID_ETH))

        #regfile
        self.regfile = regfile.REGFILE(self.nocif, (chipid, modids.MODID_PM5))

        #routers
        #self.routers = [jtag.JtagDev(self.jtagcomm, 'ROUTER%d' % x) for x in [0,1,2,3]]

        #DRAM
        self.dram1 = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM1))
        #self.dram1_rf = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM1), True)
        self.dram2 = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM2))
        #self.dram2_rf = dram.DRAM(self.nocif, (chipid, modids.MODID_DRAM2), True)
        
        #PMs
        #self.pms = [pm.PM(self.nocif, chipid, modids.MODID_PM3, 0)]
        self.pm6 = pm.PM(self.nocif, (chipid, modids.MODID_PM6), 0)
        self.pm7 = pm.PM(self.nocif, (chipid, modids.MODID_PM7), 0)

        #ASICs
        #self.fec = fec.Fec(self.jtagcomm, self.noccomm, (0, 12))
        #self.sphdec = sphdec.Sphdec(self.jtagcomm, self.noccomm, (0, 13))
        
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
