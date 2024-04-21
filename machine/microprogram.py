from enum import Enum

from machine.isa import Opcode


class Latch(Enum):
    DA = 0
    TOS = 1
    SOS = 2
    SP = 3
    SB = 4
    RS = 5
    RSP = 6
    PC = 7
    IR = 8
    MPC = 9
    NMPC = 10
    # DATA_LINE = 11
    # PROG_LINE = 12


class MUX(Enum):
    STACK_VALUE_DATA = 0
    STACK_VALUE_IMMEDIATE = 1
    STACK_VALUE_INPUT = 2
    STACK_VALUE_ALU = 3
    STACK_VALUE_SB = 4

    ALU_LEFT_ZERO = 10
    ALU_LEFT_STACK = 11

    ALU_RIGHT_ZERO = 20
    ALU_RIGHT_DEC = 21
    ALU_RIGHT_INC = 22
    ALU_RIGHT_STACK = 23

    TYPE_PC_ZERO = 30  # if zero -> jump else -> inc
    TYPE_PC_MPC = 31  # default -> sets PC by value

    PC_INC = 40
    PC_RS = 41
    PC_JUMP = 42

    MPC_ZERO = 50
    MPC_INC = 51
    MPC_ADDR = 52
    MPC_NEXT = 53
    MPC_DATA_CACHE_READ_FETCH = 54
    MPC_DATA_CACHE_WRITE_FETCH = 55
    MPC_PROG_CACHE_READ_FETCH = 56
    # MPC_PROG_CACHE_WRITE_FETCH = 57

    SP_INC = 60
    SP_DEC = 61
    SP_DDEC = 62

    RSP_INC = 70
    RSP_DEC = 71

    DATA_TOS = 80
    DATA_SOS = 81

    # DATA_CACHE_MEMORY = 90
    # DATA_CACHE_PROC = 91
    #
    # PROGRAM_CACHE_MEMORY = 100
    # PROGRAM_CACHE_PROC = 101

    MPC_TYPE_NEXT = 110  # default -> sets MPC by value
    MPC_TYPE_READY = 111  # if ready -> next_mpc else data_fetch

    READY_DATA = 120
    READY_PROG = 121


class ALU(Enum):
    ADD = 0
    SUB = 1
    MUL = 2
    DIV = 3
    MOD = 4


class DataMemory(Enum):
    OE = 0
    WE = 1


class IO(Enum):
    INPUT = 0
    OUTPUT = 1


class Cache_Fetch(Enum):
    DATA_READ = 0
    DATA_WRITE = 1
    PROG_READ = 2
    # PROG_WRITE = 3


class Halt:
    pass


# instruction address in microprogram memory (!)
class MPType(Enum):
    INSTRUCTION_FETCH = 0
    DATA_CACHE_READ_FETCH = 3
    DATA_CACHE_WRITE_FETCH = 4
    PROG_CACHE_READ_FETCH = 5
    # PROG_CACHE_WRITE_FETCH = ???
    HLT = 6
    NOP = 7
    JMP = 8
    JZ = 10
    CALL = 12
    RET = 14
    PUSH = 15
    POP = 17
    LOAD = 20
    DROP = 23
    SWAP = 24
    DUP = 26
    INC = 28
    DEC = 29
    ADD = 30
    SUB = 31
    MUL = 32
    DIV = 33
    MOD = 34
    INPUT = 35
    OUTPUT = 37


mp_values = [e.value for e in MPType]


def get_mp_type(ind: int):
    assert ind >= 0
    while ind not in mp_values:
        ind -= 1
    return MPType(ind)


