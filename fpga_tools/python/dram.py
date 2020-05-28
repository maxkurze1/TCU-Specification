
import noc
import memory


class DRAM(memory.Memory):
    TCU_EP_REG_COUNT = 8
    TCU_CFG_REG_COUNT = 8
    TCU_STATUS_REG_COUNT = 1

    TCU_EP_REG_SIZE = 0x18
    TCU_CFG_REG_SIZE = 0x8
    TCU_STATUS_REG_SIZE = 0x8

    TCU_REGADDR_START = 0xF000_0000

    #ep regs
    TCU_REGADDR_EP_START = TCU_REGADDR_START + 0x0000_0038

    #TCU status vector
    TCU_REGADDR_TCU_STATUS = TCU_REGADDR_EP_START + TCU_EP_REG_COUNT*TCU_EP_REG_SIZE

    #config regs for core
    TCU_REGADDR_CORE_CFG_START = TCU_REGADDR_TCU_STATUS + TCU_STATUS_REG_COUNT*TCU_STATUS_REG_SIZE
    

    def __init__(self, nocif, nocid):
        self.nocid = nocid
        self.mem = self
        self.shortname = "dram"
        self.name = "DDR4 SDRAM"
        self.mem = memory.Memory(nocif, self.nocid)

    def getStatus(self):
        return self.mem[self.TCU_REGADDR_CORE_CFG_START]
    
    def getInitCalibComplete(self):
        return self.mem[self.TCU_REGADDR_CORE_CFG_START+0x8]
