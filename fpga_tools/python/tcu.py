
import modids


def modid_to_tile(modid):
    try:
        return modids.MODID_TO_TILE[modid]
    except:
        return "Unknown({:#x})".format(modid)

class Flags():
    READ = 1
    WRITE = 2
    RDWR = 3

class EP():
    INVALID = 0
    SEND = 1
    RECEIVE = 2
    MEMORY = 3

    def invalid():
        return EP([0, 0, 0])

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

    def vpe(self):
        return (self.regs[0] >> 3) & 0xFFFF
    def set_vpe(self, vpe):
        self.regs[0] &= ~(0xFFFF << 3)
        self.regs[0] |= (vpe & 0xFFFF) << 3;

    def __repr__(self):
        return "Inv [type={}, vpe={}]".format(self.type(), self.vpe())

class MemEP(EP):
    def __init__(self, regs = [EP.MEMORY, 0, 0]):
        super(MemEP, self).__init__(regs)

    def pe(self):
        return (self.regs[0] >> 23) & 0xFF
    def set_pe(self, pe):
        self.regs[0] &= ~(0xFF << 23)
        self.regs[0] |= (pe & 0xFF) << 23;

    def addr(self):
        return self.regs[1]
    def set_addr(self, addr):
        self.regs[1] = addr

    def size(self):
        return self.regs[2]
    def set_size(self, size):
        self.regs[2] = size

    def flags(self):
        return (self.regs[0] >> 19) & 0xF
    def set_flags(self, flags):
        self.regs[0] &= ~(0xF << 19)
        self.regs[0] |= (flags & 0xF) << 19

    def __repr__(self):
        return "Mem [pe={}, vpe={:#x}, addr={:#x}, size={:#x}, flags={}]".format(
            modid_to_tile(self.pe()), self.vpe(), self.addr(), self.size(), self.flags()
        )

class SendEP(EP):
    UNLIMITED_CRD = 0x3F

    def __init__(self, regs = [EP.SEND, 0, 0]):
        super(SendEP, self).__init__(regs)

    def pe(self):
        return (self.regs[1] >> 16) & 0xFF
    def set_pe(self, pe):
        self.regs[1] &= ~(0xFF << 16)
        self.regs[1] |= (pe & 0xFF) << 16

    def ep(self):
        return self.regs[1] & 0xFFFF
    def set_ep(self, ep):
        self.regs[1] &= ~0xFFFF
        self.regs[1] |= ep & 0xFFFF

    def label(self):
        return self.regs[2] & 0xFFFFFFFF
    def set_label(self, label):
        self.regs[2] &= ~0xFFFFFFFF
        self.regs[2] |= label & 0xFFFFFFFF

    def msg_size(self):
        return (self.regs[0] >> 31) & 0x3F
    def set_msg_size(self, size):
        self.regs[0] &= ~(0x3F << 31)
        self.regs[0] |= (size & 0x3F) << 31

    def max_crd(self):
        return (self.regs[0] >> 25) & 0x3F
    def cur_crd(self):
        return (self.regs[0] >> 19) & 0x3F
    def set_crd(self, crd):
        self.regs[0] &= ~((0x3F << 25) | (0x3F << 19))
        self.regs[0] |= (crd & 0x3F) << 25
        self.regs[0] |= (crd & 0x3F) << 19

    def is_reply(self):
        return (self.regs[0] >> 53) & 0x1
    def crd_ep(self):
        return (self.regs[0] >> 37) & 0xFFFF

    def __repr__(self):
        return "Send[dst={}:{}, vpe={:#x}, label={:#x}, msgsz=2^{}, crd={}:{}, reply={}]".format(
            modid_to_tile(self.pe()), self.ep(), self.vpe(), self.label(), self.msg_size(), self.cur_crd(),
            self.max_crd(), self.is_reply()
        )

