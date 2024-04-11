#!/usr/bin/python3
import sys

from isa import Opcode, write_code, MIN_SIGN, MAX_SIGN, MAX_UNSIGN


def get_meaningful_token(line: str) -> str:
    return line.split(";", 1)[0].strip()


def translate_data_part(token: str) -> tuple[str, list[str | int | Opcode]]:
    variable, str_opcode, arg = token.split(" ", 2)
    opcode = Opcode[str_opcode]
    assert opcode in [Opcode.NUMBER, Opcode.STRING, Opcode.BUFFER], f"Wrong instruction in data part {token}"
    tokens = [opcode]

    if opcode == Opcode.NUMBER:
        num = int(arg)
        assert MIN_SIGN <= num <= MAX_SIGN, f"Wrong instruction argument: {token}"
        if num < 0:
            num = MAX_UNSIGN + num
        tokens += [num]
    elif opcode == Opcode.STRING:
        tokens += [ord(c) for c in arg] + [0]
    elif opcode == Opcode.BUFFER:
        num = int(arg)
        assert 1 <= num <= MAX_UNSIGN, f"Wrong instruction argument: {token}"
        tokens += [num]
    else:
        raise AttributeError()

    return variable, tokens


def translate_code_part(token: str) -> list[str | int | Opcode]:
    tokens = []
    if " " in token:  # instruction with argument
        sub_tokens = token.split(" ")
        assert len(sub_tokens) == 2, f"Invalid instruction, check arguments amount: {token}"
        opcode = Opcode[sub_tokens[0]]
        assert opcode in [Opcode.PUSH, Opcode.JMP, Opcode.JZ,
                          Opcode.CALL], f"Instruction shouldn't have an argument: {token}"
        arg = sub_tokens[1]
        if arg.isdigit():
            arg = int(arg)
            assert MIN_SIGN <= arg < MAX_SIGN, f"16-bit numbers only {token}"
            if arg < 0:
                arg = MAX_UNSIGN + arg

        tokens += [opcode, arg]

    else:  # instruction without argument
        opcode = Opcode[token]
        tokens.append(opcode)

    return tokens


def translate_stage_1(text: str) -> tuple[dict[str, int], dict[str, int], list[str | int | Opcode]]:
    variables = {}
    labels = {}
    tokens = []

    data_stage = True

    data_counter = 0
    program_counter = 0
    for line in text.splitlines():
        token = get_meaningful_token(line)
        if token == "" or token == ".data:":
            continue

        if token == ".code:":
            data_stage = False
            continue

        if data_stage:
            variable, data_part = translate_data_part(token)
            assert variable not in variables, f"Redefinition of variable: {variable}"
            variables[variable] = data_counter
            data_counter += len(data_part) - 1
            tokens += data_part

        else:
            if token.endswith(":"):  # label
                label = token.strip(":")
                assert label not in labels, f"Redefinition of label: {label}"
                labels[label] = program_counter
            else:
                tokens_part = translate_code_part(token)
                program_counter += len(tokens_part)
                tokens += tokens_part

    return labels, variables, tokens


def translate_stage_2(labels: dict[str, int], variables: dict[str, int], tokens: list[str | int | Opcode]) -> list[int]:
    code = []
    for token in tokens:
        if isinstance(token, Opcode):
            code.append(token.value)
        elif isinstance(token, int):
            assert 0 <= token <= MAX_UNSIGN, f"16-bit numbers only {token}"
            code.append(token)
        else:
            assert token in labels or token in variables, f"Label or variable is not defined: {token}"
            if token in labels:
                code.append(labels[token])
            else:
                code.append(variables[token])

    return code


def translate(text: str) -> list[int]:
    labels, variables, tokens = translate_stage_1(text)
    code = translate_stage_2(labels, variables, tokens)

    return code


def main(source: str, target: str):
    with open(source, "r") as f:
        text = f.read()

    code = translate(text)

    write_code(target, code)


if __name__ == "__main__":
    assert len(sys.argv) == 3, r"Wrong arguments: .\translator.py <input_file> <output_file>"
    _, source, target = sys.argv
    main(source, target)

    with open(source, "r") as f:
        text = f.read()

    res1 = translate_stage_1(text)
    res2 = translate(text)

    print(res1)
    print(res2)
