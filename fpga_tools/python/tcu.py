
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

    def act(self):
        return (self.regs[0] >> 3) & 0xFFFF
    def set_act(self, act):
        self.regs[0] &= ~(0xFFFF << 3)
        self.regs[0] |= (act & 0xFFFF) << 3;

    def __repr__(self):
        return "Inv [type={}, act={}]".format(self.type(), self.act())

class MemEP(EP):
    def __init__(self, regs = [EP.MEMORY, 0, 0]):
        super(MemEP, self).__init__(regs)

    def tile(self):
        return (self.regs[0] >> 23) & 0xFF
    def set_tile(self, tile):
        self.regs[0] &= ~(0xFF << 23)
        self.regs[0] |= (tile & 0xFF) << 23;

    def chip(self):
        return (self.regs[0] >> 31) & 0x3F
    def set_chip(self, chip):
        self.regs[0] &= ~(0x3F << 31)
        self.regs[0] |= (chip & 0x3F) << 31;

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
        return "Mem [chip={}, tile={}, act={:#x}, addr={:#x}, size={:#x}, flags={}]".format(
            self.chip(), modid_to_tile(self.tile()), self.act(), self.addr(), self.size(), self.flags()
        )

class SendEP(EP):
    UNLIMITED_CRD = 0x3F

    def __init__(self, regs = [EP.SEND, 0, 0]):
        super(SendEP, self).__init__(regs)

    def tile(self):
        return (self.regs[1] >> 16) & 0xFF
    def set_tile(self, tile):
        self.regs[1] &= ~(0xFF << 16)
        self.regs[1] |= (tile & 0xFF) << 16

    def chip(self):
        return (self.regs[1] >> 24) & 0x3F
    def set_chip(self, chip):
        self.regs[1] &= ~(0x3F << 24)
        self.regs[1] |= (chip & 0x3F) << 24;

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
        return "Send[dst={}-{}:{}, act={:#x}, label={:#x}, msgsz=2^{}, crd={}:{}, reply={}]".format(
            self.chip(), modid_to_tile(self.tile()), self.ep(), self.act(), self.label(), self.msg_size(), self.cur_crd(),
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
        return "Recv[buffer={:#x}, act={:#x}, slots=2^{}, slot_size=2^{}, unread={:#x}, occupied={:#x}, rpl_eps={}, rpos={}, wpos={}]".format(
            self.buffer(), self.act(), self.slots(), self.slot_size(), self.unread(), self.occupied(),
            self.reply_eps(), self.rpos(), self.wpos()
        )

class LOG():

    LOG_ID = ["NONE",

              "CMD_SEND",
              "CMD_REPLY",
              "CMD_READ",
              "CMD_WRITE",
              "CMD_FETCH",
              "CMD_ACK_MSG",
              "CMD_FINISH",
              "RECV_FINISH",

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
              "NOC_MSG",
              "NOC_MSG_INV",
              "NOC_WRITE_ACK",
              "NOC_MSG_ACK",
              "NOC_ACK_ERR",
              "NOC_ERROR",
              "NOC_ERROR_UNEXP",
              "NOC_INVMODE",
              "NOC_INVFLIT",

              "CMD_PRIV_INV_PAGE",
              "CMD_PRIV_INV_TLB",
              "CMD_PRIV_INS_TLB",
              "CMD_PRIV_XCHG_VPE",
              "CMD_PRIV_SET_TIMER",
              "CMD_PRIV_ABORT",
              "CMD_PRIV_FINISH",
              "PRIV_CORE_REQ_FORMSG",
              "PRIV_CORE_REQ_FORMSG_FINISH",
              "PRIV_TLB_WRITE_ENTRY",
              "PRIV_TLB_READ_ENTRY",
              "PRIV_TLB_DEL_ENTRY",
              "PRIV_CUR_VPE_CHANGE",
              "PRIV_TIMER_INTR",
              "PMP_ACCESS_DENIED"]

    def split_tcu_log(upper_data64, lower_data64):
        tcu_log = LOG()
        log_id = (lower_data64 >> 32) & 0xFF
        log_time = (lower_data64 & 0xFFFFFFFF) << 4    #shift left by 4 to get time in ns
        id_string = tcu_log.get_tcu_log(log_id)
        time_string = "Time: {:12}".format(log_time)
        ret_string = time_string + ", " + id_string + ", "

        if (id_string == "NONE"):
            return ret_string

        #unpriv cmd
        if (id_string == "CMD_SEND"):
            log_ep = (lower_data64 >> 40) & 0xFFFF
            log_addr = ((upper_data64 & 0xFFFFFF) << 8) | (lower_data64 >> 56)
            log_size = (upper_data64 >> 24) & 0xFFFFFFFF
            log_modid = upper_data64 >> 56
            return ret_string + "to tile: {}, ep: {:d}, local addr: {:#010x}, size: {:d}".format(modid_to_tile(log_modid), log_ep, log_addr, log_size)

        if (id_string == "CMD_REPLY"):
            log_ep = (lower_data64 >> 40) & 0xFF
            log_addr = ((upper_data64 & 0xFFFF) << 16) | (lower_data64 >> 48)
            log_offset = (upper_data64 >> 16) & 0xFFFFF
            log_size = (upper_data64 >> 36) & 0xFFFFF
            log_modid = upper_data64 >> 56
            return ret_string + "to tile: {}, ep: {:d}, local addr: {:#010x}, msg offset: {:#x}, size: {:d}".format(modid_to_tile(log_modid), log_ep, log_addr, log_offset, log_size)

        if (id_string == "CMD_READ" or id_string == "CMD_WRITE"):
            log_ep = (lower_data64 >> 40) & 0xFF
            log_addr = ((upper_data64 & 0xFFFF) << 16) | (lower_data64 >> 48)
            log_offset = (upper_data64 >> 16) & 0xFFFFF
            log_size = (upper_data64 >> 36) & 0xFFFFF
            log_modid = upper_data64 >> 56
            return ret_string + "to tile: {}, ep: {:d}, local addr: {:#010x}, rem. addr offset: {:#x}, size: {:d}".format(modid_to_tile(log_modid), log_ep, log_addr, log_offset, log_size)

        if (id_string == "CMD_FETCH" or id_string == "CMD_ACK_MSG"):
            log_ep = (lower_data64 >> 40) & 0xFFFF
            log_offset = ((upper_data64 & 0xFFFFFF) << 8) | (lower_data64 >> 56)
            return ret_string + "ep: {:d}, msg offset: {:#x}".format(log_ep, log_offset)

        #unpriv finish
        if (id_string == "CMD_FINISH"):
            log_error = (lower_data64 >> 40) & 0x1F
            return ret_string + "error: {:d}".format(log_error)

        #msg receive has been finished
        if (id_string == "RECV_FINISH"):
            log_occ_mask = ((upper_data64 & 0xFF) << 24) | (lower_data64 >> 40)
            log_unread_mask = (upper_data64 >> 8) & 0xFFFFFFFF
            log_bitpos = (upper_data64 >> 40) & 0xFFFF
            return ret_string + "orig. occ. mask: {:#010x}, orig. unread mask: {:#010x}, new set bit pos. in masks: {:#010x}".format(log_occ_mask, log_unread_mask, log_bitpos)

        #ext cmd
        if (id_string == "CMD_EXT_INVEP"):
            log_ep = (lower_data64 >> 40) & 0xFF
            log_force = (lower_data64 >> 48) & 0x1
            return ret_string + "ep: {:d}, force: {:d}".format(log_ep, log_force)

        #ext finish
        if (id_string == "CMD_EXT_FINISH"):
            log_error = (lower_data64 >> 40) & 0x1F
            return ret_string + "error: {:d}".format(log_error)

        #NoC received write or read
        if (id_string == "NOC_REG_WRITE_ERR" or id_string == "NOC_REG_WRITE" or id_string == "NOC_READ_RSP" or id_string == "NOC_READ_RSP_ERR"):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_mode = (lower_data64 >> 48) & 0xF
            log_addr = ((upper_data64 & 0xFFFFF) << 12) | (lower_data64 >> 52)
            return ret_string + "from tile: {}, mode: {:d}, local addr: {:#010x}".format(modid_to_tile(log_modid), log_mode, log_addr)

        if (id_string == "NOC_READ_RSP_DONE"):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_error = (lower_data64 >> 48) & 0x1F
            return ret_string + "from tile: {}, error: {:d}".format(modid_to_tile(log_modid), log_error)

        if (id_string == "NOC_WRITE"):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_mode = (lower_data64 >> 48) & 0xF
            log_addr = ((upper_data64 & 0xFFFFF) << 12) | (lower_data64 >> 52)
            return ret_string + "from tile: {}, mode: {:d}, local addr: {:#010x}".format(modid_to_tile(log_modid), log_mode, log_addr)

        if (id_string == "NOC_READ_ERR" or id_string == "NOC_READ"):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_mode = (lower_data64 >> 48) & 0xF
            log_addr = ((upper_data64 & 0xFFFFF) << 12) | (lower_data64 >> 52)
            log_size = upper_data64 >> 20
            return ret_string + "from tile: {}, mode: {:d}, local addr: {:#010x} size: {:d}".format(modid_to_tile(log_modid), log_mode, log_addr, log_size)

        #NoC received msg
        if (id_string == "NOC_MSG" or id_string == "NOC_MSG_INV"):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_ep = (lower_data64 >> 48) & 0xFFFF
            return ret_string + "from tile: {}, recv-ep: {:d}".format(modid_to_tile(log_modid), log_ep)

        #NoC received write ACK
        if (id_string == "NOC_WRITE_ACK"):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_addr = ((upper_data64 & 0xFFFF) << 16) | ((lower_data64 >> 48) & 0xFFFF)
            log_size = (upper_data64 >> 16) & 0xFFFFFFFF
            return ret_string + "from tile: {}, addr: {:#010x}, size: {:d}".format(modid_to_tile(log_modid), log_addr, log_size)

        #NoC received msg ACK or error packet
        if (id_string == "NOC_MSG_ACK" or id_string == "NOC_ACK_ERR"):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_error = (lower_data64 >> 48) & 0x1F
            return ret_string + "from tile: {}, error: {:d}".format(modid_to_tile(log_modid), log_error)

        if (id_string == "NOC_ERROR" or id_string == "NOC_ERROR_UNEXP"):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_addr = ((upper_data64 & 0xFFFF) << 16) | ((lower_data64 >> 48) & 0xFFFF)
            log_error = (upper_data64 >> 16) & 0x1F
            return ret_string + "from tile: {}, addr: {:#010x}, error: {:d}".format(modid_to_tile(log_modid), log_addr, log_error)

        #NoC received packet with invalid data
        if (id_string == "NOC_INVMODE" or id_string == "NOC_INVFLIT"):
            log_modid = (lower_data64 >> 40) & 0xFF
            log_mode = (lower_data64 >> 48) & 0xF
            log_addr = ((upper_data64 & 0xFFFFF) << 12) | (lower_data64 >> 52)
            log_burst_flag = (upper_data64 >> 20) & 0x1
            log_burst_length = (lower_data64 >> 21) & 0xFFFF
            return ret_string + "from tile: {}, mode: {:d}, addr: {:#010x}, burst flag: {}, burst length: {:d}".format(modid_to_tile(log_modid), log_mode, log_addr, log_burst_flag, log_burst_length)

        #priv. cmds
        #invalidate page
        if (id_string == "CMD_PRIV_INV_PAGE"):
            log_actid = (lower_data64 >> 40) & 0xFFFF
            log_virt = ((upper_data64 & 0xFFFFFFFFFFF) << 8) | (lower_data64 >> 56)
            return ret_string + "actid: {:#x}, virt. page: {:#015x}".format(log_actid, log_virt)

        #insert TLB
        if (id_string == "CMD_PRIV_INS_TLB"):
            log_actid = (lower_data64 >> 40) & 0xFFFF
            log_virt = ((upper_data64 & 0xFFFFFFFFFFF) << 8) | (lower_data64 >> 56)
            log_phys = (upper_data64 >> 44) & 0xFFFFF
            return ret_string + "actid: {:#x}, virt. page: {:#015x}, phys. page: {:#07x}".format(log_actid, log_virt, log_phys)

        #xchg_act (act=id+msgs)
        if (id_string == "CMD_PRIV_XCHG_VPE"):
            log_curact = ((upper_data64 & 0xFF) << 24) | (lower_data64 >> 40)
            log_xchgact = (upper_data64 >> 8) & 0xFFFFFFFF
            return ret_string + "cur_act: {:#x}, xchg_act: {:#x}".format(log_curact, log_xchgact)

        #timer
        if (id_string == "CMD_PRIV_SET_TIMER"):
            log_nanos = ((upper_data64 & 0xFF) << 24) | (lower_data64 >> 40)
            return ret_string + "nanos: {:d}".format(log_nanos)

        #finish
        if (id_string == "CMD_PRIV_FINISH"):
            log_error = (lower_data64 >> 40) & 0x1F
            return ret_string + "error: {:d}".format(log_error)

        #core request
        if (id_string == "PRIV_CORE_REQ_FORMSG"):
            log_actid = (lower_data64 >> 40) & 0xFFFF
            log_ep = ((upper_data64 & 0xFF) << 8) | (lower_data64 >> 56)
            return ret_string + "actid: {:#x}, ep: {:d}".format(log_actid, log_ep)

        #TLB write
        if (id_string == "PRIV_TLB_WRITE_ENTRY"):
            log_tlb_actid = (lower_data64 >> 40) & 0xFFFF
            log_tlb_virtpage = ((upper_data64 & 0xFFFFFFFFFFF) << 8) | (lower_data64 >> 56)
            log_tlb_physpage = (upper_data64 >> 44) & 0xFFFFF
            return ret_string + "actid: {:#x}, virt. page: {:#015x}, phys. page: {:#07x}".format(log_tlb_actid, log_tlb_virtpage, log_tlb_physpage)

        #TLB read
        if (id_string == "PRIV_TLB_READ_ENTRY"):
            log_tlb_actid = (lower_data64 >> 40) & 0xFFFF
            log_tlb_virtpage = ((upper_data64 & 0xFFFFFFFFFFF) << 8) | (lower_data64 >> 56)
            log_tlb_physpage = (upper_data64 >> 44) & 0xFFFFF
            return ret_string + "actid: {:#x}, virt. page: {:#015x}, read phys. page: {:#07x}".format(log_tlb_actid, log_tlb_virtpage, log_tlb_physpage)

        #TLB invalidate page
        if (id_string == "PRIV_TLB_DEL_ENTRY"):
            log_tlb_actid = (lower_data64 >> 40) & 0xFFFF
            log_tlb_virtpage = ((upper_data64 & 0xFFFFFFFFFFF) << 8) | (lower_data64 >> 56)
            return ret_string + "actid: {:#x}, virt. page: {:#015x}".format(log_tlb_actid, log_tlb_virtpage)

        #reg CUR_VPE has changed its value
        if (id_string == "PRIV_CUR_VPE_CHANGE"):
            log_new_cur_act = ((upper_data64 & 0xFF) << 24) | (lower_data64 >> 40)
            log_old_cur_act = (upper_data64 >> 8) & 0xFFFFFFFF
            return ret_string + "old cur_act: {:#x}, new cur_act: {:#x}".format(log_old_cur_act, log_new_cur_act)

        #PMP: access from core not allowed
        if (id_string == "PMP_ACCESS_DENIED"):
            log_mode = (lower_data64 >> 40) & 0xF
            log_addr = ((upper_data64 & 0xFFF) << 20) | (lower_data64 >> 44)
            log_size = (upper_data64 >> 12) & 0xFFFF
            return ret_string + "mode: {:d}, addr: {:#010x}, size: {:d}".format(log_mode, log_addr, log_size)

        return ret_string

    def __init__(self):
        pass

    def get_tcu_log(self, log_id):
        if (log_id >= len(self.LOG_ID)):
            return "UNDEFINED"
        return self.LOG_ID[log_id]


class TCU():

    TCU_EP_REG_COUNT = 128
    TCU_CFG_REG_COUNT = 32
    TCU_STATUS_REG_COUNT = 5
    TCU_LOG_REG_COUNT = 2**17

    TCU_EP_REG_SIZE = 0x18
    TCU_CFG_REG_SIZE = 0x8
    TCU_STATUS_REG_SIZE = 0x8

    TCU_REGADDR_START = 0xF000_0000

    #ext regs
    TCU_REGADDR_FEATURES = TCU_REGADDR_START + 0x0000_0000
    TCU_REGADDR_EXT_CMD  = TCU_REGADDR_START + 0x0000_0008

    #unpriv. regs
    TCU_REGADDR_COMMAND   = TCU_REGADDR_START + 0x0000_0010
    TCU_REGADDR_DATA_ADDR = TCU_REGADDR_START + 0x0000_0018
    TCU_REGADDR_DATA_SIZE = TCU_REGADDR_START + 0x0000_0020
    TCU_REGADDR_ARG1      = TCU_REGADDR_START + 0x0000_0028
    TCU_REGADDR_CUR_TIME  = TCU_REGADDR_START + 0x0000_0030

    #ep regs
    TCU_REGADDR_EP_START = TCU_REGADDR_START + 0x0000_0040

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
    TCU_REGADDR_TCU_BYP_FLIT_COUNT  = TCU_REGADDR_START + 0x0000_3018
    TCU_REGADDR_TCU_DROP_FLIT_COUNT = TCU_REGADDR_START + 0x0000_3020

    #config regs for core
    TCU_REGADDR_CORE_CFG_START = TCU_REGADDR_TCU_STATUS + TCU_STATUS_REG_COUNT*TCU_STATUS_REG_SIZE

    #addr of log mem
    TCU_REGADDR_TCU_LOG = TCU_REGADDR_START + 0x0100_0000
