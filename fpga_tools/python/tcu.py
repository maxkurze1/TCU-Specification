
import modids

MODID_TO_PMID = {
    modids.MODID_PM6 : "PM1",
    modids.MODID_PM7 : "PM2",
    modids.MODID_PM3 : "PM3",
    modids.MODID_PM5 : "PM4",
    modids.MODID_PM2 : "DRAM1",
}

class EP():
    INVALID = 0
    SEND = 1
    RECEIVE = 2
    MEMORY = 3

    def from_regs(regs):
        ep = EP(regs)
        if ep.type() == EP.SEND:
            return SendEP(regs)
        if ep.type() == EP.RECEIVE:
            return RecvEP(regs)
        if ep.type() == EP.MEMORY:
            return MemEP(regs)
        return ep

    def __init__(self, regs):
        self.regs = regs

    def type(self):
        return self.regs[0] & 0x7

    def __repr__(self):
        return "Inv [type={}]".format(self.type())

class MemEP(EP):
    def __init__(self, regs):
        super(MemEP, self).__init__(regs)

    def pe(self):
        return (self.regs[0] >> 23) & 0xFF
    def addr(self):
        return self.regs[1]
    def size(self):
        return self.regs[2]
    def flags(self):
        return (self.regs[0] >> 19) & 0xF

    def __repr__(self):
        return "MemEP[pe={}, addr={:#x}, size={:#x}, flags={}]".format(
            MODID_TO_PMID[self.pe()], self.addr(), self.size(), self.flags()
        )

class SendEP(EP):
    def __init__(self, regs):
        super(SendEP, self).__init__(regs)

    def pe(self):
        return (self.regs[1] >> 16) & 0xFF
    def ep(self):
        return self.regs[1] & 0xFFFF
    def label(self):
        return self.regs[2] & 0xFFFFFFFF
    def is_reply(self):
        return (self.regs[0] >> 53) & 0x1
    def crd_ep(self):
        return (self.regs[0] >> 37) & 0xFFFF
    def msg_size(self):
        return (self.regs[0] >> 31) & 0x3F
    def max_crd(self):
        return (self.regs[0] >> 25) & 0x3F
    def cur_crd(self):
        return (self.regs[0] >> 19) & 0x3F

    def __repr__(self):
        return "SendEP[dst={}:{}, label={:#x}, msgsz=2^{}, crd={}:{}, reply={}]".format(
            MODID_TO_PMID[self.pe()], self.ep(), self.label(), self.msg_size(), self.cur_crd(),
            self.max_crd(), self.is_reply()
        )

class RecvEP(EP):
    def __init__(self, regs):
        super(RecvEP, self).__init__(regs)

    def buffer(self):
        return self.regs[1]
    def unread(self):
        return self.regs[2] >> 32
    def occupied(self):
        return self.regs[2] & 0xFFFFFFFF
    def rpos(self):
        return (self.regs[0] >> 53) & 0x3F
    def wpos(self):
        return (self.regs[0] >> 47) & 0x3F
    def slot_size(self):
        return (self.regs[0] >> 41) & 0x3F
    def slots(self):
        return (self.regs[0] >> 35) & 0x3F
    def reply_eps(self):
        return (self.regs[0] >> 19) & 0xFFFF

    def __repr__(self):
        return "RecvEP[buffer={:#x}, slots=2^{}, slot_size=2^{}, unread={:#x}, occupied={:#x}, rpl_eps={}, rpos={}, wpos={}]".format(
            self.buffer(), self.slots(), self.slot_size(), self.unread(), self.occupied(),
            self.reply_eps(), self.rpos(), self.wpos()
        )

class TCU():

    TCU_EP_REG_COUNT = 64
    TCU_CFG_REG_COUNT = 8
    TCU_STATUS_REG_COUNT = 5

    TCU_EP_REG_SIZE = 0x18
    TCU_CFG_REG_SIZE = 0x8
    TCU_STATUS_REG_SIZE = 0x8

    TCU_REGADDR_START = 0xF000_0000

    #ext regs
    TCU_REGADDR_FEATURES = TCU_REGADDR_START + 0x0000_0000
    TCU_REGADDR_EXT_CMD  = TCU_REGADDR_START + 0x0000_0008

    #unpriv. regs
    TCU_REGADDR_COMMAND  = TCU_REGADDR_START + 0x0000_0010
    TCU_REGADDR_DATA     = TCU_REGADDR_START + 0x0000_0018
    TCU_REGADDR_ARG1     = TCU_REGADDR_START + 0x0000_0020
    TCU_REGADDR_CUR_TIME = TCU_REGADDR_START + 0x0000_0028

    #ep regs
    TCU_REGADDR_EP_START = TCU_REGADDR_START + 0x0000_0038

    #priv. regs
    TCU_REGADDR_CORE_REQ     = TCU_REGADDR_START + 0x0000_2000
    TCU_REGADDR_PRIV_CMD     = TCU_REGADDR_START + 0x0000_2008
    TCU_REGADDR_PRIV_CMD_ARG = TCU_REGADDR_START + 0x0000_2010
    TCU_REGADDR_CUR_VPE      = TCU_REGADDR_START + 0x0000_2018
    TCU_REGADDR_OLD_VPE      = TCU_REGADDR_START + 0x0000_2020

    #TCU status vector
    TCU_REGADDR_TCU_STATUS          = TCU_REGADDR_START + 0x0000_3000
    TCU_REGADDR_TCU_RESET           = TCU_REGADDR_START + 0x0000_3008
    TCU_REGADDR_TCU_CTRL_FLIT_COUNT = TCU_REGADDR_START + 0x0000_3010
    TCU_REGADDR_TCU_IO_FLIT_COUNT   = TCU_REGADDR_START + 0x0000_3018
    TCU_REGADDR_TCU_DROP_FLIT_COUNT = TCU_REGADDR_START + 0x0000_3020

    #config regs for core
    TCU_REGADDR_CORE_CFG_START = TCU_REGADDR_TCU_STATUS + TCU_STATUS_REG_COUNT*TCU_STATUS_REG_SIZE

