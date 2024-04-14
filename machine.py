import logging
import sys

from control_unit import ControlUnit
from datapath import DataPath
from isa import read_code
from microprogram import microprogram_memory


def simulation(data: list[int], code: list[int], microprogram: list, stack_size: int, input_buffer: list[str], limit: int, full: bool = True):
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
    instructions = 0
    try:
        while control_unit.current_tick() < limit:
            if control_unit.microprogram_counter == 0:
                instructions += 1

            control_unit.decode_and_execute()
            if full or control_unit.microprogram_counter not in [0, 1]:
                logging.debug(control_unit)

    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if control_unit.current_tick() >= limit:
        logging.warning("Limit exceeded!")
        pass

    output = ''.join(map(lambda x: chr(x) if x < 256 else str(x), datapath.output_buffer))
    logging.info(f"output_buffer: {output}")

    return output, instructions, control_unit.current_tick()


def main(code_file: str, input_file: str, full: bool = True):

    STACK_SIZE = 10
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
    output, instructions, ticks = simulation(data, code, microprogram_memory, STACK_SIZE, input_buffer, LIMIT, full)
    logging.info("End simulation")

    print(output)
    print(f"Instructions: {instructions} Ticks: {ticks}")


if __name__ == "__main__":
    assert len(sys.argv) in [2, 3], r"Wrong arguments: .\machine.py <code_file> [<input_file>]"
    logging.getLogger().setLevel(logging.INFO)  # DEBUG for details; INFO for results
    if len(sys.argv) == 2:
        _, code_file = sys.argv
        input_file = None
    else:
        _, code_file, input_file = sys.argv
    main(code_file, input_file, False)
