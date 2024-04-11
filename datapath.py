from control_unit import ControlUnit
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

    we = None
    oe = None
    alu_operation: ALU = None

    control_unit: ControlUnit = None

    def __init__(self, data_memory_size: int, stack_size: int, input_buffer: list[str]):
        assert data_memory_size > 0, "Data memory size must be > 0"
        assert stack_size > 0, "Stack size must be > 0"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.data_address = 0
        self.stack_size = stack_size
        self.stack = [0] * stack_size
        self.stack_pointer = 0
        self.stack_buffer = 0
        self.we = 0
        self.oe = 0
        self.input_buffer = input_buffer
        self.output_buffer = []

    def get_alu_result(self):
        # left
        if self.mux_alu_left == MUX.ALU_LEFT_STACK:
            if self.mux_stack_data == MUX.VALUE_TOS:
                left = self.stack[self.stack_pointer]
            elif self.mux_stack_data == MUX.VALUE_SOS:
                left = self.stack[self.stack_pointer - 1]
            else:
                raise ValueError(f"Wrong mux_stack_data value: {self.mux_stack_data}")
        elif self.mux_alu_left == MUX.ALU_LEFT_ZERO:
            left = 0
        else:
            raise ValueError(f"Wrong mux_alu_left value: {self.mux_alu_left}")

        # right
        if self.mux_alu_left == MUX.ALU_RIGHT_STACK:
            right = self.stack[self.stack_pointer - 1]
        elif self.mux_alu_left == MUX.ALU_RIGHT_INC:
            right = 1
        elif self.mux_alu_left == MUX.ALU_RIGHT_ZERO:
            right = 0
        elif self.mux_alu_left == MUX.ALU_RIGHT_DEC:
            right = -1
        else:
            raise ValueError(f"Wrong mux_alu_right value: {self.mux_alu_right}")

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

    def signal_alu_operation(self, sel):
        self.alu_operation = sel

    def signal_mux_stack_value(self, sel):
        self.mux_stack_value = sel

    def signal_mux_alu_left(self, sel):
        self.mux_alu_left = sel

    def signal_mux_alu_right(self, sel):
        self.mux_alu_right = sel

    def signal_mux_stack_pointer(self, sel):
        self.mux_stack_pointer = sel

    def signal_mux_stack_data(self, sel):
        self.mux_stack_data = sel

    def signal_latch_data_address(self):
        if self.mux_stack_data == MUX.VALUE_TOS:
            self.data_address = self.stack[self.stack_pointer]
        elif self.mux_stack_data == MUX.VALUE_SOS:
            self.data_address = self.stack[self.stack_pointer - 1]
        else:
            raise ValueError(f"Wrong mux_stack_data value: {self.mux_stack_data}")

    def signal_latch_stack_buffer(self):
        if self.mux_stack_data == MUX.VALUE_TOS:
            self.data_address = self.stack[self.stack_pointer]
        elif self.mux_stack_data == MUX.VALUE_SOS:
            self.data_address = self.stack[self.stack_pointer - 1]
        else:
            raise ValueError(f"Wrong mux_stack_data value: {self.mux_stack_data}")

    def signal_latch_stack_pointer(self):
        if self.mux_stack_pointer == MUX.SP_DEC:
            self.stack_pointer -= 1
        elif self.mux_stack_pointer == MUX.SP_INC:
            self.stack_pointer += 1
        elif self.mux_stack_pointer == MUX.SP_DDEC:
            self.stack_pointer -= 2
        else:
            raise ValueError(f"Wrong mux_stack_pointer value: {self.mux_stack_pointer}")

        assert 0 <= self.stack_pointer < self.stack_size, f"Out of stack: {self.stack_pointer}"

    def signal_latch_tos(self):
        if self.mux_stack_value == MUX.STACK_VALUE_DATA:
            assert self.oe, "No output enable signal"
            self.stack[self.stack_pointer] = self.data_memory[self.data_address]
        elif self.mux_stack_value == MUX.STACK_VALUE_IMMEDIATE:
            self.stack[self.stack_pointer] = self.control_unit.program_memory[self.control_unit.program_counter]
        elif self.mux_stack_value == MUX.STACK_VALUE_INPUT:
            # TODO log input
            self.stack[self.stack_pointer] = ord(self.input_buffer.pop(0))
        elif self.mux_stack_value == MUX.STACK_VALUE_ALU:
            self.stack[self.stack_pointer] = self.get_alu_result()
        elif self.mux_stack_value == MUX.STACK_VALUE_SB:
            self.stack[self.stack_pointer] = self.stack_buffer
        else:
            raise ValueError(f"Wrong mux_stack_value value: {self.mux_stack_value}")

    def signal_latch_sos(self):
        if self.mux_stack_value == MUX.STACK_VALUE_DATA:
            assert self.oe, "No output enable signal"
            self.stack[self.stack_pointer] = self.data_memory[self.data_address]
        elif self.mux_stack_value == MUX.STACK_VALUE_IMMEDIATE:
            self.stack[self.stack_pointer] = self.control_unit.program_memory[self.control_unit.program_counter]
        elif self.mux_stack_value == MUX.STACK_VALUE_INPUT:
            # TODO log input
            self.stack[self.stack_pointer] = ord(self.input_buffer.pop(0))
        elif self.mux_stack_value == MUX.STACK_VALUE_ALU:
            self.stack[self.stack_pointer] = self.get_alu_result()
        elif self.mux_stack_value == MUX.STACK_VALUE_SB:
            self.stack[self.stack_pointer] = self.stack_buffer
        else:
            raise ValueError(f"Wrong mux_stack_value value: {self.mux_stack_value}")

    def signal_we(self):
        self.we = True
        self.oe = False

        assert 0 <= self.data_address < self.data_memory_size, f"Out of memory: {self.data_address}"

        if self.mux_stack_data == MUX.VALUE_TOS:
            self.data_memory[self.data_address] = self.stack[self.stack_pointer]
        elif self.mux_stack_data == MUX.VALUE_SOS:
            self.data_memory[self.data_address] = self.stack[self.stack_pointer - 1]
        else:
            raise ValueError(f"Wrong mux_stack_data value: {self.mux_stack_data}")

    def signal_oe(self):
        self.oe = True
        self.we = False

    def signal_output(self):
        if self.mux_stack_data == MUX.VALUE_TOS:
            self.output_buffer.append(self.stack[self.stack_pointer])
        elif self.mux_stack_data == MUX.VALUE_SOS:
            self.output_buffer.append(self.stack[self.stack_pointer - 1])
        else:
            raise ValueError(f"Wrong mux_stack_data value: {self.mux_stack_data}")
        # TODO log output

    def zero(self):
        return self.stack[self.stack_pointer] == 0
