from enum import Enum


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

    TYPE_PC_ZERO = 30  # if zero -> inc else -> addr
    TYPE_PC_MPC = 31  # default -> sets MUX.PC_ by value

    PC_INC = 40
    PC_RS = 41
    PC_JUMP = 42

    MPC_ZERO = 50
    MPC_INC = 51
    MPC_ADDR = 52

    SP_INC = 60
    SP_DEC = 61
    SP_DDEC = 62

    RSP_INC = 70
    RSP_DEC = 71

    VALUE_TOS = 80
    VALUE_SOS = 81


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


# instruction address in microprogram memory (!)
class MPType(Enum):
    INSTRUCTION_FETCH = 0
    HLT = 2
    NOP = 3
    JMP = 4
    JZ = 5
    CALL = 6
    RET = 8
    PUSH = 9
    POP = 11
    LOAD = 13
    DROP = 15
    SWAP = 16
    DUP = 18
    INC = 20
    DEC = 21
    ADD = 22
    SUB = 23
    MUL = 24
    DIV = 25
    MOD = 26
    INPUT = 27
    OUTPUT = 29


class Halt: pass


# each array element is an active signals
microprogram_memory = [
    # 0 instruction fetch
    [Latch.MPC, MUX.MPC_INC, MUX.PC_INC, Latch.PC, Latch.IR],
    [Latch.MPC, MUX.MPC_ADDR],
    # 2 HLT = 0b10000000
    [Halt],
    # 3 NOP = 0b10000001
    [Latch.MPC, MUX.MPC_ZERO],
    # 4 JMP = 0b10000010
    [Latch.MPC, MUX.MPC_ZERO, MUX.PC_JUMP, Latch.PC],
    # 5 JZ = 0b10000011
    [Latch.MPC, MUX.MPC_ZERO, MUX.TYPE_PC_ZERO, Latch.PC],
    # 6 CALL = 0b10000100
    [Latch.MPC, MUX.MPC_INC, MUX.RSP_INC, Latch.RSP],
    [Latch.MPC, MUX.MPC_ZERO, MUX.PC_JUMP, Latch.PC, Latch.RS],
    # 8 RET = 0b10000101
    [Latch.MPC, MUX.MPC_ZERO, MUX.PC_RS, Latch.PC, MUX.RSP_DEC, Latch.RSP],
    #
    # 9 PUSH = 0b01000000
    [Latch.MPC, MUX.MPC_INC, MUX.SP_INC, Latch.SP],
    [Latch.MPC, MUX.MPC_ZERO, MUX.PC_INC, Latch.PC, MUX.STACK_VALUE_IMMEDIATE, Latch.TOS],
    # 11 POP = 0b01000001
    [Latch.MPC, MUX.MPC_INC, MUX.VALUE_SOS, Latch.DA],
    [Latch.MPC, MUX.MPC_ZERO, MUX.VALUE_TOS, DataMemory.WE, MUX.SP_DDEC, Latch.SP],
    # 13 LOAD = 0b01000010
    [Latch.MPC, MUX.MPC_INC, MUX.VALUE_TOS, Latch.DA],
    [Latch.MPC, MUX.MPC_ZERO, DataMemory.OE, MUX.STACK_VALUE_DATA, Latch.TOS],
    # 15 DROP = 0b01000011
    [Latch.MPC, MUX.MPC_ZERO, MUX.SP_DEC, Latch.SP],
    # 16 SWAP = 0b01000100
    [Latch.MPC, MUX.MPC_INC, MUX.VALUE_TOS, Latch.SB, MUX.ALU_LEFT_ZERO, MUX.ALU_RIGHT_STACK, ALU.ADD, MUX.STACK_VALUE_ALU, Latch.TOS],
    [Latch.MPC, MUX.MPC_ZERO, MUX.STACK_VALUE_SB, Latch.SOS],
    # 18 DUP = 0b01000101
    [Latch.MPC, MUX.MPC_INC, MUX.VALUE_TOS, Latch.SB, MUX.SP_INC, Latch.SP],
    [Latch.MPC, MUX.MPC_ZERO, MUX.STACK_VALUE_SB, Latch.TOS],
    #
    # 20 INC = 0b00100000
    [Latch.MPC, MUX.MPC_ZERO, MUX.VALUE_TOS, MUX.ALU_LEFT_STACK, MUX.ALU_RIGHT_INC, ALU.ADD, MUX.STACK_VALUE_ALU, Latch.TOS],
    # 21 DEC = 0b00100001
    [Latch.MPC, MUX.MPC_ZERO, MUX.VALUE_TOS, MUX.ALU_LEFT_STACK, MUX.ALU_RIGHT_DEC, ALU.ADD, MUX.STACK_VALUE_ALU, Latch.TOS],
    # 22 ADD = 0b00100010
    [Latch.MPC, MUX.MPC_ZERO, MUX.VALUE_TOS, MUX.ALU_LEFT_STACK, MUX.ALU_RIGHT_STACK, ALU.ADD, MUX.STACK_VALUE_ALU, Latch.SOS, MUX.SP_DEC, Latch.SP],
    # 23 SUB = 0b00100011
    [Latch.MPC, MUX.MPC_ZERO, MUX.VALUE_TOS, MUX.ALU_LEFT_STACK, MUX.ALU_RIGHT_STACK, ALU.SUB, MUX.STACK_VALUE_ALU, Latch.SOS, MUX.SP_DEC, Latch.SP],
    # 24 MUL = 0b00100100
    [Latch.MPC, MUX.MPC_ZERO, MUX.VALUE_TOS, MUX.ALU_LEFT_STACK, MUX.ALU_RIGHT_STACK, ALU.MUL, MUX.STACK_VALUE_ALU, Latch.SOS, MUX.SP_DEC, Latch.SP],
    # 25 DIV = 0b00100101
    [Latch.MPC, MUX.MPC_ZERO, MUX.VALUE_TOS, MUX.ALU_LEFT_STACK, MUX.ALU_RIGHT_STACK, ALU.DIV, MUX.STACK_VALUE_ALU, Latch.SOS, MUX.SP_DEC, Latch.SP],
    # 26 MOD = 0b00100110
    [Latch.MPC, MUX.MPC_ZERO, MUX.VALUE_TOS, MUX.ALU_LEFT_STACK, MUX.ALU_RIGHT_STACK, ALU.MOD, MUX.STACK_VALUE_ALU, Latch.SOS, MUX.SP_DEC, Latch.SP],
    #
    # 27 INPUT = 0b00010000
    [Latch.MPC, MUX.MPC_INC, MUX.SP_INC, Latch.SP],
    [Latch.MPC, MUX.MPC_ZERO, IO.INPUT, MUX.STACK_VALUE_INPUT, Latch.TOS],
    # 29 OUTPUT = 0b00010001
    [Latch.MPC, MUX.MPC_ZERO, MUX.VALUE_TOS, IO.OUTPUT, MUX.SP_DEC, Latch.SP],
]
