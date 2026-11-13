import pytest
import os

@pytest.mark.hil_only
def test_load_image_in_primary_slot(board):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    app_v1_path = os.path.join(repo_root, "samples", "app_signed_uart_v1.bin")
    app_v2_path = os.path.join(repo_root, "samples", "app_signed_uart_v2.bin")
    
    print("\nFlashing Slot 0 (No reset)...")
    board.flash_slot_no_reset(slot=0, fw_image=app_v1_path)
    print("\nFlashing Slot 1 (No reset)...")
    board.flash_slot_no_reset(slot=1, fw_image=app_v2_path)
    
    board.reboot(wait_s=3.0)
    
    uart_log = board.capture_uart_output(duration_s=20)
    
    assert "Bootloader Version:" in uart_log, "Ожидалось 'Bootloader Version:' после запуска"
    assert "Firmware version: 0.1.0" in uart_log, "Ожидалось 'Firmware version: 0.1.0'"

