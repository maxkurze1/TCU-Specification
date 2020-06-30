
import serial
import time
import struct

import modids


TIMER_COUNT = 100

#addr, data, r/w (0/2)
config_eth_init = [
    [0x500, 0x00000053, 2], #set MDIO clock
    [0x404, 0x9000FFFF, 2], #reset MAC receiver
    [0x408, 0x90000000, 2], #reset MAC transmitter
    #[0x708, 0x00000000, 2], #disable frame filter
    [0x708, 0x80000000, 2], #disable frame filter
    [0x700, 0x28030405, 2], #set MAC address (lower part)
    [0x704, 0x00000800, 2], #set MAC address (upper part)
    [0x504, 0x00000080, 0]  #check if MDIO ready (read bit 7)
]

#int PHY (addr 0x1): enable AN
config_eth_intPHY_enAN = [
    [0x508, 0x00001040, 2],
    [0x504, 0x01004800, 2], #start MDIO transfer
    [0x504, 0x00000080, 0]  #check if MDIO ready (read bit 7)
]

#ext PHY: strap PHY to mode 3 or 4
config_eth_extPHY_strapPHY = [
    [0x508, 0x0000001F, 2], #prepare to write addr
    [0x504, 0x030D4800, 2], #ext reg space (addr 0xD)
    [0x504, 0x00000080, 0],
    [0x508, 0x00000031, 2], #set reg addr
    [0x504, 0x030E4800, 2], #ext reg space (addr 0xE)
    [0x504, 0x00000080, 0],
    [0x508, 0x0000401F, 2], #prepare to write data
    [0x504, 0x030D4800, 2],
    [0x504, 0x00000080, 0],
    [0x508, 0x00001170, 2], #set reg data
    [0x504, 0x030E4800, 2],
    [0x504, 0x00000080, 0]
]

#ext PHY (addr 0x3): enable SGMII clock
config_eth_extPHY_enSGMIIclock = [
    [0x508, 0x0000001F, 2], #prepare to write addr
    [0x504, 0x030D4800, 2], #ext reg space (addr 0xD)
    [0x504, 0x00000080, 0],
    [0x508, 0x000000D3, 2], #set reg addr
    [0x504, 0x030E4800, 2], #ext reg space (addr 0xE)
    [0x504, 0x00000080, 0],
    [0x508, 0x0000401F, 2], #prepare to write data
    [0x504, 0x030D4800, 2],
    [0x504, 0x00000080, 0],
    [0x508, 0x00004000, 2], #set reg data
    [0x504, 0x030E4800, 2],
    [0x504, 0x00000080, 0]
]

#ext PHY: enable AN
config_eth_extPHY_enAN = [
    [0x508, 0x00001140, 2],
    [0x504, 0x03004800, 2],
    [0x504, 0x00000080, 0]
]

#ext PHY: CFG2 reg
config_eth_extPHY_cfg2 = [
    [0x508, 0x0000001F, 2], #prepare to write addr
    [0x504, 0x030D4800, 2], #ext reg space (addr 0xD)
    [0x504, 0x00000080, 0],
    [0x508, 0x00000014, 2], #set reg addr
    [0x504, 0x030E4800, 2], #ext reg space (addr 0xE)
    [0x504, 0x00000080, 0],
    [0x508, 0x0000401F, 2], #prepare to write data
    [0x504, 0x030D4800, 2],
    [0x504, 0x00000080, 0],
    [0x508, 0x000029C7, 2], #set reg data
    [0x504, 0x030E4800, 2],
    [0x504, 0x00000080, 0]
]

#ext PHY: disable RGMII
config_eth_extPHY_disRGMII = [
    [0x508, 0x0000001F, 2], #prepare to write addr
    [0x504, 0x030D4800, 2], #ext reg space (addr 0xD)
    [0x504, 0x00000080, 0],
    [0x508, 0x00000032, 2], #set reg addr
    [0x504, 0x030E4800, 2], #ext reg space (addr 0xE)
    [0x504, 0x00000080, 0],
    [0x508, 0x0000401F, 2], #prepare to write data
    [0x504, 0x030D4800, 2],
    [0x504, 0x00000080, 0],
    [0x508, 0x00000000, 2], #set reg data
    [0x504, 0x030E4800, 2],
    [0x504, 0x00000080, 0]
]


