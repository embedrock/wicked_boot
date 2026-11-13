import pytest
    
@pytest.mark.hil_only
def test_updating_primary_slot(board):
    assert board.wait_for_regex_in_file(r"Image upgrade secondary slot -> primary slot"), \
        "MCUboot не начал обновление из слота 1 в слот 0"
    
    assert board.wait_for_regex_in_file(r"Firmware version:"), \
        "Ожидалось 'Firmware version:' после завершения обновления"