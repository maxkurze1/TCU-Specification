
import noc
import memory
from tcu import TCU


class DRAM(memory.Memory):
    def __init__(self, nocif, nocid):
        self.shortname = "dram"
        self.name = "DDR4 SDRAM"
        self.mem = memory.Memory(nocif, nocid)
        self.nocarq = noc.NoCARQRegfile(nocid)

    def getStatus(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START]

    def getInitCalibComplete(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x8]

    def tcu_status(self):
        return self.mem[TCU.TCU_REGADDR_TCU_STATUS]

    def tcu_reset(self):
        self.mem[TCU.TCU_REGADDR_TCU_RESET] = 1

    def tcu_ctrl_flit_count(self):
        flits = self.mem[TCU.TCU_REGADDR_TCU_CTRL_FLIT_COUNT]
        flits_rx = flits & 0xFFFFFFFF
        flits_tx = flits >> 32
        return (flits_tx, flits_rx)

    def tcu_byp_flit_count(self):
        flits = self.mem[TCU.TCU_REGADDR_TCU_BYP_FLIT_COUNT]
        flits_rx = flits & 0xFFFFFFFF
        flits_tx = flits >> 32
        return (flits_tx, flits_rx)

    def tcu_drop_flit_count(self):
        return self.mem[TCU.TCU_REGADDR_TCU_DROP_FLIT_COUNT] & 0xFFFFFFFF

    def tcu_error_flit_count(self):
        return self.mem[TCU.TCU_REGADDR_TCU_DROP_FLIT_COUNT] >> 32
