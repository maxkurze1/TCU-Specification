use log::{debug, error};
use num_enum::{IntoPrimitive, TryFromPrimitive};
use socket2::{self, Domain, Protocol, SockAddr, Socket};
use std::cmp;
use std::convert::TryFrom;
use std::fmt;
use std::net::{IpAddr, SocketAddr};
use std::time::Duration;

const ETH_MOD: FPGAModule = FPGAModule::new(0, 0x05);

const NOC_PACKET_LEN: usize = 18;
const UDP_PAYLOAD_LEN: usize = 1472;

const BYTES_PER_BURST_PACKET: usize = 16;
const BYTES_PER_PACKET: usize = 8;

const MAX_READ_BURST_LEN: usize = 32 * BYTES_PER_BURST_PACKET;
const MAX_WRITE_BURST_LEN: usize = 2047 * BYTES_PER_BURST_PACKET;

const READ_TIMEOUT: Duration = Duration::from_secs(1);
const MAX_READ_RETRIES: usize = 3;

#[repr(u8)]
#[derive(Debug, Eq, PartialEq, IntoPrimitive, TryFromPrimitive)]
enum Mode {
    ReadReq     = 0,
    ReadResp    = 1,
    WritePosted = 2,
}

#[derive(Copy, Clone, Eq, PartialEq)]
pub struct FPGAModule {
    pub chip_id: u8,
    pub mod_id: u8,
}

impl FPGAModule {
    pub const fn new(chip_id: u8, mod_id: u8) -> Self {
        Self { chip_id, mod_id }
    }
}

impl fmt::Display for FPGAModule {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "(chip={}, mod={})", self.chip_id, self.mod_id)
    }
}

pub struct Communicator {
    addr: SockAddr,
    sock: Socket,
    send_buf: Vec<u8>,
    burst: Option<(u8, bool)>,
}