class uart_noc_packet(object):
    UART_LOGFILE = "log/uart.log"
    def __init__(self, logtofile=0):
        self.data = 0           #64
        self.addr = 0           #32
        self.mode = 0           # 4
        self.trg_chipid = 0     # 6
        self.trg_modid = 0      # 8
        self.src_chipid = 0     # 6
        self.src_modid = 0      # 8
        self.bsel = 0           # 8

        self.uart_logtofile = logtofile
        if (self.uart_logtofile):
            self.uart_log = open(self.UART_LOGFILE, "w")

    def dump(self, pack_info=""):
        if (self.uart_logtofile):
            self.uart_log.write("noc_packet: %s\n" % pack_info)
            self.uart_log.write("  data: 0x%x\n" % self.data)
            self.uart_log.write("  addr: 0x%x\n" % self.addr)
            self.uart_log.write("  mode: 0x%x\n" % self.mode)
            self.uart_log.write("  trg_chipid: 0x%x\n" % self.trg_chipid)
            self.uart_log.write("  trg_modid: 0x%x\n" % self.trg_modid)
            self.uart_log.write("  src_chipid: 0x%x\n" % self.src_chipid)
            self.uart_log.write("  src_modid: 0x%x\n\n" % self.src_modid)
            self.uart_log.write("  bsel: 0x%x\n\n" % self.bsel)
            self.uart_log.flush()
        else:
            print("noc_packet: %s" % pack_info)
            print("  data: 0x%x" % self.data)
            print("  addr: 0x%x" % self.addr)
            print("  mode: 0x%x" % self.mode)
            print("  trg_chipid: 0x%x" % self.trg_chipid)
            print("  trg_modid: 0x%x" % self.trg_modid)
            print("  src_chipid: 0x%x" % self.src_chipid)
            print("  src_modid: 0x%x\n" % self.src_modid)
            print("  bsel: 0x%x\n\n" % self.bsel)


    def prepare(self, modid, adr, data, mode=0x2, bsel=0xFF):
        self.data = data
        self.addr = adr
        self.mode = mode
        self.trg_chipid = 0
        self.trg_modid = modid
        self.src_chipid = 0
        self.src_modid = modids.MODID_UART
        self.bsel = bsel

        buf = bytearray(17)
        buf[0]  = self.bsel
        buf[1]  = self.src_modid
        buf[2]  = (self.src_chipid << 2) | (self.trg_modid >> 6)
        buf[3]  = (self.trg_modid << 2) | (self.trg_chipid >> 4)
        buf[4]  = (self.trg_chipid << 4) | self.mode
        buf[5]  = (self.addr & 0xFF000000) >> 24
        buf[6]  = (self.addr & 0x00FF0000) >> 16
        buf[7]  = (self.addr & 0x0000FF00) >> 8
        buf[8]  = (self.addr & 0x000000FF)
        buf[9]  = (self.data & 0xFF00000000000000) >> 56
        buf[10] = (self.data & 0x00FF000000000000) >> 48
        buf[11] = (self.data & 0x0000FF0000000000) >> 40
        buf[12] = (self.data & 0x000000FF00000000) >> 32
        buf[13] = (self.data & 0x00000000FF000000) >> 24
        buf[14] = (self.data & 0x0000000000FF0000) >> 16
        buf[15] = (self.data & 0x000000000000FF00) >> 8
        buf[16] = (self.data & 0x00000000000000FF)
        return buf

    def unpack(self, buf):
        self.bsel = buf[0]
        self.src_modid = buf[1]
        self.src_chipid = buf[2] >> 2
        self.trg_modid = (buf[2] & 0x3) | (buf[3] >> 2)
        self.trg_chipid = (buf[3] & 0x3) | (buf[4] >> 4)
        self.mode = buf[4] & 0xF
        self.addr = (buf[5] << 24) | (buf[6] << 16) | (buf[7] << 8) | buf[8]
        self.data = (buf[9] << 56) | (buf[10] << 48) | (buf[11] << 40) | (buf[12] << 32) | (buf[13] << 24) | (buf[14] << 16) | (buf[15] << 8) | buf[16]


