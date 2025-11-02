// This file mirrors bci/emotiv-rs/src/lib.rs so the crate can live under bci/emotiv/lib
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread::{self, JoinHandle};
use std::time::Duration;

use crossbeam_channel::{Receiver, Sender};
use crossbeam_channel as channel;
use hidapi::HidApi;
use parking_lot::Mutex;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use std::ffi::CString;

use aes::cipher::{BlockDecrypt, KeyInit};
use aes::Aes128;
use hex::FromHex;

const DEFAULT_VID: u16 = 0x1234;
const DEFAULT_PID: u16 = 0xED02;
const DEFAULT_PACKET_SIZE: usize = 32;

// Default AES key (hex): 31003554381037423100354838003750
const AES_KEY_DEFAULT: [u8; 16] = [
    0x31, 0x00, 0x35, 0x54, 0x38, 0x10, 0x37, 0x42, 0x31, 0x00, 0x35, 0x48, 0x38, 0x00, 0x37,
    0x50,
];

const SENSOR_BITS: &[(&str, &[(usize, u8)])] = &[
    ("F3", &[(0, 6), (0, 7), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (2, 0), (2, 1), (2, 2), (2, 3)]),
    ("FC5", &[(2, 4), (2, 5), (2, 6), (2, 7), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (4, 0), (4, 1)]),
    ("AF3", &[(4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7), (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7)]),
    ("F7", &[(6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7), (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5)]),
    ("T7", &[(7, 6), (7, 7), (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (9, 0), (9, 1), (9, 2), (9, 3)]),
    ("P7", &[(9, 4), (9, 5), (9, 6), (9, 7), (10, 0), (10, 1), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (11, 0), (11, 1)]),
    ("O1", &[(11, 2), (11, 3), (11, 4), (11, 5), (11, 6), (11, 7), (12, 0), (12, 1), (12, 2), (12, 3), (12, 4), (12, 5), (12, 6), (12, 7)]),
    ("O2", &[(13, 0), (13, 1), (13, 2), (13, 3), (13, 4), (13, 5), (13, 6), (13, 7), (14, 0), (14, 1), (14, 2), (14, 3), (14, 4), (14, 5)]),
    ("P8", &[(14, 6), (14, 7), (15, 0), (15, 1), (15, 2), (15, 3), (15, 4), (15, 5), (15, 6), (15, 7), (16, 0), (16, 1), (16, 2), (16, 3)]),
    ("T8", &[(16, 4), (16, 5), (16, 6), (16, 7), (17, 0), (17, 1), (17, 2), (17, 3), (17, 4), (17, 5), (17, 6), (17, 7), (18, 0), (18, 1)]),
    ("FC6", &[(18, 2), (18, 3), (18, 4), (18, 5), (18, 6), (18, 7), (19, 0), (19, 1), (19, 2), (19, 3), (19, 4), (19, 5), (19, 6), (19, 7)]),
    ("F4", &[(20, 0), (20, 1), (20, 2), (20, 3), (20, 4), (20, 5), (20, 6), (20, 7), (21, 0), (21, 1), (21, 2), (21, 3), (21, 4), (21, 5)]),
    ("F8", &[(21, 6), (21, 7), (22, 0), (22, 1), (22, 2), (22, 3), (22, 4), (22, 5), (22, 6), (22, 7), (23, 0), (23, 1), (23, 2), (23, 3)]),
    ("AF4", &[(23, 4), (23, 5), (23, 6), (23, 7), (24, 0), (24, 1), (24, 2), (24, 3), (24, 4), (24, 5), (24, 6), (24, 7), (25, 0), (25, 1)]),
];

fn decrypt_packet_with_key_impl(encrypted: &[u8], key_bytes: &[u8; 16]) -> Option<[u8; 32]> {
    if encrypted.len() != 32 { return None; }
    let cipher = Aes128::new(key_bytes.into());
    let mut out = [0u8; 32];
    for i in 0..2 {
        let slice = &encrypted[i * 16..(i + 1) * 16];
        let mut block: [u8; 16] = slice.try_into().ok()?;
        cipher.decrypt_block((&mut block).into());
        out[i * 16..(i + 1) * 16].copy_from_slice(&block);
    }
    Some(out)
}

fn parse_hex_key(hex_str: &str) -> Option<[u8; 16]> {
    if hex_str.len() != 32 { return None; }
    let vec = <[u8; 16]>::from_hex(hex_str).ok()?;
    Some(vec)
}

fn get_level_impl(packet: &[u8], sensor: &str) -> Option<i32> {
    let (_, bits) = SENSOR_BITS.iter().find(|(name, _)| *name == sensor)?;
    let mut level: i32 = 0;
    for (i, (byte_idx, bit_idx)) in bits.iter().enumerate() {
        let bit = (packet.get(*byte_idx)? >> bit_idx) & 1;
        level |= (bit as i32) << i;
    }
    Some(level)
}

/// Extract contact quality for each sensor from the packet
/// Quality is stored in a limited range, with varying encoding by firmware
/// Values: 0=No signal, 1=Very poor, 2=Poor, 3=Fair, 4=Good
fn get_quality_impl(packet: &[u8]) -> Vec<(String, u8)> {
    if packet.len() < 32 { return Vec::new(); }
    
    // Contact quality encoding varies by firmware version
    // Using bytes 26-31 (6 bytes = 12 nibbles) for quality data
    // This gives us quality for 12 sensors; remaining 2 get default value
    let mut qualities = Vec::with_capacity(SENSOR_BITS.len());
    
    // Map sensor index to quality nibble, ensuring we don't go out of bounds
    for (idx, (name, _)) in SENSOR_BITS.iter().enumerate() {
        let byte_offset = 26 + (idx / 2);
        
        // Ensure we don't exceed packet bounds (indices 0-31)
        let quality = if byte_offset < packet.len() {
            if idx % 2 == 0 {
                // Lower nibble
                packet[byte_offset] & 0x0F
            } else {
                // Upper nibble
                (packet[byte_offset] >> 4) & 0x0F
            }
        } else {
            // Default quality for sensors beyond available data
            0
        };
        
        // Clamp to 0-4 range (some versions use 0-15)
        let quality_clamped = quality.min(4);
        qualities.push(((*name).to_string(), quality_clamped));
    }
    
    qualities
}

fn parse_sensor_data_impl(packet: &[u8]) -> Option<(u8, i16, i16, u8, Vec<(String, i32)>, Vec<(String, u8)>)> {
    if packet.len() != 32 { return None; }
    
    let counter = packet[0];
    
    // Battery level is in byte 26 (0-255, higher = better)
    // Convert to percentage (approximate)
    let battery_raw = packet[26] as u16;  // Cast to u16 to avoid overflow
    let battery = if battery_raw > 248 {
        100
    } else if battery_raw < 200 {
        0
    } else {
        (((battery_raw - 200) * 100 / 48).min(100)) as u8
    };
    
    // Gyro X and Y are at bytes 29 and 30
    // These are raw 8-bit values that need to be converted to signed
    // The gyro should give values around 102-106 when still (neutral = ~104)
    // Converting to signed relative to neutral position
    let gyro_x_raw = packet[29] as i16;
    let gyro_y_raw = packet[30] as i16;
    
    // Convert to signed values relative to neutral (104)
    // Range is approximately -104 to +151 after conversion
    let gyro_x = gyro_x_raw - 104;
    let gyro_y = gyro_y_raw - 104;
    
    // Extract EEG sensor levels
    let mut sensors = Vec::with_capacity(SENSOR_BITS.len());
    for (name, _) in SENSOR_BITS.iter() {
        if let Some(level) = get_level_impl(packet, name) {
            sensors.push(((*name).to_string(), level));
        }
    }
    
    // Extract contact quality for each sensor
    let qualities = get_quality_impl(packet);
    
    Some((counter, gyro_x, gyro_y, battery, sensors, qualities))
}

#[derive(Debug)]
struct ReaderState {
    running: Arc<AtomicBool>,
    tx: Option<Sender<Vec<u8>>>,
    rx: Option<Receiver<Vec<u8>>>,
    handle: Option<JoinHandle<()>>,
}

impl ReaderState {
    fn new() -> Self {
        Self {
            running: Arc::new(AtomicBool::new(false)),
            tx: None,
            rx: None,
            handle: None,
        }
    }
}

#[pyclass]
struct EmotivReader {
    vid: u16,
    pid: u16,
    packet_size: usize,
    aes_key: [u8; 16],
    inner: Arc<Mutex<ReaderState>>,
}

#[pymethods]
impl EmotivReader {
    #[new]
    fn new(vid: Option<u16>, pid: Option<u16>, packet_size: Option<usize>, aes_key_hex: Option<&str>) -> Self {
        let aes_key = aes_key_hex
            .and_then(parse_hex_key)
            .unwrap_or(AES_KEY_DEFAULT);
        EmotivReader {
            vid: vid.unwrap_or(DEFAULT_VID),
            pid: pid.unwrap_or(DEFAULT_PID),
            packet_size: packet_size.unwrap_or(DEFAULT_PACKET_SIZE),
            aes_key,
            inner: Arc::new(Mutex::new(ReaderState::new())),
        }
    }

    fn start(&self) -> PyResult<()> {
        let mut guard = self.inner.lock();
        if guard.running.load(Ordering::SeqCst) { return Ok(()); }

        let (tx, rx) = channel::bounded::<Vec<u8>>(self.packet_size * 1024);
        guard.tx = Some(tx.clone());
        guard.rx = Some(rx);

        let running_flag = guard.running.clone();
        running_flag.store(true, Ordering::SeqCst);

        let vid = self.vid;
        let pid = self.pid;
        let packet_size = self.packet_size;

        let handle = thread::spawn(move || {
            let api = match HidApi::new() {
                Ok(api) => api,
                Err(e) => { eprintln!("Failed to initialize hidapi: {e}"); running_flag.store(false, Ordering::SeqCst); return; }
            };

            let mut devices: Vec<_> = api.device_list().filter(|d| d.vendor_id() == vid && d.product_id() == pid).collect();
            devices.sort_by_key(|d| (d.interface_number() != 1, d.interface_number()));

            let device_info = match devices.into_iter().next() { Some(info) => info, None => { eprintln!("No matching Emotiv device found (VID={vid:#06x}, PID={pid:#06x})"); running_flag.store(false, Ordering::SeqCst); return; } };

            let path = match device_info.path().to_str() { Ok(p) => p, Err(_) => { eprintln!("Device path is not valid UTF-8"); running_flag.store(false, Ordering::SeqCst); return; } };

            let c_path = match CString::new(path.as_bytes()) { Ok(c) => c, Err(_) => { eprintln!("Invalid device path"); running_flag.store(false, Ordering::SeqCst); return; } };

            let device = match api.open_path(&c_path) { Ok(dev) => dev, Err(e) => { eprintln!("Failed to open device: {e}"); running_flag.store(false, Ordering::SeqCst); return; } };

            if let Err(e) = device.set_blocking_mode(false) { eprintln!("Failed to set non-blocking mode: {e}"); }

            let sleep_short = Duration::from_millis(5);
            let mut buf = vec![0u8; packet_size];
            while running_flag.load(Ordering::SeqCst) {
                match device.read(&mut buf) {
                    Ok(n) if n > 0 => {
                        let mut packet = Vec::with_capacity(n);
                        packet.extend_from_slice(&buf[..n]);
                        if let Err(_) = tx.send(packet) { break; }
                    }
                    Ok(_) => { thread::sleep(sleep_short); }
                    Err(_) => { thread::sleep(sleep_short); }
                }
            }
            running_flag.store(false, Ordering::SeqCst);
        });

        guard.handle = Some(handle);
        Ok(())
    }

    fn stop(&self) -> PyResult<()> {
        let mut guard = self.inner.lock();
        guard.running.store(false, Ordering::SeqCst);
        guard.tx = None;
        if let Some(handle) = guard.handle.take() { let _ = handle.join(); }
        guard.rx = None;
        Ok(())
    }

    fn is_running(&self) -> bool {
        let guard = self.inner.lock();
        guard.running.load(Ordering::SeqCst)
    }

    fn poll_raw<'py>(&self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyBytes>>> {
        let guard = self.inner.lock();
        if let Some(ref rx) = guard.rx {
            match rx.try_recv() { Ok(bytes) => Ok(Some(PyBytes::new(py, &bytes))), Err(_) => Ok(None) }
        } else { Ok(None) }
    }

    fn poll_decrypted<'py>(&self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyBytes>>> {
        if let Some(raw) = self.poll_raw(py)? {
            let data = raw.as_bytes();
            if let Some(dec) = decrypt_packet_with_key_impl(data, &self.aes_key) {
                return Ok(Some(PyBytes::new(py, &dec)));
            }
        }
        Ok(None)
    }

    fn poll_parsed<'py>(&self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyAny>>> {
        if let Some(dec_bytes) = self.poll_decrypted(py)? {
            let dec = dec_bytes.as_bytes();
            if let Some((counter, gx, gy, battery, sensors, qualities)) = parse_sensor_data_impl(dec) {
                let dict = PyDict::new(py);
                dict.set_item("counter", counter)?;
                dict.set_item("gyro_x", gx)?;
                dict.set_item("gyro_y", gy)?;
                dict.set_item("battery", battery)?;
                
                let sensors_dict = PyDict::new(py);
                for (name, level) in sensors.into_iter() { 
                    sensors_dict.set_item(name, level)?; 
                }
                dict.set_item("sensors", sensors_dict)?;
                
                let quality_dict = PyDict::new(py);
                for (name, quality) in qualities.into_iter() { 
                    quality_dict.set_item(name, quality)?; 
                }
                dict.set_item("quality", quality_dict)?;
                
                return Ok(Some(dict.into_any()));
            }
        }
        Ok(None)
    }
}

