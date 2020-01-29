
import noc
import memory
from fpga_utils import Progress


class PM():
    DTU_EP_REG_COUNT = 8
    DTU_CFG_REG_COUNT = 8

    DTU_EP_REG_SIZE = 0x18
    DTU_CFG_REG_SIZE = 0x8

    DTU_REGADDR_START = 0xF000_0000

    #dtu regs
    DTU_REGADDR_FEATURES  = DTU_REGADDR_START + 0x0000_0000
    DTU_REGADDR_CUR_TIME  = DTU_REGADDR_START + 0x0000_0008
    DTU_REGADDR_CLEAR_IRQ = DTU_REGADDR_START + 0x0000_0010
    DTU_REGADDR_CLOCK     = DTU_REGADDR_START + 0x0000_0018

    #cmd regs
    DTU_REGADDR_COMMAND   = DTU_REGADDR_START + 0x0000_0020
    DTU_REGADDR_ABORT     = DTU_REGADDR_START + 0x0000_0028
    DTU_REGADDR_DATA      = DTU_REGADDR_START + 0x0000_0030
    DTU_REGADDR_ARG1      = DTU_REGADDR_START + 0x0000_0038

    #ep regs
    DTU_REGADDR_EP_START = DTU_REGADDR_START + 0x0000_0040

    #config regs for core
    DTU_REGADDR_CORE_CFG_START = DTU_REGADDR_EP_START + DTU_EP_REG_COUNT*DTU_EP_REG_SIZE


    def __init__(self, nocif, nocid, pm_num):
        self.nocid = nocid
        self.shortname = "pm%d" % pm_num
        self.name = "PM%d" % pm_num
        self.mem = memory.Memory(nocif, self.nocid)
        self.pm_num = pm_num
    
    def __repr__(self):
        return self.name
    
    def initMem(self, file):
        """
        PE mem addr (8-byte addresses):
            0x0000-0x7FFF: imem
            0x8000-0xFFFF: dmem
        NoC mem addr (byte addresses):
            0x00000-0x3FFFF: imem
            0x40000-0x7FFFF: dmem
        """
        self.pmdata = []
        for slic in memory.memfilestream(file):
            #print("slic.begin: %x" % slic.begin)
            #if slic.begin < 0x00008000:
            #    addr = slic.begin + 0x00010000 #imem
            #else:
            #    addr = slic.begin - 0x00008000 #dmem
            addr = slic.begin   #addr in hex file corresponds to pysical mem distribution
            #print("addr: %x" % addr)
            self.pmdata.append(memory.MemSlice(addr, slic.data))
        #proc = Progress("load PM mem", sum([len(x) for x in self.pmdata]))
        #self.mem.writes(self.pmdata, prgss=lambda x: proc.advance(x))
        self.mem.writes(self.pmdata, force_no_burst=True)
        #proc.clear()
    
    def checkMem(self):
        #proc = Progress("check PM mem", sum([len(x) for x in self.pmdata]))
        #ret = self.mem.checks(self.pmdata, prgss=lambda x:proc.advance(x))
        #ret = self.mem.checks(self.pmdata)
        
        
        #for addr in range(self.pmdata.begin, len(self.pmdata)):
        
        #read_mem = self.mem.read(self.pmdata[0].begin, len(self.pmdata)/8)
        #for idx in range(self.pmdata[0].begin, len(self.pmdata[0])/8):
        #    if read_mem.data[idx] != self.pmdata[0].data[idx]:
        #        print("data not the same: %x != %x" % (read_mem.data[idx], self.pmdata[0].data[idx]))
        #
        #
        #proc.clear()
        return ret
    

    #deprecated

    #write to debug register, reg 0-3, 32-bit value (val)
    #def writeDbgReg(self, reg, val):
    #    if reg >= 0 and reg < 4:
    #        self.mem[self.PM_RF_BASE_ADDR+reg*4] = 0x0000000F_00000000 + val
    #
    #def readDbgReg(self, reg):
    #    if reg >= 0 and reg < 4:
    #        return self.mem[self.PM_RF_BASE_ADDR+reg*4]
    #    else:
    #        return -1

    

    #div_val: clk divider only even values (default: 1 -> pm_clk)
    #def setClkDiv(self, div_val):
    #    self.mem[self.PM_RF_BASE_ADDR+0x14] = 0x0000000F_00000000 + div_val
    #
    #def getClkDiv(self):
    #    return self.mem[self.PM_RF_BASE_ADDR+0x14]



    def start(self):
        self.mem[self.DTU_REGADDR_CORE_CFG_START] = 1
    
    def stop(self):
        self.mem[self.DTU_REGADDR_CORE_CFG_START] = 0

    def getEnable(self):
        return self.mem[self.DTU_REGADDR_CORE_CFG_START]
    
    
    #----------------------------------------------
    #special functions for PicoRV32 RISC-V core

    #interrupt val (32 bit)
    def setIRQ(self, val32):
        self.mem[self.DTU_REGADDR_CORE_CFG_START+0x10] = val32
    
    def getIRQ(self):
        return self.mem[self.DTU_REGADDR_CORE_CFG_START+0x10]
    
    
    def getEOI(self):
        return self.mem[self.DTU_REGADDR_CORE_CFG_START+0x18]

    def getTrap(self):
        return self.mem[self.DTU_REGADDR_CORE_CFG_START+0x8]

    #set stack addr
    def setStackAddr(self, val32):
        self.mem[self.DTU_REGADDR_CORE_CFG_START+0x20] = val32
    
    def getStackAddr(self):
        return self.mem[self.DTU_REGADDR_CORE_CFG_START+0x20]

