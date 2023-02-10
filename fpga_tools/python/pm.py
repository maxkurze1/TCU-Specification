
import noc
import memory
from tcu import TCUStatusReg, TCUExtReg, EP, LOG
from fpga_utils import Progress


class PM():
    #Rocket interrupt
    ROCKET_INT_COUNT = 2
    ROCKET_TRACEMEM_BASE = 0x00100000
    ROCKET_TRACEMEM_SIZE = 1024

    def __init__(self, tcu, nocif, nocid, pm_num):
        self.tcu = tcu
        self.nocid = nocid
        self.shortname = "pm%d" % pm_num
        self.name = "PM%d" % pm_num
        self.mem = memory.Memory(nocif, self.nocid)
        self.nocarq = noc.NoCARQRegfile(self.nocid)
        self.pm_num = pm_num

    def __repr__(self):
        return self.name

    def start(self):
        self.mem[self.tcu.config_reg_addr(0)] = 1

    def stop(self):
        self.mem[self.tcu.config_reg_addr(0)] = 0

    def getEnable(self):
        return self.mem[self.tcu.config_reg_addr(0)]

    def tcu_get_ep(self, ep_id):
        r0 = self.mem[self.tcu.ep_addr(ep_id) + 0]
        r1 = self.mem[self.tcu.ep_addr(ep_id) + 8]
        r2 = self.mem[self.tcu.ep_addr(ep_id) + 16]
        return EP.from_regs([r0, r1, r2])

    def tcu_set_ep(self, ep_id, ep):
        self.mem[self.tcu.ep_addr(ep_id) + 0] = ep.regs[0]
        self.mem[self.tcu.ep_addr(ep_id) + 8] = ep.regs[1]
        self.mem[self.tcu.ep_addr(ep_id) + 16] = ep.regs[2]

    def tcu_set_features(self, priv, vm, ctxsw):
        flags = ((ctxsw & 0x1) << 2) | ((vm & 0x1) << 1) | (priv & 0x1)
        self.mem[self.tcu.ext_reg_addr(TCUExtReg.FEATURES)] = self.tcu.version << 32 | flags

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

    def tcu_print_log(self, filename, all=False):
        # open and truncate file first (reads below might fail)
        fh = open(filename, 'w')

        if all:
            log_count = 65536
        else:
            log_count = self.mem[self.tcu.log_addr()]

        print("%s: Number of TCU log messages: %d" % (self.name, log_count))
        if log_count > 65536:
            fh.write("%s: Number of TCU log messages: %d (only 65536 shown, last log at %d)\n" % (self.name, log_count, log_count%65536-1))
            log_count = 65536
        else:
            fh.write("%s: Number of TCU log messages: %d\n" % (self.name, log_count))

        #read log mem: first log is at TCU_REGADDR_TCU_LOG+0x10
        if log_count > 0:
            for i in range(log_count):
                lower = self.mem[self.tcu.log_addr() + 0x10 + i * 16]
                upper = self.mem[self.tcu.log_addr() + 0x18 + i * 16]
                fh.write("%5d: %s\n" % (i, LOG.split_tcu_log(self.tcu.version, upper, lower)))
        fh.close()

    def tcu_set_log_mask(self, mask):
        """
        Set log selection mask. Default value: 0xFFFFFFFF
        Each bit of the mask represents a log id from list TCU.LOG_ID starting with bit 0 = CMD_SEND
        If the bit in the mask is set, the TCU writes the log with this id to log mem.
        """
        self.mem[self.tcu.log_addr() + 8] = mask

    def tcu_get_log_mask(self):
        return self.mem[self.tcu.log_addr() + 8]


    #----------------------------------------------
    #special functions for PicoRV32 RISC-V core

    #interrupt val (32 bit)
    def pico_setIRQ(self, val32):
        self.mem[self.tcu.config_reg_addr(2)] = val32

    def pico_getIRQ(self):
        return self.mem[self.tcu.config_reg_addr(2)]

    def pico_getEOI(self):
        return self.mem[self.tcu.config_reg_addr(3)]

    def pico_getTrap(self):
        return self.mem[self.tcu.config_reg_addr(1)]

    #set stack addr
    def pico_setStackAddr(self, val32):
        self.mem[self.tcu.config_reg_addr(4)] = val32

    def pico_getStackAddr(self):
        return self.mem[self.tcu.config_reg_addr(4)]

    #----------------------------------------------
    #special functions for Rocket RISC-V core

    #interrupt val
    def rocket_setInt(self, int_num, val):
        if (int_num < self.ROCKET_INT_COUNT):
            self.mem[self.tcu.config_reg_addr(1 + int_num)] = val
        else:
            print("Interrupt %d not supported for Rocket core. Max = %d" % (int_num, self.ROCKET_INT_COUNT))

    def rocket_getInt(self, int_num):
        if (int_num < self.ROCKET_INT_COUNT):
            return self.mem[self.tcu.config_reg_addr(1 + int_num)]
        else:
            print("Interrupt %d not supported for Rocket core. Max = %d" % (int_num, self.ROCKET_INT_COUNT))
            return 0

    #start core via interrupt 0
    def rocket_start(self):
        self.rocket_setInt(0, 1)

    def rocket_getTCUAXIBridgeError(self):
        return self.mem[self.tcu.config_reg_addr(6)]

    def rocket_getAXIMemBridgeError(self):
        return self.mem[self.tcu.config_reg_addr(7)]

    def rocket_enableTrace(self):
        self.mem[self.tcu.config_reg_addr(8)] = 1

    def rocket_disableTrace(self):
        self.mem[self.tcu.config_reg_addr(8)] = 0

    def rocket_printTrace(self, filename, all=False):
        #make sure trace is stopped before reading it
        self.rocket_disableTrace()

        #open file first (reads below might fail)
        fh = open(filename, 'w')

        #read trace count
        trace_count = self.mem[self.tcu.config_reg_addr(10)]
        if all:
            trace_count = self.ROCKET_TRACEMEM_SIZE

        print("%s: Number of Rocket instruction traces: %d" % (self.name, trace_count))
        fh.write("%s: Number of Rocket instruction traces: %d\n" % (self.name, trace_count))

        if trace_count > 0:
            fh.write("columns: addr opcode priv.-level exception interrupt cause tval\n")

            #read current idx to calculate address of first trace
            trace_current_idx = self.mem[self.tcu.config_reg_addr(9)]
            if trace_current_idx >= trace_count:
                trace_start_idx = trace_current_idx - trace_count
            else:
                trace_start_idx = self.ROCKET_TRACEMEM_SIZE + trace_current_idx - trace_count
            trace_start_addr = self.ROCKET_TRACEMEM_BASE + 32*trace_start_idx

            tmp_count = trace_count
            #reduce tmp_count if traces wrap around
            if (trace_start_idx+trace_count) > self.ROCKET_TRACEMEM_SIZE:
                tmp_count = self.ROCKET_TRACEMEM_SIZE - trace_start_idx

            #read traces, one trace occupies 32 byte
            trace_data = self.mem.read_words(trace_start_addr, tmp_count*4)

            #read the rest from start of trace memory
            if tmp_count < trace_count:
                trace_data_rest = self.mem.read_words(self.ROCKET_TRACEMEM_BASE, (trace_count-tmp_count)*4)
                trace_data.extend(trace_data_rest)

            #print to file
            for i in range(0, trace_count*4, 4):
                trace_addr = trace_data[i] & 0xFFFFFFFF
                trace_opcode = trace_data[i] >> 32
                trace_priv = trace_data[i+1] & 0x7
                trace_except = (trace_data[i+1] >> 3) & 0x1
                trace_int = (trace_data[i+1] >> 4) & 0x1
                trace_cause = ((trace_data[i+2] & 0x1F) << 59) |  (trace_data[i+1] >> 5)
                trace_tval = trace_data[i+2] >> 5
                fh.write("{:4d}: {:#010x} {:#010x} {:d} {:d} {:d} {:#018x} {:#010x}\n".format(i>>2, trace_addr, trace_opcode, trace_priv, trace_except, trace_int, trace_cause, trace_tval))

        fh.close()
