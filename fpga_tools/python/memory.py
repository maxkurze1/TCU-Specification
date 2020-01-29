"""
accessing memory modules on the chip
"""
def memfilestream(fname):
    """reads the contend of the file and returns a stream of datablocks.
    this stream can be passed to Memory_Slice.writememdata()"""
    fhand = open(fname, 'r')
    addr = 0
    data = []
    for line in fhand:
        if line[0] == '@':
            if data:
                yield MemSlice(addr, data)
            naddr = int(line[1:9], 16)*8
            assert naddr >= addr + len(data)*8
            addr = naddr
            data = []
        else:
            data.append(int(line[0:16], 16))
    if data:
        yield MemSlice(addr, data)

def memusage(fname):
    """prints the sizes of each memory block in the file"""
    for slic in memfilestream(fname):
        print("%08x - %08x (%i B)" % (slic.begin, slic.end(), len(slic)))


class Memory(object):
    """
    represents a memory module on the chip
    """
    def __init__(self, nocif, nocid, offset=0, ispe=False):
        self.nocif = nocif
        self.nocid = nocid
        self.ispe = ispe
        self.offset = offset

    def read(self, start, amount):
        """
        read values from the memory returning a MemSlice object
        """
        #assert start % 8 == 0
        if amount == 1:
            data = [x.data0 for x in self.nocif.read(self.nocid, start + self.offset, amount)]
        else:
            data = []
            for x in self.nocif.read(self.nocid, start + self.offset, amount):
                data.append(x.data0)
                data.append(x.data1)
        return MemSlice(start, data)

    def write(self, slic, force_no_burst=False):
        """
        write MemSlice object to memory
        """
        assert isinstance(slic, MemSlice)
        self.nocif.write(self.nocid, slic.begin + self.offset, slic.data, force_no_burst)

    def writes(self, slics, force_no_burst=False):
        """
        writes multiple MemSlice objects to memory
        """
        for slic in slics:
            self.write(slic, force_no_burst)

    def check(self, slic):
        """
        check if the data from a MemSlice is present in the memory
        """
        curr = self.read(slic.begin, len(slic) / 8)
        if curr != slic:
            return False
        else:
            return True

    def checks(self, slics):
        """
        checks multiple MemSlices for live consistency
        """
        for slic in slics:
            if not self.check(slic):
                return False
        return True

    def set32(self, start, val):
        """
        writes a list of 32bit vales to a memory address
        """
        assert isinstance(start, int), "address must be a integer"
        if isinstance(val, int):
            return self.set32(start, [val])
        assert isinstance(val, list), "values must be an integer or a list"
        assert start & 0x3 == 0, "bad start address for 32bit set"
        lst = []
        vals = val[:]
        if start & 0x4:
            start &= 0xfffffff8
            data = self[start]
            lst.append((data & 0xffffffff) | (vals.pop(0) << 32))
        for i in range(len(vals)/2):
            lst.append((vals[i*2+1] << 32) | vals[i*2])
        if len(vals) % 2:
            data = self[start + len(lst) * 8]
            lst.append((data & 0xffffffff00000000) | vals[-1])
        self.write(MemSlice(start, lst))

    def set64(self, start, val):
        """
        writes a list of 64bit vales to a memory address
        """
        assert isinstance(start, int), "address must be a integer"
        if isinstance(val, (int, int)):
            return self.set64(start, [val])
        assert isinstance(val, list), "values must be an integer or a list"
        self.write(MemSlice(start, val))

    def __repr__(self):
        return '<Memory Module:%d:%d>' % self.nocid

    def __setitem__(self, idx, val):
        if isinstance(idx, slice):
            assert idx.step == None, "Slice stepping not supported!"
            assert idx.start % 8 == 0 and idx.stop % 8 == 0, \
                "range is not 8-byte aligned: 0x%x:0x%x" % (idx.start. idx.stop)
            size = (idx.stop - idx.start) / 8
            if isinstance(val, int):
                val = [val] * size
            assert isinstance(val, list)
            if len(val) < size:
                val = val * (size / len(val) + 1)
                val = val[:int(size)]
            elif len(val) > size:
                val = val[:int(size)]    #only send 'size' values, not length of val
            self.write(MemSlice(idx.start, val))

        elif isinstance(idx, int):
            assert isinstance(val, int)
            self.write(MemSlice(idx, [val]))

        else:
            assert False, "setitem: index type:%s (%s)" % (type(idx), idx)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            assert idx.step == None, "Slice stepping not supported!"
            assert idx.start % 8 == 0 and idx.stop % 8 == 0, \
                "range is not 8-byte aligned: 0x%x:0x%x" % (idx.start, idx.stop)
            size = (idx.stop - idx.start) / 8
            return self.read(idx.start, size)
        elif isinstance(idx, int):
            assert idx % 8 == 0, "index must be 8-byte aligned 0x%x" % idx
            slic = self.read(idx, 1)
            return slic.data[0]
        else:
            assert False, "getitem: index type: %s (%s)" % (type(idx), idx)


