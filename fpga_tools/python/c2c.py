from enum import Enum

import noc
import memory
from tcu import TCUStatusReg, TCUExtReg


class C2CConfigReg(Enum):
    DEBUG = 0
    VERSION = 1
    ERROR = 2
    ENABLE = 3
    CLK_VERSION = 11
    CLK_USE_REF = 12

    #simulation only
    CLK_MULTI = 13
    CLK_ENABLE = 14


class C2C():
    def __init__(self, tcu, nocif, nocid, dir):
        self.tcu = tcu
        self.nocid = nocid
        self.name = "C2C_LINK_%s" % dir
        self.mem = memory.Memory(nocif, self.nocid)
        self.nocarq = noc.NoCARQRegfile(self.nocid)

    def __repr__(self):
        return self.name

    def setDebug(self, val):
        self.mem[self.tcu.config_reg_addr(C2CConfigReg.DEBUG)] = val

    def getDebug(self):
        return self.mem[self.tcu.config_reg_addr(C2CConfigReg.DEBUG)]

    def getVersion(self):
        return self.mem[self.tcu.config_reg_addr(C2CConfigReg.VERSION)]

    def resetError(self):
        self.mem[self.tcu.config_reg_addr(C2CConfigReg.ERROR)] = 0

    def getError(self):
        return self.mem[self.tcu.config_reg_addr(C2CConfigReg.ERROR)]

    def setEnable(self, val):
        self.mem[self.tcu.config_reg_addr(C2CConfigReg.ENABLE)] = val

    def getEnable(self):
        return self.mem[self.tcu.config_reg_addr(C2CConfigReg.ENABLE)]


    def tcu_version(self):
        return self.mem[self.tcu.ext_reg_addr(TCUExtReg.FEATURES)] >> 32

    def tcu_status(self):
        status = self.mem[self.tcu.status_reg_addr(TCUStatusReg.STATUS)]
        return (status & 0xFF, (status >> 8) & 0xFF, (status >> 16) & 0xFF, (status >> 24) & 0xFF)

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