def opcode_to_MPType(opcode: int):
    if opcode == Opcode.HLT.value:
        return MPType.HLT
    elif opcode == Opcode.NOP.value:
        return MPType.NOP
    elif opcode == Opcode.JMP.value:
        return MPType.JMP
    elif opcode == Opcode.JZ.value:
        return MPType.JZ
    elif opcode == Opcode.CALL.value:
        return MPType.CALL
    elif opcode == Opcode.RET.value:
        return MPType.RET
    elif opcode == Opcode.PUSH.value:
        return MPType.PUSH
    elif opcode == Opcode.POP.value:
        return MPType.POP
    elif opcode == Opcode.LOAD.value:
        return MPType.LOAD
    elif opcode == Opcode.DROP.value:
        return MPType.DROP
    elif opcode == Opcode.SWAP.value:
        return MPType.SWAP
    elif opcode == Opcode.DUP.value:
        return MPType.DUP
    elif opcode == Opcode.INC.value:
        return MPType.INC
    elif opcode == Opcode.DEC.value:
        return MPType.DEC
    elif opcode == Opcode.ADD.value:
        return MPType.ADD
    elif opcode == Opcode.SUB.value:
        return MPType.SUB
    elif opcode == Opcode.MUL.value:
        return MPType.MUL
    elif opcode == Opcode.DIV.value:
        return MPType.DIV
    elif opcode == Opcode.MOD.value:
        return MPType.MOD
    elif opcode == Opcode.INPUT.value:
        return MPType.INPUT
    elif opcode == Opcode.OUTPUT.value:
        return MPType.OUTPUT
    else:
        raise ValueError(f"Wrong opcode: {opcode}")