class MemSlice(object):
    """
    represents a data piece of a memory
    """
    def __init__(self, begin, data):
        assert isinstance(data, list)
        for val in data:
            assert isinstance(val, int), "data entries should be int not %s (%s)" % (type(val), val)
        self.begin = int(begin)
        self.data = data

    def end(self):
        """
        returns the end address of the mem slice
        """
        return self.begin + len(self)

    def __len__(self):
        return len(self.data) * 8

    def __cmp__(self, other):
        #ret = cmp(self.begin, other.begin)
        #no cmp function in Python3
        ret = (self.begin > other.begin) - (self.begin < other.begin)
        if ret:
            return ret
        #ret = cmp(len(self), len(other))
        ret = (len(self) > len(other)) - (len(self) < len(other))
        if ret:
            return ret
        for val1, val2 in zip(self.data, other.data):
            #ret = cmp(val1, val2)
            ret = (val1 > val2) - (val1 < val2)
            if ret:
                return ret
        return 0

    def __getitem__(self, idx):
        return self.get64(idx)

    def get64(self, addr):
        """
        get a 64bit data word from a specified address
        """
        assert addr >= self.begin and addr < self.end() and addr % 8 == 0, \
            "cannot get item %x from [%x,%x]" % (addr, self.begin, self.end())
        return self.data[(addr - self.begin) / 8]

    def get32(self, addr):
        """
        get a 32bit data word from a specified address
        """
        assert (addr & 0x3) == 0, "addr is not 4 byte aligned 0x%x" % addr
        data = self[addr & 0xfffffff8]
        if addr & 0x7 == 0:
            return data & 0xffffffff
        else:
            return data >> 32

    def dump(self, rev=False, do32=False, offset=0):
        """
        prints the mem slice to the console. Each value in one line with its
        address. The list can be printed in reversed order (high -> low address)
        with rev=True. 32bit values can be used by specifieing do32=True. The
        printed can be offsetted by setting offset=[value]
        """
        dat = [(offset + self.begin + 8 * idx, data) \
            for idx, data in enumerate(self.data)]
        if do32:
            datt = []
            for addr, data in dat:
                datt.append((addr, data & 0xffffffff))
                datt.append((addr + 4, data >> 32))
            dat = datt
            fmt = "0x%8x: 0x%8x (%10d)"
        else:
            fmt = "0x%8x: 0x%16x (%20d)"
        if rev:
            dat.reverse()
        for addr, data in dat:
            print(fmt % (addr, data, data))

    def getdict(self, b32=False):
        """
        returns a dictionary assigning address -> data
        """
        if b32:
            ret = {}
            for adr in range(self.begin, self.begin + len(self), 4):
                ret[adr] = self.get32(adr)
            return ret
        else:
            return {self.begin + i*8 : data for i, data in enumerate(self.data)}

    def __iter__(self):
        for i, data in enumerate(self.data):
            yield self.begin + i * 8, data

    def iter32(self):
        """
        iterator for 32bit values
        """
        for i, data in enumerate(self.data):
            yield self.begin + i * 8, data & 0xffffffff
            yield self.begin + i * 8 + 4, data >> 32
