#!/usr/bin/python3
import struct
from enum import Enum


MIN_SIGN = -(2 ** 15)
MAX_SIGN = 2 ** 15 - 1
MAX_UNSIGN = 2 ** 16 - 1

class Opcode(Enum):
    """
    As program memory is 16-bit, only last byte is represented, first is 0x00
    Opcodes can be divided into groups:
    1. Program flow     - starts with 1
    2. Stack operations - starts with 01
    3. Arithmetics      - starts with 001
    4. IO               - starts with 0001
    5. Data allocation  - starts with 00001
    """

    HLT     = 0b10000000
    NOP     = 0b10000001
    JMP     = 0b10000010
    JZ      = 0b10000011
    CALL    = 0b10000100
    RET     = 0b10000101

    PUSH    = 0b01000000
    POP     = 0b01000001
    LOAD    = 0b01000010
    DROP    = 0b01000011
    SWAP    = 0b01000100
    DUP     = 0b01000101

    INC     = 0b00100000
    DEC     = 0b00100001
    ADD     = 0b00100010
    SUB     = 0b00100011
    MUL     = 0b00100100
    DIV     = 0b00100101
    MOD     = 0b00100110

    INPUT   = 0b00010000
    OUTPUT  = 0b00010001

    NUMBER  = 0b00001000
    STRING  = 0b00001001
    BUFFER  = 0b00001010


def write_code(target: str, code: list[int]):
    with open(target, "wb") as f:
        f.write(struct.pack(f"{len(code)}H", *code))


def read_code(source: str) -> list[int]:
    code = []
    with open(source, "rb") as f:
        short = f.read(2)
        while short:
            code.append(*struct.unpack("H", short))
            short = f.read(2)

    return code


print(read_code("./out/cat.out"))