#[pyfunction]
fn decrypt_packet<'py>(py: Python<'py>, encrypted: &[u8]) -> PyResult<Option<Bound<'py, PyBytes>>> {
    Ok(decrypt_packet_with_key_impl(encrypted, &AES_KEY_DEFAULT).map(|d| PyBytes::new(py, &d)))
}

#[pyfunction]
fn decrypt_packet_with_key<'py>(py: Python<'py>, encrypted: &[u8], aes_key_hex: &str) -> PyResult<Option<Bound<'py, PyBytes>>> {
    if let Some(key) = parse_hex_key(aes_key_hex) {
        Ok(decrypt_packet_with_key_impl(encrypted, &key).map(|d| PyBytes::new(py, &d)))
    } else { Ok(None) }
}

#[pyfunction]
fn get_level(packet: &[u8], sensor: &str) -> PyResult<Option<i32>> { Ok(get_level_impl(packet, sensor)) }

#[pyfunction]
fn parse_sensor_data<'py>(py: Python<'py>, decrypted: &[u8]) -> PyResult<Option<Bound<'py, PyAny>>> {
    Ok(parse_sensor_data_impl(decrypted).map(|(counter, gx, gy, battery, sensors, qualities)| {
        let dict = PyDict::new(py);
        dict.set_item("counter", counter).unwrap();
        dict.set_item("gyro_x", gx).unwrap();
        dict.set_item("gyro_y", gy).unwrap();
        dict.set_item("battery", battery).unwrap();
        
        let sensors_dict = PyDict::new(py);
        for (name, level) in sensors.into_iter() { 
            sensors_dict.set_item(name, level).unwrap(); 
        }
        dict.set_item("sensors", sensors_dict).unwrap();
        
        let quality_dict = PyDict::new(py);
        for (name, quality) in qualities.into_iter() { 
            quality_dict.set_item(name, quality).unwrap(); 
        }
        dict.set_item("quality", quality_dict).unwrap();
        
        dict.into_any()
    }))
}

#[pymodule]
fn emotiv_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<EmotivReader>()?;
    m.add("DEFAULT_VID", DEFAULT_VID)?;
    m.add("DEFAULT_PID", DEFAULT_PID)?;
    m.add("DEFAULT_PACKET_SIZE", DEFAULT_PACKET_SIZE)?;
    m.add_function(wrap_pyfunction!(decrypt_packet, m)?)?;
    m.add_function(wrap_pyfunction!(get_level, m)?)?;
    m.add_function(wrap_pyfunction!(parse_sensor_data, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_packet_with_key, m)?)?;
    Ok(())
}


