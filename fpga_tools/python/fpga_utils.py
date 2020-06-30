
import os
import sys
import time
import threading


class FPGA_Error(Exception):
    pass


class Progress(threading.Thread):
    MIN_UPD_INVL =  0.1
    EST_UPD_INVL =  1.0
    def __init__(self, label="status", max=1000, format="iec", wait=1.0):
        self.label = label
        self.max = max
        self.value = 0
        self.lvalue = None
        self.lupdate = 0.0
        self.running = True
        self.format = format
        self.begin = time.time() + wait
        super(Progress, self).__init__()
        self.daemon = True
        self.start()

    def run(self):
        while self.running:
            if self._needupd():
                self._upd()
            time.sleep(self.MIN_UPD_INVL)

    def setmax(self, max):
        self.max = max

    def advance(self, amount):
        self.value += amount

    def clear(self):
        self.running = False
        self.join()
        if self.begin is None:
            print("\r%s - (done)" % self.label, " " * 20)

    def _needupd(self):
        if self.lupdate + self.MIN_UPD_INVL > time.time():
            return False
        if self.value == self.lvalue:
            return False
        if self.begin is not None and self.begin > time.time():
            return False
        return True

    def _upd(self):
        #next update
        self.lupdate = time.time()
        self.lvalue = self.value
        #render values
        if self.format == "iec":
            curval = iec_size(self.value)
            maxval = iec_size(self.max)
        else:
            curval = str(self.value)
            maxval = str(self.max)
        #
        if self.begin is not None:
            self.begin = None
        print("\r%s %s/%s (%.1f%%)" % (self.label, curval, maxval, float(self.value) / self.max * 100.0))
        sys.stdout.flush()