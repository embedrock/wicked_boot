import pytest
import os

@pytest.mark.hil_only
def test_load_image_in_primary_slot(board):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    app_v1_path = os.path.join(repo_root, "samples", "app_signed_uart_v1.bin")
    
    board.flash_slot(slot=0, fw_image=app_v1_path)
    
    uart_log = board.capture_uart_output(duration_s=20)
    
    assert "Bootloader Version:" in uart_log, "Ожидалось 'Bootloader Version:' после запуска"
    assert "Firmware version:" in uart_log, "Ожидалось 'Firmware version:' после завершения обновления"

@pytest.mark.hil_only
def test_updating_primary_slot(board):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    app_v2_path = os.path.join(repo_root, "samples", "app_signed_uart_v2.bin")
    
    board.flash_slot(slot=1, fw_image=app_v2_path)
    
    uart_log = board.capture_uart_output(duration_s=20)
    
    assert "Image upgrade secondary slot -> primary slot" in uart_log, "MCUboot не начал обновление из слота 1 в слот 0"
    assert "Firmware version:" in uart_log, "Ожидалось 'Firmware version:' после завершения обновления"
    
    pos_upgrade = uart_log.find("Image upgrade secondary slot -> primary slot")
    pos_version = uart_log.find("Firmware version:")
    
    assert pos_upgrade != -1 and pos_version != -1 and (pos_upgrade < pos_version), \
        "Строки найдены, но в неправильном порядке! Сначала upgrade, потом version."
