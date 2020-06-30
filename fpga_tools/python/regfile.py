
import noc
import memory


class REGFILE(memory.Memory):
    RF_BASE_ADDR = 0x00000000
    COUNTER_SETGET_ADDR = 0x10
    COUNTER_START_ADDR = 0x14
    def __init__(self, nocif, nocid):
        self.nocid = nocid
        self.mem = self
        self.shortname = "rf"
        self.name = "Register File"
        self.mem_rf = memory.Memory(nocif, self.nocid, self.RF_BASE_ADDR)
        #memory.Memory.__init__(self, nocif, self.nocid, self.RF_BASE_ADDR)

    def counter_start(self):
        self.mem_rf[self.RF_BASE_ADDR+self.COUNTER_START_ADDR] = 1

    def counter_stop(self):
        self.mem_rf[self.RF_BASE_ADDR+self.COUNTER_START_ADDR] = 0

    def counter_set(self, val):
        self.mem_rf[self.RF_BASE_ADDR+self.COUNTER_SETGET_ADDR] = val

    def counter_read(self):
        return self.mem_rf[self.RF_BASE_ADDR+self.COUNTER_SETGET_ADDR]
