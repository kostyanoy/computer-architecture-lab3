import logging

from isa import MAX_UNSIGN
from microprogram import MUX, ALU


class DataPath:
    data_memory_size: int = None
    data_memory: list[int] = None
    data_address: int = None
    stack_size: int = None
    stack: list[int] = None
    stack_pointer: int = None
    stack_buffer: int = None
    input_buffer: list[str] = None
    output_buffer: list[int] = None

    mux_stack_value: MUX = None
    mux_alu_left: MUX = None
    mux_alu_right: MUX = None
    mux_stack_pointer: MUX = None
    mux_stack_data: MUX = None

    we: int = None
    oe: int = None
    immediate_value: int = None
    input_value: str = None
    alu_operation: ALU = None

    def __init__(self, data_memory: list[int], stack_size: int, input_buffer: list[str]):
        assert stack_size > 0, "Stack size must be > 0"
        self.data_memory_size = len(data_memory)
        self.data_memory = data_memory
        self.data_address = 0
        self.stack_size = stack_size
        self.stack = [-1] * stack_size
        self.stack_pointer = -1
        self.stack_buffer = 0
        self.input_buffer = input_buffer
        self.output_buffer = []

    # get MUX values
    def get_mux_stack_value(self):
        if self.mux_stack_value == MUX.STACK_VALUE_DATA:
            assert self.oe, "No output enable signal"
            return self.data_memory[self.data_address]
        elif self.mux_stack_value == MUX.STACK_VALUE_IMMEDIATE:
            return self.immediate_value
        elif self.mux_stack_value == MUX.STACK_VALUE_INPUT:
            return ord(self.input_value)
        elif self.mux_stack_value == MUX.STACK_VALUE_ALU:
            return self.get_alu_result()
        elif self.mux_stack_value == MUX.STACK_VALUE_SB:
            return self.stack_buffer
        else:
            raise ValueError(f"Wrong mux_stack_value value: {self.mux_stack_value}")

    def get_mux_alu_left(self):
        if self.mux_alu_left == MUX.ALU_LEFT_STACK:
            return self.get_mux_stack_data()
        elif self.mux_alu_left == MUX.ALU_LEFT_ZERO:
            return 0
        else:
            raise ValueError(f"Wrong mux_alu_left value: {self.mux_alu_left}")

    def get_mux_alu_right(self):
        if self.mux_alu_right == MUX.ALU_RIGHT_STACK:
            return self.stack[self.stack_pointer - 1]
        elif self.mux_alu_right == MUX.ALU_RIGHT_INC:
            return 1
        elif self.mux_alu_right == MUX.ALU_RIGHT_ZERO:
            return 0
        elif self.mux_alu_right == MUX.ALU_RIGHT_DEC:
            return -1
        else:
            raise ValueError(f"Wrong mux_alu_right value: {self.mux_alu_right}")

    def get_mux_stack_pointer(self):
        if self.mux_stack_pointer == MUX.SP_DEC:
            return self.stack_pointer - 1
        elif self.mux_stack_pointer == MUX.SP_INC:
            return self.stack_pointer + 1
        elif self.mux_stack_pointer == MUX.SP_DDEC:
            return self.stack_pointer - 2
        else:
            raise ValueError(f"Wrong mux_stack_pointer value: {self.mux_stack_pointer}")

    def get_mux_stack_data(self):
        if self.mux_stack_data == MUX.DATA_TOS:
            return self.stack[self.stack_pointer]
        elif self.mux_stack_data == MUX.DATA_SOS:
            return self.stack[self.stack_pointer - 1]
        else:
            raise ValueError(f"Wrong mux_stack_data value: {self.mux_stack_data}")

    def get_alu_result(self):
        left = self.get_mux_alu_left()
        right = self.get_mux_alu_right()

        # operation
        if self.alu_operation == ALU.ADD:
            res = right + left
        elif self.alu_operation == ALU.SUB:
            res = right - left
        elif self.alu_operation == ALU.MUL:
            res = right * left
        elif self.alu_operation == ALU.DIV:
            res = right // left
        elif self.alu_operation == ALU.MOD:
            res = right % left
        else:
            raise ValueError(f"Wrong alu_operation value: {self.alu_operation}")

        # binary overflow
        if res < 0:
            res = (MAX_UNSIGN + 1) - res
        if res > MAX_UNSIGN:
            res %= (MAX_UNSIGN + 1)
        return res

    # MUX signals
    def signal_alu_operation(self, sel: ALU):
        self.alu_operation = sel

    def signal_mux_stack_value(self, sel: MUX):
        self.mux_stack_value = sel

    def signal_mux_alu_left(self, sel: MUX):
        self.mux_alu_left = sel

    def signal_mux_alu_right(self, sel: MUX):
        self.mux_alu_right = sel

    def signal_mux_stack_pointer(self, sel: MUX):
        self.mux_stack_pointer = sel

    def signal_mux_stack_data(self, sel: MUX):
        self.mux_stack_data = sel

    # latch signals
    def signal_latch_data_address(self):
        self.data_address = self.get_mux_stack_data()

    def signal_latch_stack_buffer(self):
        self.stack_buffer = self.get_mux_stack_data()

    def signal_latch_stack_pointer(self):
        self.stack_pointer = self.get_mux_stack_pointer()
        assert -1 <= self.stack_pointer < self.stack_size, f"Out of stack: {self.stack_pointer}"

    def signal_latch_tos(self):
        self.stack[self.stack_pointer] = self.get_mux_stack_value()

    def signal_latch_sos(self):
        self.stack[self.stack_pointer - 1] = self.get_mux_stack_value()

    # other signals
    def signal_we(self):
        assert 0 <= self.data_address < self.data_memory_size, f"Out of memory: {self.data_address}"
        self.we = True
        self.oe = False
        self.data_memory[self.data_address] = self.get_mux_stack_data()

    def signal_oe(self):
        self.oe = True
        self.we = False

    def signal_input(self):
        if len(self.input_buffer) == 0:
            raise EOFError("End of input file")
        symbol = self.input_buffer.pop(0)
        self.input_value = symbol
        if ord(symbol) == 0:
            symbol = ""
        logging.debug(f"input: {symbol}")

    def signal_output(self):
        symbol = self.get_mux_stack_data()
        self.output_buffer.append(symbol)
        logging.debug(f"output: {''.join(map(lambda x: chr(x) if x < 256 else str(x), self.output_buffer))} << {symbol}")

    def zero(self):
        return self.stack[self.stack_pointer] == 0
