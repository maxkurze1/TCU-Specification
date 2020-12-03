
import noc
import memory
from tcu import TCU, EP, LOG
from fpga_utils import Progress


class PM():
    #Rocket interrupt
    ROCKET_INT_COUNT = 2

    def __init__(self, nocif, nocid, pm_num):
        self.nocid = nocid
        self.shortname = "pm%d" % pm_num
        self.name = "PM%d" % pm_num
        self.mem = memory.Memory(nocif, self.nocid)
        self.pm_num = pm_num

    def __repr__(self):
        return self.name

    def start(self):
        self.mem[TCU.TCU_REGADDR_CORE_CFG_START] = 1

    def stop(self):
        self.mem[TCU.TCU_REGADDR_CORE_CFG_START] = 0

    def getEnable(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START]

    def tcu_status(self):
        status = self.mem[TCU.TCU_REGADDR_TCU_STATUS]
        return (status & 0xFF, (status >> 8) & 0xFF, (status >> 16) & 0xFF)

    def tcu_reset(self):
        self.mem[TCU.TCU_REGADDR_TCU_RESET] = 1

    def tcu_set_privileged(self, priv):
        self.mem[TCU.TCU_REGADDR_FEATURES] = priv

    def tcu_get_ep(self, ep_id):
        r0 = self.mem[TCU.TCU_REGADDR_EP_START + (8 * 3) * ep_id + 0]
        r1 = self.mem[TCU.TCU_REGADDR_EP_START + (8 * 3) * ep_id + 8]
        r2 = self.mem[TCU.TCU_REGADDR_EP_START + (8 * 3) * ep_id + 16]
        return EP.from_regs([r0, r1, r2])

    def tcu_set_ep(self, ep_id, ep):
        self.mem[TCU.TCU_REGADDR_EP_START + (8 * 3) * ep_id + 0] = ep.regs[0]
        self.mem[TCU.TCU_REGADDR_EP_START + (8 * 3) * ep_id + 8] = ep.regs[1]
        self.mem[TCU.TCU_REGADDR_EP_START + (8 * 3) * ep_id + 16] = ep.regs[2]

    def tcu_ctrl_flit_count(self):
        flits = self.mem[TCU.TCU_REGADDR_TCU_CTRL_FLIT_COUNT]
        flits_rx = flits & 0xFFFFFFFF
        flits_tx = flits >> 32
        return (flits_tx, flits_rx)

    def tcu_io_flit_count(self):
        flits = self.mem[TCU.TCU_REGADDR_TCU_IO_FLIT_COUNT]
        flits_rx = flits & 0xFFFFFFFF
        flits_tx = flits >> 32
        return (flits_tx, flits_rx)

    def tcu_drop_flit_count(self):
        return self.mem[TCU.TCU_REGADDR_TCU_DROP_FLIT_COUNT]

    def tcu_print_log(self, filename):
        log_count = self.mem[TCU.TCU_REGADDR_TCU_LOG]
        print("%s: Number of TCU log messages: %d" % (self.name, log_count))

        fh = open(filename, 'w')
        fh.write("%s: Number of TCU log messages: %d\n" % (self.name, log_count))

        if log_count > 0:
            for i in range(log_count):
                lower = self.mem[TCU.TCU_REGADDR_TCU_LOG+8+i*16]
                upper = self.mem[TCU.TCU_REGADDR_TCU_LOG+16+i*16]
                fh.write("%5d: %s\n" % (i, LOG.split_tcu_log(upper, lower)))
        fh.close()


    #----------------------------------------------
    #special functions for PicoRV32 RISC-V core

    #interrupt val (32 bit)
    def pico_setIRQ(self, val32):
        self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x10] = val32

    def pico_getIRQ(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x10]

    def pico_getEOI(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x18]

    def pico_getTrap(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x8]

    #set stack addr
    def pico_setStackAddr(self, val32):
        self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x20] = val32

    def pico_getStackAddr(self):
        return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x20]

    #----------------------------------------------
    #special functions for Rocket RISC-V core

    #interrupt val
    def rocket_setInt(self, int_num, val):
        if (int_num < self.ROCKET_INT_COUNT):
            self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x8+8*int_num] = val
        else:
            print("Interrupt %d not supported for Rocket core. Max = %d" % (int_num, self.ROCKET_INT_COUNT))

    def rocket_getInt(self, int_num):
        if (int_num < self.ROCKET_INT_COUNT):
            return self.mem[TCU.TCU_REGADDR_CORE_CFG_START+0x8+8*int_num]
        else:
            print("Interrupt %d not supported for Rocket core. Max = %d" % (int_num, self.ROCKET_INT_COUNT))
            return 0

    #start core via interrupt 0
    def rocket_start(self):
        self.rocket_setInt(0, 1)
        self.rocket_setInt(0, 0)
