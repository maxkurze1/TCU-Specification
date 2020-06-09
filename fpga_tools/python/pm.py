
import noc
import memory
from tcu import TCU
from fpga_utils import Progress


class PM():
    
    #Rocket interrupt
    ROCKET_INT_COUNT = 2


    def __init__(self, nocif, nocid, pm_num):
        self.nocid = nocid
        self.shortname = "pm%d" % pm_num
        self.name = "PM%d" % pm_num
        self.mem = memory.Memory(nocif, self.nocid)
        self.pm_num = pm_num
    
    def __repr__(self):
        return self.name
    
    def initMem(self, file, base_addr=0x0):
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
            self.pmdata.append(memory.MemSlice(base_addr+addr, slic.data))
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
    

    def start(self):
        self.mem[TCU.TCU_REGADDR_CORE_CFG_START] = 1
    
    def stop(self):
        self.mem[TCU.TCU_REGADDR_CORE_CFG_START] = 0

    def getEnable(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START]
    
    def tcu_status(self):
        return self.mem[TCU.TCU_REGADDR_TCU_STATUS]
    
    #----------------------------------------------
    #special functions for PicoRV32 RISC-V core

    #interrupt val (32 bit)
    def pico_setIRQ(self, val32):
        self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x10] = val32
    
    def pico_getIRQ(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x10]
    
    
    def pico_getEOI(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x18]

    def pico_getTrap(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x8]

    #set stack addr
    def pico_setStackAddr(self, val32):
        self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x20] = val32
    
    def pico_getStackAddr(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x20]

    #----------------------------------------------
    #special functions for Rocket RISC-V core

    #interrupt val
    def rocket_setInt(self, int_num, val):
        if (int_num < self.ROCKET_INT_COUNT):
            self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x8+8*int_num] = val
        else:
            print("Interrupt %d not supported for Rocket core. Max = %d" % (int_num, self.ROCKET_INT_COUNT))
    
    def rocket_getInt(self, int_num):
        if (int_num < self.ROCKET_INT_COUNT):
            return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x8+8*int_num]
        else:
            print("Interrupt %d not supported for Rocket core. Max = %d" % (int_num, self.ROCKET_INT_COUNT))
            return 0

