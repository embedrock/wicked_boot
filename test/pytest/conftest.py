# tests/conftest.py
import pytest
import subprocess
import time
import os
import shutil
import re
from pathlib import Path

def pytest_addoption(parser):
    parser.addoption("--fw-image", type=str, action="store", default="build/qemu-f4/wicked_boot.elf", help="firmware binary to program to device")
    parser.addoption("--port", type=str, action="store", default="/dev/ttyUSB0", help="UART port")

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
            "-gdb", "tcp::1234",
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

@pytest.fixture(scope="session")
def board(fw_image):
    my_board = QemuBoard(fw_image)
    yield my_board
    my_board.teardown()
