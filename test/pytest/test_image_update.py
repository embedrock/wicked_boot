import pytest

@pytest.mark.hil_only
def test_updating_primary_slot(board):
    # 1. Считываем 20 секунд вывода (этого более чем достаточно для загрузки MCUboot)
    uart_log = board.capture_uart_output(duration_s=20)
    
    # 2. Проверяем, что нужные строки есть в этом логе
    assert "Image upgrade secondary slot -> primary slot" in uart_log, \
        "MCUboot не начал обновление из слота 1 в слот 0"
    
    assert "Firmware version:" in uart_log, \
        "Ожидалось 'Firmware version:' после завершения обновления"
    
    # 3. (Бонус) Проверяем строгий порядок следования строк
    pos_upgrade = uart_log.find("Image upgrade secondary slot -> primary slot")
    pos_version = uart_log.find("Firmware version:")
    
    assert pos_upgrade < pos_version, \
        "Строки найдены, но в неправильном порядке! Сначала upgrade, потом version."
    
# @pytest.mark.hil_only
# def test_updating_primary_slot(board):
#     assert board.wait_for_regex_in_file(r"Image upgrade secondary slot -> primary slot"), \
#         "MCUboot не начал обновление из слота 1 в слот 0"
    
#     assert board.wait_for_regex_in_file(r"Firmware version:"), \
#         "Ожидалось 'Firmware version:' после завершения обновления"