class RecvEP(EP):
    def __init__(self, regs = [EP.RECEIVE, 0, 0]):
        super(RecvEP, self).__init__(regs)

    def buffer(self):
        return self.regs[1]
    def set_buffer(self, buffer):
        self.regs[1] = buffer

    def slot_size(self):
        return (self.regs[0] >> 41) & 0x3F
    def set_slot_size(self, size):
        self.regs[0] &= ~(0x3F << 41)
        self.regs[0] |= (size & 0x3F) << 41

    def slots(self):
        return (self.regs[0] >> 35) & 0x3F
    def set_slots(self, slots):
        self.regs[0] &= ~(0x3F << 35)
        self.regs[0] |= (slots & 0x3F) << 35

    def reply_eps(self):
        return (self.regs[0] >> 19) & 0xFFFF
    def set_reply_eps(self, eps):
        self.regs[0] &= ~(0xFFFF << 19)
        self.regs[0] |= (eps & 0xFFFF) << 19

    def unread(self):
        return self.regs[2] >> 32
    def occupied(self):
        return self.regs[2] & 0xFFFFFFFF
    def rpos(self):
        return (self.regs[0] >> 53) & 0x3F
    def wpos(self):
        return (self.regs[0] >> 47) & 0x3F

    def __repr__(self):
        return "Recv[buffer={:#x}, vpe={:#x}, slots=2^{}, slot_size=2^{}, unread={:#x}, occupied={:#x}, rpl_eps={}, rpos={}, wpos={}]".format(
            self.buffer(), self.vpe(), self.slots(), self.slot_size(), self.unread(), self.occupied(),
            self.reply_eps(), self.rpos(), self.wpos()
        )

