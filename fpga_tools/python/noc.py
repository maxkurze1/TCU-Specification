"""
this module implements the driver for the NoC acces via ethernet
"""
import struct
import threading
import socket
import select
import time
import re
import copy

from fpga_utils import FPGA_Error
import modids
import memory

MODE_READ_REQ = 0x0
MODE_READ_RESP = 0x1
MODE_WRITE_POSTED = 0x2


def str2mode(mode):
    """converts noc packet modes to human readable string"""
    return {
        'MODE_READ_REQ' : MODE_READ_REQ,
        'MODE_READ_RSP' : MODE_READ_RESP,
        'MODE_WRITE_POSTED' : MODE_WRITE_POSTED,
        'DUMMY' : 0xf
    }[mode]

def mode2str(mode):
    """converts noc packet modes to human readable string"""
    try:
        return {
            MODE_READ_REQ : 'MODE_READ_REQ',
            MODE_READ_RESP : 'READ_RSP',
            MODE_WRITE_POSTED : 'WRITE_POSTED',
            0xf: 'DUMMY'
        }[mode]
    except KeyError:
        return "mode:%d" % mode

class noc_packet:
    """
    struct to hold a noc packet or a noc packet burst
    """
    def __init__(self):
        self.data0 = 0          #64
        self.data1 = 0          #64
        self.addr = 0           #32
        self.mode = 0           # 4
        self.trg_chipid = 0     # 6
        self.trg_modid = 0      # 8
        self.src_chipid = 0     # 6
        self.src_modid = 0      # 8
        self.bsel = 0           # 8
        self.burst = 0          # 1

    def dump(self, is_burst=False):
        """dump the data of the packet to the console"""
        print("noc_packet:")
        if not is_burst:
            print("  data0: 0x%x" % self.data0)
            print("  data1: 0x%x" % self.data1)
            print("  addr: 0x%x" % self.addr)
            print("  mode: 0x%x (%s)" % (self.mode, mode2str(self.mode)))
            print("  trg_chipid: 0x%x" % self.trg_chipid)
            print("  trg_modid: 0x%x" % self.trg_modid)
            print("  src_chipid: 0x%x" % self.src_chipid)
            print("  src_modid: 0x%x" % self.src_modid)
            print("  bsel: 0x%x" % self.bsel)
            print("  burst: 0x%x" % self.burst)
        else:
            print("  data0: 0x%x" % self.data0)
            print("  data1: 0x%x" % self.data1)
            print("  bsel: 0x%x" % self.bsel)
            print("  burst: 0x%x" % self.burst)

    def prepare(self, trg_id, adr, data, mode=MODE_WRITE_POSTED, burst=0, bsel=0xFF, src_adr=(0,modids.MODID_ETH)):
        self.data0 = data
        self.addr = adr
        self.mode = mode
        self.trg_chipid = trg_id[0]
        self.trg_modid = trg_id[1]
        self.src_chipid = src_adr[0]
        self.src_modid = src_adr[1]
        self.bsel = bsel
        self.burst = burst

    def prepare_burst(self, data0, data1, burst, bsel=0xFF):
        self.data0 = data0
        self.data1 = data1
        self.bsel = bsel
        self.burst = burst


def check_adr(adr):
    if not isinstance(adr, tuple):
        return False
    if len(adr) != 2:
        return False
    if not isinstance(adr[0], int) or not isinstance(adr[1], int):
        return False
    return True

