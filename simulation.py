import argparse
import logging

from machine.cache import Cache
from machine.control_unit import ControlUnit
from machine.datapath import DataPath
from machine.isa import read_code
from machine.microprogram import microprogram_memory


def simulation(
    data: list[int],
    code: list[int],
    microprogram: list,
    stack_size: int,
    input_buffer: list[str],
    debug_limit: int,
    limit: int,
    cache_size: int,
    bus_size: int,
    delay: int,
    stack_log: bool = False,
    cache_log: bool = False,
    instr_fetch_log: bool = False,
):
    """
    Prepare datapath and control unit

    Stop at:
    1. Halt -> StopIteration
    2. End of input -> EOFError
    3. Exceed the ticks limit
    """
    data_cache = Cache(delay, cache_size, bus_size, data)
    prog_cache = Cache(delay, cache_size, bus_size, code)

    datapath = DataPath(data_cache, stack_size, input_buffer)
    control_unit = ControlUnit(prog_cache, microprogram, stack_size, datapath)

    logging.debug(repr(control_unit))
    instructions = 0
    try:
        while control_unit.current_tick() < limit:
            if control_unit.microprogram_counter == 0:
                instructions += 1

            control_unit.decode_and_execute()
            if control_unit.current_tick() < debug_limit:
                if instr_fetch_log or control_unit.microprogram_counter not in [0, 1]:
                    logging.debug(control_unit)
                    if stack_log:
                        logging.debug(f"Stack   : {datapath.stack[:5]}")
                        logging.debug(f"Return  : {control_unit.return_stack[:5]}")
                    if cache_log:
                        logging.debug("CU cache: " + repr(control_unit.cache))
                        logging.debug("DP cache: " + repr(control_unit.datapath.cache))
            elif control_unit.current_tick() == debug_limit:
                logging.warning("Debug limit exceeded!")

    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if control_unit.current_tick() >= limit:
        logging.warning("Limit exceeded!")
        pass

    data_cache.clear()

    output = "".join(
        map(lambda x: chr(x) if x < 256 else str(x), datapath.output_buffer)
    )
    logging.info(f"output_buffer: {output}")

    return output, instructions, control_unit.current_tick()


def main(
    code_file: str,
    input_file: str,
    stack_size: int,
    debug_limit: int,
    limit: int,
    cache_size: int,
    bus_size: int,
    delay_ticks: int,
    stack_log: bool,
    cache_log: bool,
    instr_fetch_log: bool,
):
    machine_code = read_code(code_file)
    if input_file is None:
        input_buffer = []
    else:
        with open(input_file, "r") as f:
            input_buffer = list(f.read()) + [chr(0)]

    data_len = machine_code[0]
    data = machine_code[1 : data_len + 1]
    code = machine_code[data_len + 1 :]

    logging.info("Start simulation")
    output, instructions, ticks = simulation(
        data,
        code,
        microprogram_memory,
        stack_size,
        input_buffer,
        debug_limit,
        limit,
        cache_size,
        bus_size,
        delay_ticks,
        stack_log,
        cache_log,
        instr_fetch_log,
    )
    logging.info("End simulation")

    print(output)
    print(f"Instructions: {instructions} Ticks: {ticks}")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)  # DEBUG | INFO

    parser = argparse.ArgumentParser(description="Симуляция процессора")
    parser.add_argument("code_file", help="Имя файла бинарным с кодом")
    parser.add_argument(
        "input_file", nargs="?", help="Имя входного файла (опционально)"
    )
    parser.add_argument(
        "--stack_size", type=int, default=10, help="Размер стека (по умолчанию 10)"
    )
    parser.add_argument(
        "--debug_limit", type=int, default=200, help="Лимит отладки (по умолчанию 200)"
    )
    parser.add_argument(
        "--limit", type=int, default=100000, help="Лимит тиков (по умолчанию 100000)"
    )
    parser.add_argument(
        "--cache_size", type=int, default=8, help="Размер кэша (по умолчанию 8)"
    )
    parser.add_argument(
        "--bus_size", type=int, default=8, help="Размер шины (по умолчанию 8)"
    )
    parser.add_argument(
        "--delay_ticks",
        type=int,
        default=10,
        help="Задержка при обращении в память (по умолчанию 10)",
    )
    parser.add_argument("--stack_log", action="store_true", help="Логирование стека")
    parser.add_argument("--cache_log", action="store_true", help="Логирование кэша")
    parser.add_argument(
        "--inst_fetch_log", action="store_true", help="Логирование запроса инструкции"
    )

    args = parser.parse_args()

    main(
        args.code_file,
        args.input_file,
        args.stack_size,
        args.debug_limit,
        args.limit,
        args.cache_size,
        args.bus_size,
        args.delay_ticks,
        args.stack_log,
        args.cache_log,
        args.inst_fetch_log,
    )