enum NocPacket<'b> {
    Normal((FPGAModule, Mode, u32, &'b [u8])),
    Burst(&'b [u8]),
}

impl Communicator {
    pub fn new(fpga_ip: &str, fpga_port: u16) -> std::io::Result<Self> {
        let sock = Socket::new(
            Domain::ipv4(),
            socket2::Type::dgram(),
            Some(Protocol::udp()),
        )?;
        let addr = "0.0.0.0:".to_string() + &fpga_port.to_string();
        sock.bind(&addr.parse::<SocketAddr>().unwrap().into())?;

        sock.set_read_timeout(Some(READ_TIMEOUT))?;

        Ok(Self {
            addr: SockAddr::from(SocketAddr::new(
                IpAddr::V4(fpga_ip.parse().unwrap()),
                fpga_port,
            )),
            sock,
            send_buf: Vec::with_capacity(UDP_PAYLOAD_LEN),
            burst: None,
        })
    }

    pub fn self_test(&mut self) -> std::io::Result<()> {
        let test_data = [0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xFF];
        self.write_noburst(ETH_MOD, 0, &test_data)?;

        let mut buf = vec![0u8; UDP_PAYLOAD_LEN];
        let (size, _) = self.sock.recv_from(&mut buf)?;
        assert!(size >= NOC_PACKET_LEN);

        let noc_packet = self.decode_packet(&buf);
        match noc_packet {
            NocPacket::Normal((src, mode, off, data)) => {
                assert!(mode == Mode::WritePosted);
                assert!(off == 0);
                assert!(self.burst.is_none());
                assert!(src == ETH_MOD);
                assert!(data.iter().rev().eq(test_data.iter()));
            },
            _ => assert!(false),
        }

        Ok(())
    }

    pub fn read(
        &mut self,
        target: FPGAModule,
        mut addr: u32,
        mut len: usize,
    ) -> std::io::Result<Vec<u8>> {
        let mut buf = vec![0u8; UDP_PAYLOAD_LEN];
        let mut res = Vec::with_capacity(len);

        let mut retries = 0;
        while len > 0 {
            let res = self.read_single(&mut buf, &mut res, target, addr, len);
            match res {
                Err(e) => {
                    error!("read request failed: {}", e);
                    // try a few times if it failed for a different reason
                    retries += 1;
                    if retries >= MAX_READ_RETRIES {
                        return Err(e);
                    }
                },
                Ok(amount) => {
                    addr += amount as u32;
                    len -= amount;
                },
            }
        }

        Ok(res)
    }

    fn read_single(
        &mut self,
        buf: &mut Vec<u8>,
        res: &mut Vec<u8>,
        target: FPGAModule,
        addr: u32,
        len: usize,
    ) -> std::io::Result<usize> {
        let byte_count = cmp::min(MAX_READ_BURST_LEN, len);
        let byte_count_bytes = ((byte_count as u64) << 32).to_le_bytes();
        let noc_packet = encode_packet(target, false, 0xFF, addr, &byte_count_bytes, Mode::ReadReq);
        self.append_packet(&noc_packet)?;
        self.flush_packets()?;

        let (size, _) = self.sock.recv_from(buf)?;

        let org_len = res.len();
        let mut pos = 0;
        while pos + NOC_PACKET_LEN <= size {
            let noc_packet = self.decode_packet(&buf[pos..]);
            match noc_packet {
                NocPacket::Normal((src, mode, off, data)) => {
                    // TODO if the mode is not ReadResp, keep it for later
                    assert!(mode == Mode::ReadResp);

                    if self.burst.is_some() {
                        debug!("Received burst-start from {} at offset {:#x}", src, off);
                    }
                    else {
                        debug!(
                            "Received packet from {} at offset {:#x}: {:02x?}",
                            src, off, data
                        );
                        res.extend(data.iter().rev());
                    }
                },
                NocPacket::Burst(data) => {
                    res.extend(data.iter().rev());
                },
            }
            pos += NOC_PACKET_LEN;
        }

        assert!(pos == size);
        assert!(res.len() - org_len <= len);

        Ok(res.len() - org_len)
    }

    pub fn write_noburst(
        &mut self,
        target: FPGAModule,
        mut addr: u32,
        data: &[u8],
    ) -> std::io::Result<usize> {
        let build_min_packet = |data: &[u8], pos: usize| {
            let mut buf = data[pos..].to_vec();
            // pad remaining data with zeros to reach BYTES_PER_PACKET bytes
            while buf.len() % BYTES_PER_PACKET != 0 {
                buf.push(0);
            }
            buf
        };

        let mut pos = 0;

        // align it first
        let rem = addr as usize % BYTES_PER_PACKET;
        if rem != 0 {
            let buf = build_min_packet(data, pos);
            let noc_pkt = encode_packet(target, false, 0xFF >> rem, addr, &buf, Mode::WritePosted);
            self.append_packet(&noc_pkt)?;

            let amount = BYTES_PER_PACKET - rem;
            addr += amount as u32;
            pos += amount;
        }

        // write full and aligned packets
        while pos + BYTES_PER_PACKET <= data.len() {
            let noc_pkt = encode_packet(target, false, 0xFF, addr, &data[pos..], Mode::WritePosted);
            self.append_packet(&noc_pkt)?;

            addr += BYTES_PER_PACKET as u32;
            pos += BYTES_PER_PACKET;
        }

        // write trailing packet
        if pos < data.len() {
            let buf = build_min_packet(data, pos);
            let rem = data.len() - pos;
            let noc_pkt = encode_packet(
                target,
                false,
                0xFF >> (0x7 - rem),
                addr,
                &buf,
                Mode::WritePosted,
            );
            self.append_packet(&noc_pkt)?;

            pos = data.len();
        }

        self.flush_packets().map(|_| pos)
    }

    pub fn write_burst(
        &mut self,
        target: FPGAModule,
        mut addr: u32,
        data: &[u8],
    ) -> std::io::Result<usize> {
        let mut pos = 0;
        let mut burst_pos = MAX_WRITE_BURST_LEN;
        while pos + BYTES_PER_BURST_PACKET <= data.len() {
            assert!(addr % 16 == 0); // TODO support other alignments
            if burst_pos >= MAX_WRITE_BURST_LEN {
                // write initial NoC packet that defines the burst length
                let byte_count = cmp::min(MAX_WRITE_BURST_LEN, data.len() - pos);
                let word_count = (byte_count / BYTES_PER_BURST_PACKET) as u64;
                let word_count_bytes = word_count.to_le_bytes();
                let noc_packet = encode_packet(
                    target,
                    true,
                    0xFF,
                    addr,
                    &word_count_bytes,
                    Mode::WritePosted,
                );
                self.append_packet(&noc_packet)?;
                addr += word_count as u32 * BYTES_PER_BURST_PACKET as u32;
                burst_pos = 0;
            }

            let not_last = burst_pos + (BYTES_PER_BURST_PACKET * 2) <= MAX_WRITE_BURST_LEN
                && (pos + BYTES_PER_BURST_PACKET * 2) <= data.len();
            let noc_packet = encode_packet_burst(not_last, &data[pos..]);
            self.append_packet(&noc_packet)?;

            pos += BYTES_PER_BURST_PACKET;
            burst_pos += BYTES_PER_BURST_PACKET;
        }

        // sent the remaining data without burst, if there is any
        self.write_noburst(target, addr, &data[pos..])
    }

    fn append_packet(&mut self, packet: &[u8]) -> std::io::Result<()> {
        if self.send_buf.len() + packet.len() > self.send_buf.capacity() {
            self.flush_packets()?;
        }

        debug!("-> NoC packet: {:02x?}", &packet);
        self.send_buf.extend_from_slice(&packet);
        Ok(())
    }

    fn flush_packets(&mut self) -> std::io::Result<()> {
        if !self.send_buf.is_empty() {
            self.sock.send_to(&self.send_buf, &self.addr)?;
            self.send_buf.clear();
        }
        Ok(())
    }

    fn decode_packet<'b>(&mut self, bytes: &'b [u8]) -> NocPacket<'b> {
        debug!("<- NoC packet: {:02x?}", &bytes[0..18]);
        if let Some((bsel, ref mut first)) = self.burst {
            let begin = if bytes[0] == 0 {
                (0xF - (bsel >> 4)) as usize
            }
            else {
                0
            };
            let end = if *first {
                (0xF - (bsel & 0xF)) as usize
            }
            else {
                0
            };

            *first = false;
            if bytes[0] == 0 {
                self.burst = None;
            }

            NocPacket::Burst(&bytes[2 + begin..18 - end])
        }
        else {
            let src = FPGAModule::new(bytes[3] >> 2, bytes[2]);
            let addr = (bytes[6] as u32) << 24
                | (bytes[7] as u32) << 16
                | (bytes[8] as u32) << 8
                | bytes[9] as u32;
            if bytes[0] == 1 {
                self.burst = Some((bytes[1], true));
            }
            let mode = Mode::try_from(bytes[5] & 0xF).unwrap();
            let data = if bytes[1] == 0xFF {
                &bytes[10..18]
            }
            else {
                let first = bytes[1].leading_zeros() as usize;
                let last = bytes[1].trailing_zeros() as usize;
                &bytes[10 + first..18 - last]
            };
            NocPacket::Normal((src, mode, addr, data))
        }
    }
}