class UART(uart_noc_packet):
    def __init__(self, port):
        self.ser = serial.Serial(
            port=port,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
            timeout = 1.0
        )
        if self.ser.isOpen():
            if not self.test_uart():
                print("UART connected, but test failed!\n")
            #else:
            #    print("UART successfully connected!\n")
        else:
            print("UART connection failed!\n")

        """
        print("Configure Ethernet ... ")
        if not self.config_eth():
            print("Configure Ethernet: FAILED!\n")
        else:
            print("Configure Ethernet: Done!\n")
        """

        time.sleep(1)

    def close(self):
        if self.ser.isOpen():
            self.ser.close()
        #self.uart_log.close()

    def send(self, data):
        #print("sending: ", data)
        self.ser.write(data)

    def recv(self, len=1):
        return self.ser.read(len)

    def test_uart(self):
        sendpack = uart_noc_packet()
        recvpack = uart_noc_packet()

        test_data = sendpack.prepare(modids.MODID_UART, 0x123, 0x0A0B)
        #sendpack.dump("send")
        self.send(test_data)

        recv_data = self.recv(17)
        if recv_data:
            recvpack.unpack(recv_data)
            #recvpack.dump("recv")
        else:
            return False

        time.sleep(0.5)
        if (recvpack.data == 0x0A0B and recvpack.addr == 0x123):
            return True
        else:
            return False


    def set_config(self, config_list):
        sendpack = uart_noc_packet()
        recvpack = uart_noc_packet()
        config_done = 0

        for (addr, val, mode) in config_list:
            timeout_cnt = 0

            #write
            if (mode == 2):
                send_data = sendpack.prepare(modids.MODID_ETH, 0xFF000000+addr, val)
                sendpack.dump("send")
                self.send(send_data)

            #read
            elif (mode == 0):
                send_data = sendpack.prepare(modids.MODID_ETH, 0xFF000000+addr, val, 0)
                sendpack.dump("send")

                recv_ready = 0
                while (recv_ready != 1 and timeout_cnt < TIMER_COUNT):
                    self.send(send_data)
                    time.sleep(0.1)
                    recv_data = self.recv(17)
                    recvpack.unpack(recv_data)
                    timeout_cnt += 1

                    #check
                    if (recvpack.data & val):
                        recv_ready = 1
                        recvpack.dump("recv")

                    if (timeout_cnt >= TIMER_COUNT and recv_ready != 1):
                        recvpack.dump("recv")
                        print("Time out!")

                    time.sleep(0.1)


            if (timeout_cnt >= TIMER_COUNT):
                print("Cancel set-up!")
                config_done = 1
                break
            else:
                config_done = 0

            time.sleep(0.1)

        return config_done


    def config_eth(self):
        config_done = [0] * 20
        config_done_iter = 0

        print("config_eth: init ... ", end='')
        config_done[config_done_iter] = self.set_config(config_eth_init)
        if (config_done[config_done_iter]):
            print("FAILED!")
        else:
            print("Done!")
        config_done_iter += 1
        #input("Press Enter to continue ...")


        print("config_eth: int. PHY - enable AN ... ", end='')
        config_done[config_done_iter] = self.set_config(config_eth_intPHY_enAN)
        if (config_done[config_done_iter] != 0):
            print("FAILED!")
        else:
            print("Done!")
        config_done_iter += 1
        #input("Press Enter to continue ...")


        print("config_eth: ext. PHY - strap to mode 3 or 4 ... ", end='')
        config_done[config_done_iter] = self.set_config(config_eth_extPHY_strapPHY)
        if (config_done[config_done_iter] != 0):
            print("FAILED!")
        else:
            print("Done!")
        config_done_iter += 1
        #input("Press Enter to continue ...")



        print("config_eth: ext. PHY - enable SGMII clock ... ", end='')
        config_done[config_done_iter] = self.set_config(config_eth_extPHY_enSGMIIclock)
        if (config_done[config_done_iter] != 0):
            print("FAILED!")
        else:
            print("Done!")
        config_done_iter += 1
        #input("Press Enter to continue ...")


        print("config_eth: ext. PHY - enable AN ... ", end='')
        config_done[config_done_iter] = self.set_config(config_eth_extPHY_enAN)
        if (config_done[config_done_iter] != 0):
            print("FAILED!")
        else:
            print("Done!")
        config_done_iter += 1
        #input("Press Enter to continue ...")



        print("config_eth: ext. PHY - set cfg2 reg ... ", end='')
        config_done[config_done_iter] = self.set_config(config_eth_extPHY_cfg2)
        if (config_done[config_done_iter] != 0):
            print("FAILED!")
        else:
            print("Done!")
        config_done_iter += 1
        #input("Press Enter to continue ...")


        print("config_eth: ext. PHY - disable RGMII ... ", end='')
        config_done[config_done_iter] = self.set_config(config_eth_extPHY_disRGMII)
        if (config_done[config_done_iter] != 0):
            print("FAILED!")
        else:
            print("Done!")
        config_done_iter += 1
        #input("Press Enter to continue ...")


        #final check
        for i in range(0, config_done_iter):
            if (config_done[i]):
                return False

        return True



