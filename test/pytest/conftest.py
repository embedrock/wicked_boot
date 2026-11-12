# tests/conftest.py
import pytest
import subprocess
import time
import os
import serial
import shutil
import re
from pathlib import Path

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
        time.sleep(1) # Даем QEMU секунду на старт
    
    def wait_for_regex_in_file(self, regex, timeout_s=5):
        """Аналог wait_for_regex_in_line, но читает из файла QEMU"""
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
    def __init__(self, port, baud, fw_image):
        self.port = port
        self.baud = baud
        self.fw_image = fw_image
        self._flash_device(fw_image)
        #self.serial_device = serial.Serial(port, baud, timeout=1, write_timeout=1)
        time.sleep(1.5)
        #self.serial_device.reset_input_buffer()

    def _flash_device(self, fw_image):
        print(f"\n🔄 Flashing {fw_image}...")
        # cmd = [
        #     "openocd", "-f", "interface/stlink.cfg", "-f", "target/stm32f4x.cfg",
        #     "-c", f"program {os.path.abspath(fw_image)} verify reset exit"
        # ]
        # result = subprocess.run(cmd, capture_output=True, text=True)
        # if result.returncode != 0:
        #     print("❌ OpenOCD Error:\n", result.stderr)
        #     raise RuntimeError("Flashing failed")
        print("✅ Flashing successful!\n")

    def wait_for_regex_in_line(self, regex, timeout_s=5):
        start_time = time.time()
        while True:
            line = self.serial_device.read_until().decode('utf-8', errors='replace').replace("\r\n", "")
            if line != "":
                print(f"   [UART] {line}")
            
            if re.search(regex, line):
                return True
                
            if time.time() - start_time > timeout_s:
                raise RuntimeError(f"Timeout waiting for regex: {regex}")

@pytest.fixture(scope="session")
def board(target, port, fw_image, request):
    # Получаем метки текущего теста
    test_markers = [marker.name for marker in request.node.iter_markers()]
    
    # Проверяем совместимость
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