fn encode_packet(
    target: FPGAModule,
    burst: bool,
    bsel: u8,
    addr: u32,
    bytes: &[u8],
    mode: Mode,
) -> [u8; 18] {
    let mode_byte: u8 = mode.into();
    [
        // burst and bsel
        burst as u8,
        bsel,
        // source and target
        ETH_MOD.mod_id,
        (ETH_MOD.chip_id << 2) | target.mod_id >> 6,
        (target.mod_id << 2) | (target.chip_id >> 6),
        (target.chip_id << 4) | mode_byte,
        // target address
        (addr >> 24) as u8,
        (addr >> 16) as u8,
        (addr >> 8) as u8,
        (addr >> 0) as u8,
        // data
        bytes[7],
        bytes[6],
        bytes[5],
        bytes[4],
        bytes[3],
        bytes[2],
        bytes[1],
        bytes[0],
    ]
}

fn encode_packet_burst(not_last: bool, bytes: &[u8]) -> [u8; 18] {
    [
        // burst and bsel
        not_last as u8,
        0xFF,
        // data
        bytes[15],
        bytes[14],
        bytes[13],
        bytes[12],
        bytes[11],
        bytes[10],
        bytes[9],
        bytes[8],
        bytes[7],
        bytes[6],
        bytes[5],
        bytes[4],
        bytes[3],
        bytes[2],
        bytes[1],
        bytes[0],
    ]
}
