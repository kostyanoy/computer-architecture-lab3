import microprogram
from datapath import DataPath
from microprogram import ALU, MUX, Latch, DataMemory, IO, Halt


class ControlUnit:
    program_memory: list[int] = None
    program_counter: int = None
    return_stack_size: int = None
    return_stack: list[int] = None
    return_stack_pointer: int = None
    instruction_register: int = None
    microprogram_memory: list = None
    microprogram_counter: int = None

    instruction_decoder: int = None

    mux_type_pc: MUX = None
    mux_pc: MUX = None
    mux_mpc: MUX = None
    mux_rsp: MUX = None

    datapath: DataPath = None

    _tick: int = None
    latch: list = None  # latching when comes synchronize signal
    latch_pointers: list = None  # latching pointers when comes synchronize signal

    def __init__(self, program: list[int], microprogram: list, stack_size: int, datapath: DataPath):
        self.program_memory = program
        self.program_counter = 0
        self.return_stack_size = stack_size
        self.return_stack = [0] * stack_size
        self.return_stack_pointer = 0
        self.instruction_register = 0
        self.microprogram_memory = microprogram
        self.microprogram_counter = 0
        self.instruction_decoder = 0
        self.datapath = datapath
        self._tick = 0
        self.latch = []
        self.latch_pointers = []

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    # get MUX values
    def get_mux_type_pc(self):
        if self.mux_type_pc == MUX.TYPE_PC_ZERO:
            if self.datapath.zero():
                return MUX.PC_INC
            else:
                return MUX.PC_JUMP
        elif self.mux_type_pc == MUX.TYPE_PC_MPC:
            return self.mux_pc
        else:
            raise ValueError(f"Wrong mux_type_pc value: {self.mux_type_pc}")

    def get_mux_pc(self):
        self.mux_pc = self.get_mux_type_pc()
        if self.mux_pc == MUX.PC_INC:
            return self.program_counter + 1
        elif self.mux_pc == MUX.PC_RS:
            return self.return_stack[self.return_stack_pointer]
        elif self.mux_pc == MUX.PC_JUMP:
            return self.program_memory[self.program_counter]
        else:
            raise ValueError(f"Wrong mux_pc value: {self.mux_pc}")

    def get_mux_mpc(self):
        if self.mux_mpc == MUX.MPC_ZERO:
            return 0
        elif self.mux_mpc == MUX.MPC_INC:
            return self.microprogram_counter + 1
        elif self.mux_mpc == MUX.MPC_ADDR:
            return self.instruction_decoder
        else:
            raise ValueError(f"Wrong mux_mpc value: {self.mux_mpc}")

    def get_mux_rsp(self):
        if self.mux_rsp == MUX.RSP_INC:
            return self.return_stack_pointer + 1
        elif self.mux_rsp == MUX.RSP_DEC:
            return self.return_stack_pointer - 1
        else:
            raise ValueError(f"Wrong mux_rsp value: {self.mux_rsp}")

    # MUX signals
    def signal_mux_type_pc(self, sel: MUX):
        self.mux_type_pc = sel

    def signal_mux_pc(self, sel: MUX):
        self.mux_pc = sel

    def signal_mux_mpc(self, sel: MUX):
        self.mux_mpc = sel

    def signal_mux_rsp(self, sel: MUX):
        self.mux_rsp = sel

    # latch signals
    def signal_latch_program_counter(self):
        self.program_counter = self.get_mux_pc()

    def signal_latch_return_stack_pointer(self):
        self.return_stack_pointer = self.get_mux_rsp()

    def signal_latch_instruction_register(self):
        self.instruction_register = self.program_memory[self.program_counter]
        self.instruction_decoder = microprogram.opcode_to_MPType(self.instruction_register)

    def signal_latch_microprogram_counter(self):
        self.microprogram_counter = self.get_mux_mpc()

    def signal_latch_return_stack(self):
        self.return_stack[self.return_stack_pointer] = self.program_counter

    def decode_and_execute(self):
        """
        Main cycle of processor
        1. Get micro-instructions
        2. Prepare signals
        3. Run MUX signals
        4. Run latch signals
        5. Run latch pointers and counters signals
        6. Repeat
        """
        microcommands = self.microprogram_memory[self.microprogram_counter]

        for signal in microcommands:
            # Halt signal
            if signal is Halt:
                raise StopIteration("Halt!")

            # latch signals
            if signal == Latch.DA:
                self.latch.append(self.datapath.signal_latch_data_address)
            elif signal == Latch.TOS:
                self.latch.append(self.datapath.signal_latch_tos)
            elif signal == Latch.SOS:
                self.latch.append(self.datapath.signal_latch_sos)
            elif signal == Latch.SB:
                self.latch.append(self.datapath.signal_latch_stack_buffer)
            elif signal == Latch.RS:
                self.latch.append(self.signal_latch_return_stack)
            elif signal == Latch.IR:
                self.latch.append(self.signal_latch_instruction_register)

            # latch pointers and counters signals
            elif signal == Latch.SP:
                self.latch_pointers.append(self.datapath.signal_latch_stack_pointer)
            elif signal == Latch.RSP:
                self.latch_pointers.append(self.signal_latch_return_stack_pointer)
            elif signal == Latch.PC:
                self.latch_pointers.append(self.signal_latch_program_counter)
            elif signal == Latch.MPC:
                self.latch_pointers.append(self.signal_latch_microprogram_counter)

            # ALU operations
            elif isinstance(signal, ALU):
                self.datapath.signal_alu_operation(signal)

            # Data Memory signals
            elif signal == DataMemory.OE:
                self.datapath.signal_oe()
            elif signal == DataMemory.WE:
                self.datapath.signal_we()

            # IO signals
            elif signal == IO.INPUT:
                self.datapath.signal_input()
            elif signal == IO.OUTPUT:
                self.datapath.signal_output()

            # MUX signals
            elif signal in [MUX.STACK_VALUE_DATA, MUX.STACK_VALUE_IMMEDIATE, MUX.STACK_VALUE_INPUT, MUX.STACK_VALUE_ALU, MUX.STACK_VALUE_SB]:
                if signal == MUX.STACK_VALUE_IMMEDIATE:
                    self.datapath.immediate_value = self.program_memory[self.program_counter]
                self.datapath.signal_mux_stack_value(signal)
            elif signal in [MUX.ALU_LEFT_ZERO, MUX.ALU_LEFT_STACK]:
                self.datapath.signal_mux_alu_left(signal)
            elif signal in [MUX.ALU_RIGHT_ZERO, MUX.ALU_RIGHT_DEC, MUX.ALU_RIGHT_INC, MUX.ALU_RIGHT_STACK]:
                self.datapath.signal_mux_alu_right(signal)
            elif signal in [MUX.TYPE_PC_ZERO, MUX.TYPE_PC_MPC]:
                self.signal_mux_type_pc(signal)
            elif signal in [MUX.PC_INC, MUX.PC_RS, MUX.PC_JUMP]:
                self.signal_mux_pc(signal)
            elif signal in [MUX.MPC_ZERO, MUX.MPC_INC, MUX.MPC_ADDR]:
                self.signal_mux_mpc(signal)
            elif signal in [MUX.SP_INC, MUX.SP_DEC, MUX.SP_DDEC]:
                self.datapath.signal_mux_stack_pointer(signal)
            elif signal in [MUX.RSP_INC, MUX.RSP_DEC]:
                self.signal_mux_rsp(signal)
            elif signal in [MUX.DATA_TOS, MUX.DATA_SOS]:
                self.datapath.signal_mux_stack_data(signal)

            else:
                raise ValueError(f"Wrong signal: {signal}")

        for func in self.latch:
            func()
        for func in self.latch_pointers:
            func()

        self.latch = []
        self.latch_pointers = []

        self.tick()

    def __repr__(self):
        pass
        # TODO processor string representation