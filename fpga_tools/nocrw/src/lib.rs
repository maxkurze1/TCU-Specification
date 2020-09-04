mod com;

use com::{Communicator, FPGAModule};
use cpython::{py_fn, py_module_initializer, PyBytes, PyResult, Python};
use lazy_static::lazy_static;
use log::info;
use simplelog::{CombinedLogger, Config, LevelFilter, TermLogger, TerminalMode, WriteLogger};
use std::env;
use std::fs::{create_dir, File};
use std::str::FromStr;
use std::sync::Mutex;

py_module_initializer!(nocrw, |py, m| {
    m.add(
        py,
        "connect",
        py_fn!(py, connect(fpga_ip: &str, fpga_port: u16)),
    )?;

    m.add(
        py,
        "read_bytes",
        py_fn!(py, read_bytes(chip_id: u8, mod_id: u8, addr: u32, len: u32)),
    )?;

    m.add(
        py,
        "write_bytes",
        py_fn!(
            py,
            write_bytes(chip_id: u8, mod_id: u8, addr: u32, b: &PyBytes, burst: bool)
        ),
    )?;
    Ok(())
});

lazy_static! {
    static ref COM: Mutex<Option<Communicator>> = Mutex::new(None);
}

fn log_level(env_var: &str, def: LevelFilter) -> LevelFilter {
    match env::var(env_var) {
        Ok(log) => LevelFilter::from_str(&log).unwrap(),
        Err(_) => def,
    }
}

fn connect(_py: Python, fpga_ip: &str, fpga_port: u16) -> PyResult<u64> {
    assert!(COM.lock().unwrap().is_none());

    // ensure that the log directory exists
    create_dir("log").ok();

    // log to stderr and to file, controlled via env variables RUST_LOG and RUST_FILE_LOG
    let term_level = log_level("RUST_LOG", LevelFilter::Warn);
    let file_level = log_level("RUST_FILE_LOG", LevelFilter::Info);
    CombinedLogger::init(vec![
        TermLogger::new(term_level, Config::default(), TerminalMode::Stderr).unwrap(),
        WriteLogger::new(
            file_level,
            Config::default(),
            File::create("log/ethernet.log").unwrap(),
        ),
    ])
    .unwrap();

    info!("connect(fpga_ip={}, fpga_port={})", fpga_ip, fpga_port,);

    let mut com = Communicator::new(fpga_ip, fpga_port).unwrap();
    com.self_test().unwrap();
    *COM.lock().unwrap() = Some(com);

    Ok(0)
}

fn read_bytes(py: Python, chip_id: u8, mod_id: u8, addr: u32, len: u32) -> PyResult<PyBytes> {
    info!(
        "read_bytes(chip_id={}, mod_id={}, addr={:#x}, len={})",
        chip_id, mod_id, addr, len
    );

    let mut guard = COM.lock().unwrap();
    let com = guard.as_mut().unwrap();
    let bytes = com
        .read(FPGAModule::new(chip_id, mod_id), addr, len as usize)
        .unwrap();
    Ok(PyBytes::new(py, &bytes))
}

fn write_bytes(
    py: Python,
    chip_id: u8,
    mod_id: u8,
    addr: u32,
    b: &PyBytes,
    burst: bool,
) -> PyResult<u64> {
    info!(
        "write_bytes(chip_id={}, mod_id={}, addr={:#x}, len={}, burst={})",
        chip_id,
        mod_id,
        addr,
        b.data(py).len(),
        burst,
    );

    let mut guard = COM.lock().unwrap();
    let com = guard.as_mut().unwrap();
    if burst {
        com.write_burst(FPGAModule::new(chip_id, mod_id), addr, b.data(py))
            .unwrap();
    }
    else {
        com.write_noburst(FPGAModule::new(chip_id, mod_id), addr, b.data(py))
            .unwrap();
    }

    Ok(0)
}
