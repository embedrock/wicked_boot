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
from flasher import flash_jlink, erase_jlink, flash_app_slot

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
    def __init__(self, port, baud, fw_image, erase_first=True):
        self.port = port
        self.baud = baud
        self.fw_image = fw_image
        
        self.serial_device = serial.Serial(port, baud, timeout=1, write_timeout=1)
        self.serial_device.reset_input_buffer()
        
        if erase_first:
            print("🧹 Erasing chip before flashing...")
            erase_jlink(device="STM32F407VG", speed=4000)
        flash_jlink(fw_image, device="STM32F407VG", speed=4000)

        print("✅ Flashing successful!\n")
        
        print("flashing slot2!\n")
        flash_app_slot(slot=1, fw_image="samples/app_signed_uart_v2.bin", device="STM32F407VG")
        print("✅ Flashing slot2 successful!\n")

    def wait_for_regex_in_file(self, regex, timeout_s=15, drain_time_s=14):
        """
        Читает UART, ищет regex. После нахождения продолжает читать и печатать
        вывод в течение drain_time_s секунд. Использует буфер, чтобы строки,
        прочитанные во время drain, были доступны для последующих вызовов.
        """
        start_time = time.time()
        found_time = None
        buffer = ""  # Накопительный буфер всего вывода
        
        while True:
            line = self.serial_device.read_until().decode('utf-8', errors='replace').replace("\r\n", "")
            
            if line != "":
                print(f"   [UART] {line}")
                buffer += line + "\n"  # Добавляем в буфер
            
            # 1. Если еще не нашли, проверяем на совпадение
            if found_time is None and re.search(regex, buffer):
                found_time = time.time()
                print(f"   [UART] ✅ MATCH FOUND: '{regex}'. Continuing to drain UART for {drain_time_s}s...")
            
            # 2. Если уже нашли, проверяем, прошло ли достаточно времени для "долива"
            if found_time is not None:
                if time.time() - found_time >= drain_time_s:
                    print("   [UART] ✅ Drain complete. Test passed successfully.")
                    return True
            
            # 3. Если не нашли и вышло общее время ожидания — падаем с ошибкой
            if found_time is None and (time.time() - start_time > timeout_s):
                raise RuntimeError(f"Timeout ({timeout_s}s) waiting for regex: {regex}")

@pytest.fixture(scope="function")
def board(target, port, fw_image, request):
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