class LOG():

    #Log IDs
    LOG_ID = ["NONE",

              "CMD_SEND",
              "CMD_REPLY",
              "CMD_READ",
              "CMD_WRITE",
              "CMD_FETCH",
              "CMD_ACK_MSG",
              "CMD_FINISH",

              "CMD_EXT_INVEP",
              "CMD_EXT_FINISH",

              "NOC_REG_WRITE_ERR",
              "NOC_REG_WRITE",
              "NOC_READ_RSP",
              "NOC_READ_RSP_ERR",
              "NOC_READ_RSP_DONE",
              "NOC_WRITE",
              "NOC_READ_ERR",
              "NOC_READ",
              "NOC_MSG_HD_SECMSG",
              "NOC_MSG_HD",
              "NOC_MSG_HD_INV",
              "NOC_MSG_PL_CONT",
              "NOC_MSG_PL_UNEXP",
              "NOC_MSG_PL_ERR",
              "NOC_MSG_ACK",
              "NOC_MSG_ACK_ERR",
              "NOC_ERROR",
              "NOC_ERROR_UNEXP",
              "NOC_INVMODE",
              "NOC_INVFLIT",

              "CMD_PRIV_INV_PAGE",
              "CMD_PRIV_INV_TLB",
              "CMD_PRIV_INS_TLB",
              "CMD_PRIV_XCHG_VPE",
              "CMD_PRIV_TIMER",
              "CMD_PRIV_ABORT",
              "CMD_PRIV_FINISH"]

    def split_tcu_log(upper_data64, lower_data64):
        tcu_log = LOG()
        log_id = (lower_data64 >> 32) & 0xFF
        log_time = lower_data64 & 0xFFFFFFFF
        id_string = tcu_log.get_tcu_log(log_id)
        time_string = "Time: {:12}".format(log_time)
        ret_string = time_string + ", " + id_string + ", "

        if (log_id == 0):
            return ret_string

        #unpriv cmd
        if (log_id <= 4):
            log_ep = (lower_data64 >> 40) & 0xFFFF
            log_addr = ((upper_data64 & 0xFFFFFF) << 8) | (lower_data64 >> 56)
            log_size = (upper_data64 >> 24) & 0xFFFFFFFF
            log_modid = upper_data64 >> 56
            return ret_string + "to tile: {}, send-ep: {:d}, local addr: {:#010x} size: {:d}".format(modid_to_tile(log_modid), log_ep, log_addr, log_size)

        if (log_id <= 6):
            log_ep = (lower_data64 >> 40) & 0xFFFF
            return ret_string + "ep: {:d}".format(log_ep)

        #unpriv finish
        if (log_id == 7):
            log_error = (lower_data64 >> 40) & 0x1F
            return ret_string + "error: {:d}".format(log_error)

        #ext cmd
        if (log_id == 8):
            log_ep = (lower_data64 >> 40) & 0xFF
            log_force = (lower_data64 >> 48) & 0x1
            return ret_string + "ep: {:d}, force: {:d}".format(log_ep, log_force)

        #ext finish
        if (log_id == 9):
            log_error = (lower_data64 >> 40) & 0x1F
            return ret_string + "error: {:d}".format(log_error)

        #NoC received write or read
        if (log_id <= 13):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_mode = (lower_data64 >> 48) & 0xF
            log_addr = ((upper_data64 & 0xFFFFF) << 12) | (lower_data64 >> 52)
            return ret_string + "from tile: {}, mode: {:d}, local addr: {:#010x}".format(modid_to_tile(log_modid), log_mode, log_addr)

        if (log_id == 14):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_error = (lower_data64 >> 48) & 0x1F
            return ret_string + "from tile: {}, error: {:d}".format(modid_to_tile(log_modid), log_error)

        if (log_id == 15):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_mode = (lower_data64 >> 48) & 0xF
            log_addr = ((upper_data64 & 0xFFFFF) << 12) | (lower_data64 >> 52)
            return ret_string + "from tile: {}, mode: {:d}, local addr: {:#010x}".format(modid_to_tile(log_modid), log_mode, log_addr)

        if (log_id <= 17):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_mode = (lower_data64 >> 48) & 0xF
            log_addr = ((upper_data64 & 0xFFFFF) << 12) | (lower_data64 >> 52)
            log_size = upper_data64 >> 20
            return ret_string + "from tile: {}, mode: {:d}, local addr: {:#010x} size: {:d}".format(modid_to_tile(log_modid), log_mode, log_addr, log_size)

        #NoC received msg
        if (log_id <= 23):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_ep = (lower_data64 >> 48) & 0xFFFF
            return ret_string + "from tile: {}, recv-ep: {:d}".format(modid_to_tile(log_modid), log_ep)

        #NoC received msg-ack
        if (log_id <= 25):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_error = (lower_data64 >> 48) & 0x1F
            return ret_string + "from tile: {}, error: {:d}".format(modid_to_tile(log_modid), log_error)

        #NoC received error packet
        if (log_id <= 27):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_addr = ((upper_data64 & 0xFFFF) << 16) | (lower_data64 >> 48) & 0xFFFF
            log_error = (upper_data64 >> 16) & 0x1F
            return ret_string + "from tile: {}, local addr: {:#010x}, error: {:d}".format(modid_to_tile(log_modid), log_addr, log_error)

        #NoC received packet with invalid data
        if (log_id <= 29):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_mode = (lower_data64 >> 48) & 0xF
            log_burst_flag_prev = (lower_data64 >> 52) & 0x1
            log_burst_flag_curr = (lower_data64 >> 53) & 0x1
            return ret_string + "from tile: {}, mode: {:d}, burst flags (prev./current): {}-{}".format(modid_to_tile(log_modid), log_mode, log_burst_flag_prev, log_burst_flag_curr)

        #priv. cmds
        #invalidate page
        if (log_id == 30):
            log_vpeid = (lower_data64 >> 40) & 0xFFFF
            log_virt = ((upper_data64 & 0xFFF) << 8) | (lower_data64 >> 56)
            return ret_string + "vpeid: {:#x}, virt. page: {:#07x}".format(log_vpeid, log_virt)

        #insert TLB
        if (log_id == 32):
            log_vpeid = (lower_data64 >> 40) & 0xFFFF
            log_virt = ((upper_data64 & 0xFFF) << 8) | (lower_data64 >> 56)
            log_phys = (upper_data64 >> 12) & 0xFFFFF
            return ret_string + "vpeid: {:#x}, virt. page: {:#07x}, phys. page: {:#07x}".format(log_vpeid, log_virt, log_phys)

        #xchg_vpe (vpe=id+msgs)
        if (log_id == 33):
            log_curvpe = ((upper_data64 & 0xFF) << 24) | (lower_data64 >> 40)
            log_xchgvpe = (upper_data64 >> 8) & 0xFFFFFFFF
            return ret_string + "cur_vpe: {:#x}, xchg_vpe: {:#x}".format(log_curvpe, log_xchgvpe)

        #timer
        if (log_id == 34):
            log_nanos = ((upper_data64 & 0xFF) << 24) | (lower_data64 >> 40)
            return ret_string + "nanos: {:d}".format(log_nanos)

        #abort
        if (log_id == 35):
            log_vpeid = (lower_data64 >> 40) & 0xFFFF
            log_virt = (upper_data64 & 0xFFF) | (lower_data64 >> 56)
            return ret_string + "vpeid: {:#x}, virt. page: {:#07x}".format(log_vpeid, log_virt)

        #finish
        if (log_id == 36):
            log_error = (lower_data64 >> 40) & 0x1F
            return ret_string + "error: {:d}".format(log_error)

        return ret_string

    def __init__(self):
        pass

    def get_tcu_log(self, log_id):
        if (log_id >= len(self.LOG_ID)):
            return "UNDEFINED"
        return self.LOG_ID[log_id]


class TCU():

    TCU_EP_REG_COUNT = 64
    TCU_CFG_REG_COUNT = 8
    TCU_STATUS_REG_COUNT = 5
    TCU_LOG_REG_COUNT = 1024

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

    #addr of log mem
    TCU_REGADDR_TCU_LOG = TCU_REGADDR_START + 0x0100_0000
