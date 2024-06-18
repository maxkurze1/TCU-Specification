from enum import Enum

import noc
import memory
from tcu import TCUStatusReg, TCUExtReg


class C2CConfigReg(Enum):
    DEBUG = 0
    VERSION = 1
    ERROR = 2
    ENABLE = 3
    LOOPBACK = 4

    #BI Serdes
    CLK_VERSION = 11
    CLK_USE_REF = 12

    #simulation only
    CLK_MULTI = 13
    CLK_ENABLE = 14

    #Xilinx Serdes
    SERDES_STATUS_RXCTRL = 10
    SERDES_STATUS = 11



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

    """
    serdesStatusVector = {
        qpll1Lock_i,    //bit 14
        qpll1Reset_o,
        transRxDone,
        transTxDone,
        rxbufstatus,    //bits 10:8
        rxbyteisaligned,
        rybyterealign,
        rxclkcorcnt,    //bits 5:4
        rxcommadet,
        rxpmaresetdone,
        txpmaresetdone,
        gtpowergood     //bit 0
    }
    serdesStatusVectorRxCtrl = {
        rxctrl3,        //bits 23:16
        rxctrl2,        //bits 15:8
        rxctrl1[7:0]
    }
    """
    def getSerdesStatus(self, do_print=False):
        serdes_stat_rxctrl = self.mem[self.tcu.config_reg_addr(C2CConfigReg.SERDES_STATUS_RXCTRL)]
        serdes_stat = self.mem[self.tcu.config_reg_addr(C2CConfigReg.SERDES_STATUS)]
        if do_print:
            print("Serdes Status Vector:")
            print(" gtpowergood: {}".format(serdes_stat & 0x1))
            print(" txpmaresetdone: {}".format((serdes_stat >> 1) & 0x1))
            print(" rxpmaresetdone: {}".format((serdes_stat >> 2) & 0x1))
            print(" rxcommadet: {}".format((serdes_stat >> 3) & 0x1))
            print(" rxclkcorcnt: {:#x}".format((serdes_stat >> 4) & 0x3))
            print(" rybyterealign: {}".format((serdes_stat >> 6) & 0x1))
            print(" rxbyteisaligned: {}".format((serdes_stat >> 7) & 0x1))
            print(" rxbufstatus: {:#x}".format((serdes_stat >> 8) & 0x7))
            print(" transTxDone: {}".format((serdes_stat >> 11) & 0x1))
            print(" transRxDone: {}".format((serdes_stat >> 12) & 0x1))
            print(" qpll1Reset: {}".format((serdes_stat >> 13) & 0x1))
            print(" qpll1Lock: {}".format((serdes_stat >> 14) & 0x1))
            print(" rxctrl1 (byte has disparity error): {:#x}".format(serdes_stat_rxctrl & 0xFF))
            print(" rxctrl2 (byte has comma char): {:#x}".format((serdes_stat_rxctrl >> 8) & 0xFF))
            print(" rxctrl3 (byte has no valid char): {:#x}".format((serdes_stat_rxctrl >> 16) & 0xFF))
        return (serdes_stat, serdes_stat_rxctrl)

    """
    Reset chipid of incoming packets from c2c link to home-chipid to prevent infinite packets reflections.
    """
    def setLoopback(self, val):
        self.mem[self.tcu.config_reg_addr(C2CConfigReg.LOOPBACK)] = val

    def getLoopback(self):
        return self.mem[self.tcu.config_reg_addr(C2CConfigReg.LOOPBACK)]


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