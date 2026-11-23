import pytest
import os
import time

@pytest.mark.hil_only
def test_load_image_in_primary_slot(board):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    app_v1_path = os.path.join(repo_root, "samples", "app_signed_uart_v1.bin")
    app_v2_path = os.path.join(repo_root, "samples", "app_signed_uart_v2.bin")
    
    board.send_byte('a')
    cli_response = board.capture_uart_output(duration_s=2)
    assert "bl>" in cli_response
    
    print("\nFlashing Slot 0 (No reset)...")
    board.flash_slot_no_reset(slot=0, fw_image=app_v1_path)
    print("\nFlashing Slot 1 (No reset)...")
    board.flash_slot_no_reset(slot=1, fw_image=app_v2_path)    
    board.reboot(wait_s=5.0)

    match = board.wait_for_regex_in_file(r"Firmware version: 0.1.0")
    assert match is not None, "Ожидалось 'Firmware version: 0.1.0'"

@pytest.mark.hil_only
def test_swap_images(board):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    app_v1_path = os.path.join(repo_root, "samples", "app_signed_uart_v1.bin")
    app_v2_path = os.path.join(repo_root, "samples", "app_signed_uart_v2.bin")
    
    
    print("\nFlashing Slot 0 (No reset)...")
    board.flash_slot_no_reset(slot=0, fw_image=app_v1_path)
    print("\nFlashing Slot 1 (No reset)...")
    board.flash_slot_no_reset(slot=1, fw_image=app_v2_path)
    time.sleep(0.05)
    
    response = board.send_command("swap_images", wait_for_response_s=0.05)
    
    print("\nChecking uart after reboot (20 seconds)...")
    match = board.wait_for_regex_in_file(r"Firmware version: 0.2.0", timeout_s=20)
    assert match is not None, "Ожидалось 'Firmware version: 0.2.0'"
