
import noc
import memory
from tcu import TCUStatusReg, TCUExtReg, TileDesc

class DRAM(memory.Memory):
    def __init__(self, tcu, nocif, nocid):
        self.tcu = tcu
        self.shortname = "dram"
        self.name = "DDR4 SDRAM"
        self.mem = memory.Memory(nocif, nocid)
        self.nocarq = noc.NoCARQRegfile(nocid)

    def getStatus(self):
        return self.mem[self.tcu.config_reg_addr(0)]

    def getInitCalibComplete(self):
        return self.mem[self.tcu.config_reg_addr(1)]

    def tcu_tile_desc(self):
        tile_desc = self.mem[self.tcu.ext_reg_addr(TCUExtReg.TILE_DESC)]
        return TileDesc(tile_desc)

    def tcu_status(self):
        return self.mem[self.tcu.status_reg_addr(TCUStatusReg.STATUS)]

    def tcu_reset(self):
        self.mem[self.tcu.status_reg_addr(TCUStatusReg.RESET)] = 1

    def tcu_ctrl_flit_count(self):
        flits = self.mem[self.tcu.status_reg_addr(TCUStatusReg.CTRL_FLIT_COUNT)]
        flits_rx = flits & 0xFFFFFFFF
        flits_tx = flits >> 32
        return (flits_tx, flits_rx)

    def tcu_byp_flit_count(self):
        flits = self.mem[self.tcu.status_reg_addr(TCUStatusReg.BYP_FLIT_COUNT)]
        flits_rx = flits & 0xFFFFFFFF
        flits_tx = flits >> 32
        return (flits_tx, flits_rx)

    def tcu_drop_flit_count(self):
        return self.mem[self.tcu.status_reg_addr(TCUStatusReg.DROP_FLIT_COUNT)] & 0xFFFFFFFF

    def tcu_error_flit_count(self):
        return self.mem[self.tcu.status_reg_addr(TCUStatusReg.DROP_FLIT_COUNT)] >> 32
