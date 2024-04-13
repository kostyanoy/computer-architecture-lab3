import logging
import sys

from control_unit import ControlUnit
from datapath import DataPath
from isa import read_code
from microprogram import microprogram_memory


def simulation(data: list[int], code: list[int], microprogram: list, stack_size: int, input_buffer: list[str], limit: int):
    """
    Prepare datapath and control unit

    Stop at:
    1. Halt -> StopIteration
    2. End of input -> EOFError
    3. Exceed the ticks limit
    """
    datapath = DataPath(data, stack_size, input_buffer)
    control_unit = ControlUnit(code, microprogram, stack_size, datapath)

    logging.debug(repr(control_unit))
    try:
        while control_unit.current_tick() < limit:
            control_unit.decode_and_execute()
            logging.debug(control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if control_unit.current_tick() >= limit:
        logging.warning("Limit exceeded!")
        pass

    output = "".join(map(chr, datapath.output_buffer))
    logging.info(f"output_buffer: {output}")

    return output, control_unit.current_tick()


def main(code_file: str, input_file: str):

    STACK_SIZE = 128
    LIMIT = 1000

    machine_code = read_code(code_file)
    if input_file is None:
        input_buffer = []
    else:
        with open(input_file, "r") as f:
            input_buffer = list(f.read()) + [chr(0)]

    data_len = machine_code[0]
    data = machine_code[1: data_len + 1]
    code = machine_code[data_len + 1:]

    logging.info("Start simulation")
    output, ticks = simulation(data, code, microprogram_memory, STACK_SIZE, input_buffer, LIMIT)
    logging.info("End simulation")

    print(output)
    print(f"Ticks: {ticks}")


if __name__ == "__main__":
    assert len(sys.argv) in [2, 3], r"Wrong arguments: .\machine.py <code_file> [<input_file>]"
    logging.getLogger().setLevel(logging.INFO)
    if len(sys.argv) == 2:
        _, code_file = sys.argv
        input_file = None
    else:
        _, code_file, input_file = sys.argv
    main(code_file, input_file)