# each array element is an active signals
microprogram_memory = [
    # 0 instruction fetch
    [Latch.MPC, MUX.MPC_PROG_CACHE_READ_FETCH, Latch.NMPC],
    [Latch.MPC, MUX.MPC_INC, MUX.PC_INC, Latch.PC, Latch.IR],
    [Latch.MPC, MUX.MPC_ADDR],
    # 3 data cache read fetch
    [
        Latch.MPC,
        MUX.READY_DATA,
        MUX.MPC_TYPE_READY,
        Cache_Fetch.DATA_READ,
        DataMemory.OE,
    ],
    # 4 data cache write fetch
    [
        Latch.MPC,
        MUX.READY_DATA,
        MUX.MPC_TYPE_READY,
        Cache_Fetch.DATA_WRITE,
        DataMemory.WE,
    ],
    # 5 prog cache read fetch
    [Latch.MPC, MUX.READY_PROG, MUX.MPC_TYPE_READY, Cache_Fetch.PROG_READ],
    # ??? prog cache write fetch
    # [Latch.MPC, MUX.READY_PROG, MUX.MPC_TYPE_READY, Cache_Fetch.PROG_WRITE],
    # 6 HLT = 0b10000000
    [Halt()],
    # 7 NOP = 0b10000001
    [Latch.MPC, MUX.MPC_ZERO],
    # 8 JMP = 0b10000010
    [Latch.MPC, MUX.MPC_PROG_CACHE_READ_FETCH, Latch.NMPC],
    [Latch.MPC, MUX.MPC_ZERO, MUX.PC_JUMP, Latch.PC],
    # 10 JZ = 0b10000011
    [Latch.MPC, MUX.MPC_PROG_CACHE_READ_FETCH, Latch.NMPC],
    [Latch.MPC, MUX.MPC_ZERO, MUX.TYPE_PC_ZERO, Latch.PC],
    # 12 CALL = 0b10000100
    [Latch.MPC, MUX.MPC_PROG_CACHE_READ_FETCH, Latch.NMPC, MUX.RSP_INC, Latch.RSP],
    [Latch.MPC, MUX.MPC_ZERO, MUX.PC_JUMP, Latch.PC, Latch.RS],
    # 14 RET = 0b10000101
    [Latch.MPC, MUX.MPC_ZERO, MUX.PC_RS, Latch.PC, MUX.RSP_DEC, Latch.RSP],
    #
    # 15 PUSH = 0b01000000
    [Latch.MPC, MUX.MPC_PROG_CACHE_READ_FETCH, Latch.NMPC, MUX.SP_INC, Latch.SP],
    [
        Latch.MPC,
        MUX.MPC_ZERO,
        MUX.PC_INC,
        Latch.PC,
        MUX.STACK_VALUE_IMMEDIATE,
        Latch.TOS,
    ],
    # 17 POP = 0b01000001
    [Latch.MPC, MUX.MPC_INC, MUX.DATA_SOS, Latch.DA],
    [Latch.MPC, MUX.MPC_DATA_CACHE_WRITE_FETCH, Latch.NMPC, MUX.DATA_TOS],
    [Latch.MPC, MUX.MPC_ZERO, MUX.SP_DDEC, Latch.SP],
    # 20 LOAD = 0b01000010
    [Latch.MPC, MUX.MPC_INC, MUX.DATA_TOS, Latch.DA],
    [Latch.MPC, MUX.MPC_DATA_CACHE_READ_FETCH, Latch.NMPC],
    [Latch.MPC, MUX.MPC_ZERO, MUX.STACK_VALUE_DATA, Latch.TOS],
    # 23 DROP = 0b01000011
    [Latch.MPC, MUX.MPC_ZERO, MUX.SP_DEC, Latch.SP],
    # 24 SWAP = 0b01000100
    [
        Latch.MPC,
        MUX.MPC_INC,
        MUX.DATA_TOS,
        Latch.SB,
        MUX.ALU_LEFT_ZERO,
        MUX.ALU_RIGHT_STACK,
        ALU.ADD,
        MUX.STACK_VALUE_ALU,
        Latch.TOS,
    ],
    [Latch.MPC, MUX.MPC_ZERO, MUX.STACK_VALUE_SB, Latch.SOS],
    # 26 DUP = 0b01000101
    [Latch.MPC, MUX.MPC_INC, MUX.DATA_TOS, Latch.SB, MUX.SP_INC, Latch.SP],
    [Latch.MPC, MUX.MPC_ZERO, MUX.STACK_VALUE_SB, Latch.TOS],
    #
    # 28 INC = 0b00100000
    [
        Latch.MPC,
        MUX.MPC_ZERO,
        MUX.DATA_TOS,
        MUX.ALU_LEFT_STACK,
        MUX.ALU_RIGHT_INC,
        ALU.ADD,
        MUX.STACK_VALUE_ALU,
        Latch.TOS,
    ],
    # 29 DEC = 0b00100001
    [
        Latch.MPC,
        MUX.MPC_ZERO,
        MUX.DATA_TOS,
        MUX.ALU_LEFT_STACK,
        MUX.ALU_RIGHT_DEC,
        ALU.ADD,
        MUX.STACK_VALUE_ALU,
        Latch.TOS,
    ],
    # 30 ADD = 0b00100010
    [
        Latch.MPC,
        MUX.MPC_ZERO,
        MUX.DATA_TOS,
        MUX.ALU_LEFT_STACK,
        MUX.ALU_RIGHT_STACK,
        ALU.ADD,
        MUX.STACK_VALUE_ALU,
        Latch.SOS,
        MUX.SP_DEC,
        Latch.SP,
    ],
    # 31 SUB = 0b00100011
    [
        Latch.MPC,
        MUX.MPC_ZERO,
        MUX.DATA_TOS,
        MUX.ALU_LEFT_STACK,
        MUX.ALU_RIGHT_STACK,
        ALU.SUB,
        MUX.STACK_VALUE_ALU,
        Latch.SOS,
        MUX.SP_DEC,
        Latch.SP,
    ],
    # 32 MUL = 0b00100100
    [
        Latch.MPC,
        MUX.MPC_ZERO,
        MUX.DATA_TOS,
        MUX.ALU_LEFT_STACK,
        MUX.ALU_RIGHT_STACK,
        ALU.MUL,
        MUX.STACK_VALUE_ALU,
        Latch.SOS,
        MUX.SP_DEC,
        Latch.SP,
    ],
    # 33 DIV = 0b00100101
    [
        Latch.MPC,
        MUX.MPC_ZERO,
        MUX.DATA_TOS,
        MUX.ALU_LEFT_STACK,
        MUX.ALU_RIGHT_STACK,
        ALU.DIV,
        MUX.STACK_VALUE_ALU,
        Latch.SOS,
        MUX.SP_DEC,
        Latch.SP,
    ],
    # 34 MOD = 0b00100110
    [
        Latch.MPC,
        MUX.MPC_ZERO,
        MUX.DATA_TOS,
        MUX.ALU_LEFT_STACK,
        MUX.ALU_RIGHT_STACK,
        ALU.MOD,
        MUX.STACK_VALUE_ALU,
        Latch.SOS,
        MUX.SP_DEC,
        Latch.SP,
    ],
    #
    # 35 INPUT = 0b00010000
    [Latch.MPC, MUX.MPC_INC, MUX.SP_INC, Latch.SP],
    [Latch.MPC, MUX.MPC_ZERO, IO.INPUT, MUX.STACK_VALUE_INPUT, Latch.TOS],
    # 37 OUTPUT = 0b00010001
    [Latch.MPC, MUX.MPC_ZERO, MUX.DATA_TOS, IO.OUTPUT, MUX.SP_DEC, Latch.SP],
]
