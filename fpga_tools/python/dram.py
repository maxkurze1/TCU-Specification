
import noc
import memory
from tcu import TCU


class DRAM(memory.Memory):
    def __init__(self, nocif, nocid):
        self.nocid = nocid
        self.mem = self
        self.shortname = "dram"
        self.name = "DDR4 SDRAM"
        self.mem = memory.Memory(nocif, self.nocid)

    def getStatus(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START]
    
    def getInitCalibComplete(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x8]