class NoCgateway(object):
    READRETRY = 3
    BURST_MAX = 32 #max. number of flits in burst (16 byte data)
    LOGFILE = "log/noc.log"
    READTIMEOUT = 0.5
    def __init__(self):
        self.recvbuf = [] #packets received recently
        self.sendbuf = [] #packets queued for sending
        self.fails = 0    #retry counter
        self.recvd = 0    # # of packets send
        self.sendd = 0    # # of packets recvd
        self.flog = open(self.LOGFILE, "w")
        self.noclogging = True

    def recv(self):
        raise FPGA_Error("called abstract method: NoC_gateway::recv")

    def send_flush(self, lasy=False):
        raise FPGA_Error("called abstract method: NoC_gateway::send_flush")

    def tear(self):
        pass

    def recv_packet(self, src_id=None, addr_range=None, timeout=0.5):
        """
        get one packet out of recvbuf, if desired check response address and nocid
        """
        if addr_range is None:
            addr_range = (0x00000000, 0xffffffff)
        if isinstance(addr_range, int):
            addr_range = (addr_range, addr_range)
        #print("looking for packet @ (0x%08x,0x%08x) from %s - avail %d" % (addr_range[0], addr_range[1], src_id, len(self.recvbuf)))

        #if there are no packets in receive buffer, poll socket
        if len(self.recvbuf) == 0:
            self.recv()

        now = time.time()
        start = now
        while timeout is None or start + timeout >= now:
            ret = None
            #print("Get packets from recvbuf:")
            for pack in self.recvbuf:
                #pack.dump()
                #print("check with addr_range=%x:%x" % (addr_range[0], addr_range[1]))
                #if src_id is not None:
                #    print("check with modid=%x" % src_id[1])

                if pack.addr >= addr_range[0] and pack.addr <= addr_range[1] and (src_id is None or (pack.src_modid == src_id[1] and pack.src_chipid == src_id[0])):
                    #print("packet found")
                    ret = pack
                    break
            if ret:
                self.recvbuf.remove(ret)
                #print "recv from %d @0x%8x - 0x%16x" % (ret.src_modid, ret.addr, ret.data)
                return ret
            self.recv()
            now = time.time()
        return None

    def send_packet(self, packet, flush=False):
        """
        converts a packet to binary data pushing it to the send buffer.
        Flushes the buffer when it is full or flush=True
        """
        self.sendbuf.append(copy.copy(packet))
        if flush:
            self.send_flush()

    def write(self, trg_id, addr, data_list, force_no_burst=False):
        """
        write data to memory. data should be an array of 64bit data sets
        """

        pack = noc_packet()

        #check for burst
        if not force_no_burst:
            assert (len(data_list)/2 <= self.BURST_MAX), "len(data_list)/2 must be smaller than %d (%d)" % (self.BURST_MAX, len(data_list))

            #do a burst transfer
            if (len(data_list) > 1):
                #first packet of burst, burst length in data field
                #bsel determines number of data (assume 64-bit types)
                bsel = 0xFF if ((len(data_list) % 2) == 0) else 0x7F
                pack.prepare(trg_id, addr, int(len(data_list)/2), MODE_WRITE_POSTED, 1, bsel)
                self.send_packet(pack)

                while (len(data_list) > 2):
                    pack.prepare_burst(data_list[0], data_list[1], 1)
                    #pack.dump(is_burst=True)
                    self.send_packet(pack)
                    data_list.pop(0)
                    data_list.pop(0)


                #last packet of burst
                pack.prepare_burst(data_list[len(data_list)-2], data_list[len(data_list)-1], 0)
                self.send_packet(pack)

                data_list.pop(0)
                data_list.pop(0)

            #no burst, single packet
            else:
                pack.prepare(trg_id, addr, data_list[0], MODE_WRITE_POSTED)
                self.send_packet(pack, flush=True)

        #send multiple single packets
        else:
            for i in range(len(data_list)):
                pack.prepare(trg_id, addr+i*8, data_list[i], MODE_WRITE_POSTED)
                self.send_packet(pack, flush=True)
            data_list.clear()

        self.send_flush()


    def read(self, trg_id, start_addr, amount=1, recv_addr=0x0):
        """
        reads an array of a given length from a chip memory
        """
        assert check_adr(trg_id), "invalid adr: %s" % trg_id
        #assert start_addr % 8 == 0, "NoC read: addr must be 8-byte aligned: 0x%x" % start_addr
        start_addr = int(start_addr)
        amount = int(amount)    #number of 8-byte values
        #assert not ((amount % 2) and not (amount == 1))
        assert amount <= 2*self.BURST_MAX
        #print "fetch %x (%d)" % (start_addr, amount)
        done = 0
        reqd = 0
        send_read_data = (int(amount*8)<<32) | recv_addr   #NoC read-req flit counts number of byte
        pack = noc_packet()
        pack.prepare(trg_id, start_addr, send_read_data, MODE_READ_REQ)

        self.send_packet(pack, flush=True)

        read_fails = 0
        for received_flits in range(0, int(amount/2)+1):
            #only first packet includes nocid and address
            if received_flits == 0:
                recvd = self.recv_packet(trg_id, recv_addr)
            else:
                recvd = self.recv_packet(None, None)

            while recvd is None and (read_fails<self.READRETRY):
                print("WARNING: No response received (%d/%d): %x.%x:%x"  % (read_fails+1, self.READRETRY, trg_id[0], trg_id[1], start_addr))
                self.fails += 1
                read_fails += 1

                #try again
                self.send_packet(pack, flush=True)
                if received_flits == 0:
                    recvd = self.recv_packet(trg_id, recv_addr)
                else:
                    recvd = self.recv_packet(None, None)


            #if still nothing received, raise error
            if recvd is None:
                print("FAILED to get %x:%x 0x%x" % (trg_id[0], trg_id[1], start_addr))
                raise FPGA_Error("Receive error - giving up!")

            #if a burst was received, first packet does not contain data
            if not ((received_flits == 0) and (recvd.burst == 1)):
                yield recvd



