# tests/conftest.py
import pytest
import subprocess
import time
import sys
import os
import serial
import shutil
import re
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts")))
from flasher import flash_jlink, erase_jlink, flash_app_slot, reboot_jlink

def pytest_addoption(parser):
    parser.addoption("--target", action="store", default="qemu", choices=["qemu", "hil"], help="Target platform: qemu or hil (real hardware)")
    parser.addoption("--fw-image", type=str, action="store", default="build/qemu-f4/wicked_boot.elf", help="firmware binary to program to device")
    parser.addoption("--port", type=str, action="store", default="/dev/ttyUSB0", help="UART port")

@pytest.fixture(scope="session")
def target(request):
    return request.config.getoption("--target")

@pytest.fixture(scope="session")
def port(request):
    return request.config.getoption("--port")

@pytest.fixture(scope="session")
def fw_image(request):
    return request.config.getoption("--fw-image")

class QemuBoard:
    def __init__(self, fw_image):
        self.fw_image = fw_image
        self.serial_file = "build/qemu_serial.txt"
        self.start_qemu()
    
    def start_qemu(self):
        self.process = subprocess.Popen([
            "qemu-system-arm",
            "-M", "netduinoplus2",
            "-nographic",
            "-serial", f"file:{self.serial_file}",
            #"-gdb", "tcp::1234",
            "-kernel", self.fw_image
        ])
        time.sleep(1)
    
    def wait_for_regex_in_file(self, regex, timeout_s=5):
        """Analog of wait_for_regex_in_line, but read from QEMU log"""
        start_time = time.time()
        with open(self.serial_file, "r") as f:
            while time.time() - start_time < timeout_s:
                f.seek(0) # В реальном коде лучше использовать f.tell() чтобы не читать всё с начала
                content = f.read()
                match = re.search(regex, content)
                if match:
                    return match
                time.sleep(0.1)
        return None
    
    def teardown(self):
        if self.process:
            self.process.terminate()
            self.process.wait()

class STM32Board:
    def __init__(self, port, baud, fw_image, erase_first=True):
        self.port = port
        self.baud = baud
        self.fw_image = fw_image
        
        self.serial_device = serial.Serial(port, baud, timeout=1, write_timeout=1)
        self.serial_device.reset_input_buffer()
        
        if erase_first:
            erase_jlink(device="STM32F407VG", speed=4000)
        flash_jlink(fw_image, device="STM32F407VG", speed=4000)
        
    def flash_slot(self, slot: int, fw_image: str):
        """flashing slot during test"""
        self.serial_device.reset_input_buffer()
        dummy = self.serial_device.read_until().decode('utf-8', errors='replace')
        flash_app_slot(slot=slot, fw_image=fw_image, device="STM32F407VG", speed=4000)
    
    def flash_slot_no_reset(self, slot: int, fw_image: str):
        """flashing slot during test withot reboot"""
        self.serial_device.reset_input_buffer()
        dummy = self.serial_device.read_until().decode('utf-8', errors='replace')
        flash_app_slot(slot=slot, fw_image=fw_image, device="STM32F407VG", speed=4000, reset_after=False)
    
    def reboot(self, wait_s=1.0):
        """reboot mcu via J-Link and clean UART buffer"""
        self.serial_device.reset_input_buffer()
        dummy = self.serial_device.read_until().decode('utf-8', errors='replace')
        reboot_jlink(device="STM32F407VG", speed=4000)
        time.sleep(wait_s)
        return True
    
    def wait_for_regex_in_file(self, regex, timeout_s=15):
        """Waiting for regex timeout_s seconds"""
        start_time = time.time()
        
        while True:
            line = self.serial_device.read_until().decode('utf-8', errors='replace').replace("\r\n", "")
            
            if line != "" and line != '\n' and line != '\r':
                print(f"          {line}")
            
            if re.search(regex, line):
                return True
            
            if time.time() - start_time > timeout_s:
                raise RuntimeError(f"Timeout ({timeout_s}s) waiting for regex: {regex}")
        
    def capture_uart_output(self, duration_s=20):
        """Dump all uart data"""
        start_time = time.time()
        output = ""
        original_timeout = self.serial_device.timeout
        self.serial_device.timeout = 0.5 
        
        try:
            while time.time() - start_time < duration_s:
                # read_until() uses self.serial_device.timeout automaticly
                line = self.serial_device.read_until().decode('utf-8', errors='replace').replace("\r\n", "")
                if line != "" and line != '\n' and line != '\r':
                    print(f"          {line}")
                    output += line
        finally:
            self.serial_device.timeout = original_timeout
            
        return output
    
    def send_byte(self, byte_data):
        """Отправляет один байт в UART"""
        if isinstance(byte_data, str):
            byte_data = byte_data.encode('utf-8')
        self.serial_device.write(byte_data)
        time.sleep(1.05)
    
    def send_command(self, command: str, wait_for_response_s=2):
        """Send command (strint) to UART and return responce from device. Add \r in begin and end"""
        print(f"➡️ Sending command: '{command}'")
        
#        self.serial_device.reset_input_buffer()
#        line = self.serial_device.read_until().decode('utf-8', errors='replace')
        
        self.serial_device.write(("\r").encode('utf-8'))
        time.sleep(0.5)
        #self.serial_device.write((command).encode('utf-8'))
        for char in command:
            self.serial_device.write(char.encode('utf-8'))
            time.sleep(0.5)
        
        time.sleep(0.5)
        self.serial_device.reset_input_buffer()
        dummy = self.serial_device.read_until().decode('utf-8', errors='replace')
        self.serial_device.write(("\r").encode('utf-8'))
        
        response = self.capture_uart_output(duration_s=wait_for_response_s)
        
        print(f"✅ Command '{command}' sent, response captured.")
        return response

@pytest.fixture(scope="function")
def board(target, port, fw_image, request):
    test_markers = [marker.name for marker in request.node.iter_markers()]
    
    if "hil_only" in test_markers and target != "hil":
        pytest.skip(f"Test {request.node.name} requires HIL target")
    if "qemu_only" in test_markers and target != "qemu":
        pytest.skip(f"Test {request.node.name} requires QEMU target")
    
    if target == "qemu":
        test_board = QemuBoard(fw_image)
        yield test_board
        test_board.teardown()
    elif target == "hil":
        test_board = STM32Board(port, 115200, fw_image)
        yield test_board
        test_board.serial_device.close()
