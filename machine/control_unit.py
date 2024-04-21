import machine.microprogram
from machine.cache import Cache
from machine.datapath import DataPath
from machine.isa import Opcode, opcode_values
from machine.microprogram import (
    ALU,
    MUX,
    Latch,
    DataMemory,
    IO,
    Halt,
    MPType,
    Cache_Fetch,
)


class ControlUnit:
    cache: Cache = None
    program_counter: int = None
    return_stack_size: int = None
    return_stack: list[int] = None
    return_stack_pointer: int = None
    instruction_register: int = None
    microprogram_memory: list = None
    microprogram_counter: int = None
    next_mpc: int = None

    instruction_decoder: int = None

    mux_type_pc: MUX = None
    mux_pc: MUX = None
    mux_mpc: MUX = None
    mux_rsp: MUX = None
    mux_mpc_type: MUX = None
    mux_ready: MUX = None

    datapath: DataPath = None

    _tick: int = None
    latch: list = None  # latching when comes synchronize signal
    latch_pointers: list = None  # latching pointers when comes synchronize signal

    def __init__(
        self,
        cache: Cache,
        microprogram: list,
        stack_size: int,
        datapath: DataPath,
    ):
        self.cache = cache
        self.program_counter = 0
        self.return_stack_size = stack_size
        self.return_stack = [-1] * stack_size
        self.return_stack_pointer = -1
        self.instruction_register = 0
        self.microprogram_memory = microprogram
        self.microprogram_counter = 0
        self.next_mpc = 0
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
                return MUX.PC_JUMP
            else:
                return MUX.PC_INC
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
            return self.cache.get_line()
        else:
            raise ValueError(f"Wrong mux_pc value: {self.mux_pc}")

    def get_mux_mpc(self):
        self.mux_mpc = self.get_mux_mpc_type()
        if self.mux_mpc == MUX.MPC_ZERO:
            return MPType.INSTRUCTION_FETCH.value
        elif self.mux_mpc == MUX.MPC_DATA_CACHE_READ_FETCH:
            return MPType.DATA_CACHE_READ_FETCH.value
        elif self.mux_mpc == MUX.MPC_DATA_CACHE_WRITE_FETCH:
            return MPType.DATA_CACHE_WRITE_FETCH.value
        elif self.mux_mpc == MUX.MPC_PROG_CACHE_READ_FETCH:
            return MPType.PROG_CACHE_READ_FETCH.value
        elif self.mux_mpc == MUX.MPC_INC:
            return self.microprogram_counter + 1
        elif self.mux_mpc == MUX.MPC_ADDR:
            return self.instruction_decoder
        elif self.mux_mpc == MUX.MPC_NEXT:
            return self.next_mpc
        else:
            raise ValueError(f"Wrong mux_mpc value: {self.mux_mpc}")

    def get_mux_rsp(self):
        if self.mux_rsp == MUX.RSP_INC:
            return self.return_stack_pointer + 1
        elif self.mux_rsp == MUX.RSP_DEC:
            return self.return_stack_pointer - 1
        else:
            raise ValueError(f"Wrong mux_rsp value: {self.mux_rsp}")

    def get_mux_mpc_type(self):
        if self.mux_mpc_type == MUX.MPC_TYPE_NEXT:
            return self.mux_mpc
        elif self.mux_mpc_type == MUX.MPC_TYPE_READY:
            return self.get_mux_ready()
        else:
            raise ValueError(f"Wrong mux_mpc_type value: {self.mux_mpc_type}")

    def get_mux_ready(self):
        if self.mux_ready == MUX.READY_DATA and self.datapath.cache.ready():
            return MUX.MPC_NEXT
        elif self.mux_ready == MUX.READY_PROG and self.cache.ready():
            return MUX.MPC_NEXT
        elif self.mux_ready in [MUX.READY_DATA, MUX.READY_PROG]:
            return self.mux_mpc
        else:
            raise ValueError(f"Wrong mux_ready value: {self.mux_ready}")

    # MUX signals
    def signal_mux_type_pc(self, sel: MUX):
        self.mux_type_pc = sel

    def signal_mux_pc(self, sel: MUX):
        self.mux_pc = sel

    def signal_mux_mpc(self, sel: MUX):
        self.mux_mpc = sel

    def signal_mux_rsp(self, sel: MUX):
        self.mux_rsp = sel

    def signal_mux_mpc_type(self, sel: MUX):
        self.mux_mpc_type = sel

    def signal_mux_ready(self, sel: MUX):
        self.mux_ready = sel

    # latch signals
    def signal_latch_program_counter(self):
        self.program_counter = self.get_mux_pc()
        self.cache.cache_address = self.program_counter

    def signal_latch_return_stack_pointer(self):
        self.return_stack_pointer = self.get_mux_rsp()
        assert (
            -1 <= self.return_stack_pointer < self.return_stack_size
        ), f"Out of stack: {self.return_stack_pointer}"

    def signal_latch_instruction_register(self):
        self.instruction_register = self.cache.get_line()
        self.instruction_decoder = machine.microprogram.opcode_to_MPType(
            self.instruction_register
        ).value

    def signal_latch_next_mpc(self):
        self.next_mpc = self.microprogram_counter + 1

    def signal_latch_microprogram_counter(self):
        self.microprogram_counter = self.get_mux_mpc()

    def signal_latch_return_stack(self):
        self.return_stack[self.return_stack_pointer] = (
            self.program_counter + 1
        )  # To jump to next command!

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

        # default
        self.mux_type_pc = MUX.TYPE_PC_MPC
        self.mux_mpc_type = MUX.MPC_TYPE_NEXT

        for signal in microcommands:
            # Halt signal
            if isinstance(signal, Halt):
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
            elif signal == Latch.NMPC:
                self.latch.append(self.signal_latch_next_mpc)

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

            # cache signals
            elif signal == Cache_Fetch.DATA_READ:
                self.datapath.cache.read_data()
            elif signal == Cache_Fetch.DATA_WRITE:
                self.datapath.cache.write_data(self.datapath.get_mux_stack_data())
            elif signal == Cache_Fetch.PROG_READ:
                self.cache.read_data()

            # MUX signals
            elif signal in [
                MUX.STACK_VALUE_DATA,
                MUX.STACK_VALUE_IMMEDIATE,
                MUX.STACK_VALUE_INPUT,
                MUX.STACK_VALUE_ALU,
                MUX.STACK_VALUE_SB,
            ]:
                if signal == MUX.STACK_VALUE_IMMEDIATE:
                    self.datapath.immediate_value = self.cache.get_line()
                self.datapath.signal_mux_stack_value(signal)
            elif signal in [MUX.ALU_LEFT_ZERO, MUX.ALU_LEFT_STACK]:
                self.datapath.signal_mux_alu_left(signal)
            elif signal in [
                MUX.ALU_RIGHT_ZERO,
                MUX.ALU_RIGHT_DEC,
                MUX.ALU_RIGHT_INC,
                MUX.ALU_RIGHT_STACK,
            ]:
                self.datapath.signal_mux_alu_right(signal)
            elif signal in [MUX.TYPE_PC_ZERO, MUX.TYPE_PC_MPC]:
                self.signal_mux_type_pc(signal)
            elif signal in [MUX.PC_INC, MUX.PC_RS, MUX.PC_JUMP]:
                self.signal_mux_pc(signal)
            elif signal in [
                MUX.MPC_ZERO,
                MUX.MPC_INC,
                MUX.MPC_ADDR,
                MUX.MPC_NEXT,
                MUX.MPC_DATA_CACHE_READ_FETCH,
                MUX.MPC_DATA_CACHE_WRITE_FETCH,
                MUX.MPC_PROG_CACHE_READ_FETCH,
            ]:
                self.signal_mux_mpc(signal)
            elif signal in [MUX.SP_INC, MUX.SP_DEC, MUX.SP_DDEC]:
                self.datapath.signal_mux_stack_pointer(signal)
            elif signal in [MUX.RSP_INC, MUX.RSP_DEC]:
                self.signal_mux_rsp(signal)
            elif signal in [MUX.DATA_TOS, MUX.DATA_SOS]:
                self.datapath.signal_mux_stack_data(signal)
            elif signal in [MUX.MPC_TYPE_NEXT, MUX.MPC_TYPE_READY]:
                self.signal_mux_mpc_type(signal)
            elif signal in [MUX.READY_DATA, MUX.READY_PROG]:
                self.signal_mux_ready(signal)

            else:
                raise ValueError(f"Wrong signal: {signal}")

        for func in self.latch:
            func()
        for func in self.latch_pointers:
            func()

        self.latch = []
        self.latch_pointers = []

        self.tick()
        self.cache.tick()
        self.datapath.cache.tick()

    def __repr__(self):
        mp_opcode = machine.microprogram.get_mp_type(self.microprogram_counter)
        stack = self.datapath.stack
        tos = stack[self.datapath.stack_pointer]

        opcode = None
        if 0 <= self.program_counter - 1 < self.cache.memory_size:
            opcode = self.cache.memory[self.program_counter - 1]
        if opcode in opcode_values:
            opcode = Opcode(opcode)

        state_repr = (
            f"[{self.program_counter:2}: {str(opcode):13}] TICK: {self._tick:4} PC: {self.program_counter:3} MPC: {self.microprogram_counter:2} "
            f"IR: {self.instruction_register:3} RSC: {self.return_stack_pointer:2} TOS: {tos: 3} "
            f"AR: {self.datapath.data_address:3} SB: {self.datapath.stack_buffer:3} SP: {self.datapath.stack_pointer:2}"
            f"\t{mp_opcode.name}"
        )
        return state_repr
