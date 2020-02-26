
import noc
import memory


class DRAM(memory.Memory):
    DTU_EP_REG_COUNT = 8
    DTU_CFG_REG_COUNT = 8
    DTU_STATUS_REG_COUNT = 1

    DTU_EP_REG_SIZE = 0x18
    DTU_CFG_REG_SIZE = 0x8
    DTU_STATUS_REG_SIZE = 0x8

    DTU_REGADDR_START = 0xF000_0000

    #ep regs
    DTU_REGADDR_EP_START = DTU_REGADDR_START + 0x0000_0040

    #DTU status vector
    DTU_REGADDR_DTU_STATUS = DTU_REGADDR_EP_START + DTU_EP_REG_COUNT*DTU_EP_REG_SIZE

    #config regs for core
    DTU_REGADDR_CORE_CFG_START = DTU_REGADDR_DTU_STATUS + DTU_STATUS_REG_COUNT*DTU_STATUS_REG_SIZE
    

    def __init__(self, nocif, nocid):
        self.nocid = nocid
        self.mem = self
        self.shortname = "dram"
        self.name = "DDR4 SDRAM"
        self.mem = memory.Memory(nocif, self.nocid)

    def getStatus(self):
        return self.mem[self.DTU_REGADDR_CORE_CFG_START]
    
    def getInitCalibComplete(self):
        return self.mem[self.DTU_REGADDR_CORE_CFG_START+0x8]
