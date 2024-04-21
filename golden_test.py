import contextlib
import io
import logging
import os
import tempfile

import pytest

import simulation
import translator
from machine.isa import read_code


def main_test(
    golden,
    caplog,
    STACK_SIZE=10,
    DEBUG_LIMIT=200,
    LIMIT=100000,
    CACHE_SIZE=8,
    BUS_SIZE=8,
    DELAY_TICKS=1,
    STACK_LOG=False,
    CACHE_LOG=False,
    INST_FETCH_LOG=False,
):
    """
    Test: poetry run pytest . -v
    Update tests: poetry run pytest . -v --update-goldens
    """
    caplog.set_level(logging.DEBUG)

    # Создаём временную папку для тестирования приложения.
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Готовим имена файлов для входных и выходных данных.
        source = os.path.join(tmpdirname, "source.txt")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target.out")
        target_mnem = os.path.join(tmpdirname, "target.out.mnem")

        # Записываем входные данные в файлы. Данные берутся из теста.
        with open(source, "w") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w") as file:
            file.write(golden["in_stdin"])

        # Запускаем транслятор и собираем весь стандартный вывод в переменную
        # stdout
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target, target_mnem)
            print("============================================================")
            simulation.main(
                target,
                input_stream,
                STACK_SIZE,
                DEBUG_LIMIT,
                LIMIT,
                CACHE_SIZE,
                BUS_SIZE,
                DELAY_TICKS,
                STACK_LOG,
                CACHE_LOG,
                INST_FETCH_LOG,
            )

        # Выходные данные также считываем в переменные.
        code = read_code(target)
        with open(target_mnem, "r") as f:
            mnemonics = f.read()

        # Проверяем, что ожидания соответствуют реальности.
        assert mnemonics == golden.out["out_mnemonics"]
        assert code == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert caplog.text == golden.out["out_log"]


@pytest.mark.golden_test("golden/*_alg.yml")
def test_translator_and_machine(golden, caplog):
    STACK_SIZE = 10
    DEBUG_LIMIT = 200
    LIMIT = 100000
    CACHE_SIZE = 8
    BUS_SIZE = 8
    DELAY_TICKS = 1
    STACK_LOG = False
    CACHE_LOG = False
    INST_FETCH_LOG = False

    main_test(
        golden,
        caplog,
        STACK_SIZE,
        DEBUG_LIMIT,
        LIMIT,
        CACHE_SIZE,
        BUS_SIZE,
        DELAY_TICKS,
        STACK_LOG,
        CACHE_LOG,
        INST_FETCH_LOG,
    )


@pytest.mark.golden_test("golden/*_cache_demonstr.yml")
def test_cache_demonstr(golden, caplog):
    STACK_SIZE = 10
    DEBUG_LIMIT = 200
    LIMIT = 100000
    CACHE_SIZE = 8
    BUS_SIZE = 8
    DELAY_TICKS = 10
    STACK_LOG = False
    CACHE_LOG = True
    INST_FETCH_LOG = False

    main_test(
        golden,
        caplog,
        STACK_SIZE,
        DEBUG_LIMIT,
        LIMIT,
        CACHE_SIZE,
        BUS_SIZE,
        DELAY_TICKS,
        STACK_LOG,
        CACHE_LOG,
        INST_FETCH_LOG,
    )


@pytest.mark.golden_test("golden/*_small_cache.yml")
def test_small_cache(golden, caplog):
    STACK_SIZE = 10
    DEBUG_LIMIT = 200
    LIMIT = 100000
    CACHE_SIZE = 2
    BUS_SIZE = 2
    DELAY_TICKS = 10
    STACK_LOG = False
    CACHE_LOG = True
    INST_FETCH_LOG = False

    main_test(
        golden,
        caplog,
        STACK_SIZE,
        DEBUG_LIMIT,
        LIMIT,
        CACHE_SIZE,
        BUS_SIZE,
        DELAY_TICKS,
        STACK_LOG,
        CACHE_LOG,
        INST_FETCH_LOG,
    )


@pytest.mark.golden_test("golden/*_small_bus.yml")
def test_small_bus(golden, caplog):
    STACK_SIZE = 10
    DEBUG_LIMIT = 200
    LIMIT = 100000
    CACHE_SIZE = 8
    BUS_SIZE = 1
    DELAY_TICKS = 10
    STACK_LOG = False
    CACHE_LOG = True
    INST_FETCH_LOG = False

    main_test(
        golden,
        caplog,
        STACK_SIZE,
        DEBUG_LIMIT,
        LIMIT,
        CACHE_SIZE,
        BUS_SIZE,
        DELAY_TICKS,
        STACK_LOG,
        CACHE_LOG,
        INST_FETCH_LOG,
    )