class NoCethernet(NoCgateway):
    LOGFILE = "log/ethernet.log"
    UDP_PAYLOAD_LEN = 1472
    UDP_NOC_PACKET_LEN = 18 #single packet via UDP, burst or non-burst
    PACKETFREQ = 50000.0 #packets per second
    MINSLEEP = 0.02
    def __init__(self, send_ipaddr):
        super(NoCethernet, self).__init__()
        self.send_ipaddr = send_ipaddr
        self.socks = []
        self._reopensocks()
        self.lastsend = time.time()
        self.sleepaccu = 0
        if not self.testconnection():
            raise FPGA_Error("Ethernet connection test failed!")

    def recv(self):
        self._poll()

    def packet_pack(self, packet, is_burst=False):
        buf = bytearray(self.UDP_NOC_PACKET_LEN)
        if is_burst:
            buf[0]  = packet.burst
            buf[1]  = packet.bsel
            buf[2]  = (packet.data1 & 0xFF00000000000000) >> 56
            buf[3]  = (packet.data1 & 0x00FF000000000000) >> 48
            buf[4]  = (packet.data1 & 0x0000FF0000000000) >> 40
            buf[5]  = (packet.data1 & 0x000000FF00000000) >> 32
            buf[6]  = (packet.data1 & 0x00000000FF000000) >> 24
            buf[7]  = (packet.data1 & 0x0000000000FF0000) >> 16
            buf[8]  = (packet.data1 & 0x000000000000FF00) >> 8
            buf[9]  = (packet.data1 & 0x00000000000000FF)
            buf[10] = (packet.data0 & 0xFF00000000000000) >> 56
            buf[11] = (packet.data0 & 0x00FF000000000000) >> 48
            buf[12] = (packet.data0 & 0x0000FF0000000000) >> 40
            buf[13] = (packet.data0 & 0x000000FF00000000) >> 32
            buf[14] = (packet.data0 & 0x00000000FF000000) >> 24
            buf[15] = (packet.data0 & 0x0000000000FF0000) >> 16
            buf[16] = (packet.data0 & 0x000000000000FF00) >> 8
            buf[17] = (packet.data0 & 0x00000000000000FF)
        else:
            buf[0]  = packet.burst
            buf[1]  = packet.bsel
            buf[2]  = packet.src_modid
            buf[3]  = (packet.src_chipid << 2) | (packet.trg_modid >> 6)
            buf[4]  = (packet.trg_modid << 2) | (packet.trg_chipid >> 4)
            buf[5]  = (packet.trg_chipid << 4) | packet.mode
            buf[6]  = (packet.addr & 0xFF000000) >> 24
            buf[7]  = (packet.addr & 0x00FF0000) >> 16
            buf[8]  = (packet.addr & 0x0000FF00) >> 8
            buf[9]  = (packet.addr & 0x000000FF)
            buf[10] = (packet.data0 & 0xFF00000000000000) >> 56
            buf[11] = (packet.data0 & 0x00FF000000000000) >> 48
            buf[12] = (packet.data0 & 0x0000FF0000000000) >> 40
            buf[13] = (packet.data0 & 0x000000FF00000000) >> 32
            buf[14] = (packet.data0 & 0x00000000FF000000) >> 24
            buf[15] = (packet.data0 & 0x0000000000FF0000) >> 16
            buf[16] = (packet.data0 & 0x000000000000FF00) >> 8
            buf[17] = (packet.data0 & 0x00000000000000FF)

        return buf

    def packet_unpack(self, buf):
        """
        converts binary data to a noc_packet. returns that
        """
        pack0 = noc_packet()
        pack0.burst = buf[0]
        pack0.bsel = buf[1]
        pack0.src_modid = buf[2]
        pack0.src_chipid = buf[3] >> 2
        pack0.trg_modid = (buf[3] & 0x3) | (buf[4] >> 2)
        pack0.trg_chipid = (buf[4] & 0x3) | (buf[5] >> 4)
        pack0.mode = buf[5] & 0xF
        pack0.addr = (buf[6] << 24) | (buf[7] << 16) | (buf[8] << 8) | buf[9]
        pack0.data0 = (buf[10] << 56) | (buf[11] << 48) | (buf[12] << 40) | (buf[13] << 32) | (buf[14] << 24) | (buf[15] << 16) | (buf[16] << 8) | buf[17]
        ret = [pack0]

        #if a burst has been received (last flit of burst transfer has burst=0)
        #todo: burst can be longer than UDP packet -> pack0 has already data0 and data1
        i = 0
        while (buf[i*self.UDP_NOC_PACKET_LEN] and ((i+1)*self.UDP_NOC_PACKET_LEN)<len(buf)):
            i += 1
            pack = noc_packet()
            pack.burst = buf[i*self.UDP_NOC_PACKET_LEN]
            pack.bsel = buf[1+i*self.UDP_NOC_PACKET_LEN]
            pack.data1 = ((buf[2+i*self.UDP_NOC_PACKET_LEN] << 56) |
                            (buf[3+i*self.UDP_NOC_PACKET_LEN] << 48) |
                            (buf[4+i*self.UDP_NOC_PACKET_LEN] << 40) |
                            (buf[5+i*self.UDP_NOC_PACKET_LEN] << 32) |
                            (buf[6+i*self.UDP_NOC_PACKET_LEN] << 24) |
                            (buf[7+i*self.UDP_NOC_PACKET_LEN] << 16) |
                            (buf[8+i*self.UDP_NOC_PACKET_LEN] << 8) |
                            buf[9+i*self.UDP_NOC_PACKET_LEN])
            pack.data0 = ((buf[10+i*self.UDP_NOC_PACKET_LEN] << 56) |
                            (buf[11+i*self.UDP_NOC_PACKET_LEN] << 48) |
                            (buf[12+i*self.UDP_NOC_PACKET_LEN] << 40) |
                            (buf[13+i*self.UDP_NOC_PACKET_LEN] << 32) |
                            (buf[14+i*self.UDP_NOC_PACKET_LEN] << 24) |
                            (buf[15+i*self.UDP_NOC_PACKET_LEN] << 16) |
                            (buf[16+i*self.UDP_NOC_PACKET_LEN] << 8) |
                            buf[17+i*self.UDP_NOC_PACKET_LEN])
            ret.append(pack)

        return ret

    def send_flush(self):
        last_flit_was_burst = False

        #determine if we can send afterwards
        send_to_socket = True if len(self.sendbuf) else False
        data = bytearray()

        for pack in self.sendbuf:
            now = time.time()
            delta = self.lastsend + (1.0 / self.PACKETFREQ) - now
            if delta > 0.0:
                self.sleepaccu += delta
                if self.sleepaccu > self.MINSLEEP:
                    time.sleep(self.sleepaccu)
                    self.sleepaccu = 0
            self.lastsend = now
            self.sendd += 1

            data += self.packet_pack(pack, last_flit_was_burst)
            last_flit_was_burst = True if pack.burst else False

            if self.noclogging:
                self.flog.write("--> %x:%x:%08x 0x%16x mode:%d\n" % (pack.trg_chipid, pack.trg_modid, pack.addr, pack.data0, pack.mode))

        if send_to_socket:
            self.socks[0].sendto(data, self.send_ipaddr)
            self.sendbuf.clear()



    def testconnection(self):
        pack = noc_packet()
        pack.trg_chipid = 0
        pack.trg_modid = modids.MODID_ETH
        pack.src_chipid = 0
        pack.src_modid = modids.MODID_ETH
        pack.mode = MODE_WRITE_POSTED
        pack.bsel = 0xFF
        pack.burst = 0x0
        pack.addr = 0xFF
        pack.data0 = 0x1234ABCD
        self.send_packet(pack, flush=True)
        pack = self.recv_packet((0, modids.MODID_ETH), 0xFF)
        return True if pack is not None else False

    def tear(self):
        for sock in self.socks:
            sock.close()
        self.flog.flush()
        self.flog.close()

    def get_ip_adr(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            #could be an arbitrary address
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def _reopensocks(self):
        for s in self.socks:
            s.close()
        self.socks = []
        adr = self.get_ip_adr()
        port = self.send_ipaddr[1]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((adr, port))
            self.socks.append(sock)
            print("Socket successfully bound to %s:%d" % (adr, port))
        except socket.error:
            raise FPGA_Error("Cannot open socket on %s:%d - board on?" % (adr, port))

    #reading on the sockets receiving packets and put them to the recvbuf
    def _poll(self):
        rd, wr, x = select.select(self.socks, [], [], 1.0)
        for sock in rd:
            buf = bytearray(self.UDP_PAYLOAD_LEN)
            size, address = sock.recvfrom_into(buf, self.UDP_PAYLOAD_LEN)
            self.recvd += 1
            if not size:
                raise Exception("receive error")
            if len(buf) < 4:
                raise FPGA_Error("received packet smaller than 4")
            packs = self.packet_unpack(buf[0:])
            #print("packs from packet_unpack:")
            #for p in packs:
            #    p.dump()

            self.recvbuf.extend(copy.copy(packs))
            if self.noclogging:
                for pack in packs:
                    self.flog.write("<-- %x:%x:%08x 0x%16x\n" % (pack.src_chipid, pack.src_modid, pack.addr, pack.data0))


class NoCmonitor(threading.Thread):
    regex_udp = r'\s+\d+:\s(\w+):(\w+)(\s+[\w:]+){10}\s(\d+)'
    check_udp_delay = 2.0
    def __init__(self):
        self.dropmap = {}
        super(NoCmonitor, self).__init__()
        self.daemon = True
        self.start()

    def run(self):
        while True:
            self.checkdrops()
            time.sleep(self.check_udp_delay)

    def checkdrops(self):
        fh = open("/proc/net/udp", "r")
        for l in fh:
            m = re.match(self.regex_udp, l)
            if not m:
                continue
            #TODO only check our connection
            madr = "%s:%s" % (m.group(1), m.group(2))
            drops = int(m.group(4))
            if madr not in self.dropmap:
                self.dropmap[madr] = 0
            if drops > self.dropmap[madr]:
                print("WARN: detected a UDP packet drop in /proc/net/udp:%s:%d" % (madr, drops))
                #print l
                self.dropmap[madr] = drops
        fh.close()
