import pytest
import os

@pytest.mark.hil_only
def test_updating_primary_slot(board):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    app_v2_path = os.path.join(repo_root, "samples", "app_signed_uart_v2.bin")
    
    board.flash_slot(slot=1, fw_image=app_v2_path)
    
    # 1. Считываем 20 секунд вывода
    uart_log = board.capture_uart_output(duration_s=20)
    
    # 2. МАГИЯ: Создаем "плоскую" версию лога, удаляя ВСЕ \r и \n.
    # Это гарантирует, что разорванные посередине строки UART склеятся обратно.
    clean_log = uart_log.replace("\r", "").replace("\n", "")
    
    # 3. Проверяем наличие строк в очищенном логе
    assert "Image upgrade secondary slot -> primary slot" in clean_log, \
        "MCUboot не начал обновление из слота 1 в слот 0"
    
    assert "Firmware version:" in clean_log, \
        "Ожидалось 'Firmware version:' после завершения обновления"
    
    # 4. Проверяем строгий порядок следования строк (тоже в clean_log)
    pos_upgrade = clean_log.find("Image upgrade secondary slot -> primary slot")
    pos_version = clean_log.find("Firmware version:")
    
    assert pos_upgrade != -1 and pos_version != -1 and (pos_upgrade < pos_version), \
        "Строки найдены, но в неправильном порядке! Сначала upgrade, потом version."
    
# @pytest.mark.hil_only
# def test_updating_primary_slot(board):
#     assert board.wait_for_regex_in_file(r"Image upgrade secondary slot -> primary slot"), \
#         "MCUboot не начал обновление из слота 1 в слот 0"
    
#     assert board.wait_for_regex_in_file(r"Firmware version:"), \
#         "Ожидалось 'Firmware version:' после завершения обновления"