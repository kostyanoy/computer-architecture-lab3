import contextlib
import io
import logging
import os
import tempfile

import pytest

import machine
import translator
from isa import read_code

# TODO main algorithm
# TODO check mnemonics
# TODO Ci gitlab
# TODO check harv
# TODO адресация портов ??
@pytest.mark.golden_test("golden/*.yml")
def test_translator_and_machine(golden, caplog):
    """
    Test: poetry poetry run pytest . -v
    Update tests: poetry run pytest . -v --update-goldens
    """
    caplog.set_level(logging.DEBUG)

    # Создаём временную папку для тестирования приложения.
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Готовим имена файлов для входных и выходных данных.
        source = os.path.join(tmpdirname, "source.txt")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target.out")

        # Записываем входные данные в файлы. Данные берутся из теста.
        with open(source, "w") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w") as file:
            file.write(golden["in_stdin"])

        # Запускаем транслятор и собираем весь стандартный вывод в переменную
        # stdout
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target)
            print("============================================================")
            machine.main(target, input_stream)

        # Выходные данные также считываем в переменные.
        code = read_code(target)

        # Проверяем, что ожидания соответствуют реальности.
        assert code == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert caplog.text == golden.out["out_log"]