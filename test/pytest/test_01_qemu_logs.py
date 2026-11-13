import pytest

@pytest.mark.qemu_only
def test_formatting_successful(board):
    match = board.wait_for_regex_in_file(r"Wait or enter any symbol to go CLI")
    assert match is not None, "Ожидалось 'Wait or enter any symbol to go CLI' в выводе"

#def test_mounted_successful(board):
#    match = board.wait_for_regex_in_file(r"Swap type: none")
#    assert match is not None, "Сообщение Swap type: none не найдено"






