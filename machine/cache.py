import math

from machine.isa import BITS


class Cache:
    cache_size: int = None
    cache_tags: list[int] = None
    cache_modified: list[bool] = None
    cache_lines: list[int] = None
    bus_size: int = None
    memory_size: int = None
    memory: list[int] = None

    index_bits: int = None
    tag_bits: int = None
    ticks_left: int = None

    cache_address: int = None
    operation = None

    def __init__(
        self, delay: int, cache_size: int, bus_size: int, memory: list[int] = None
    ):
        self.delay = delay
        self.cache_size = cache_size
        self.cache_tags = [-1] * cache_size
        self.cache_lines = [-1] * cache_size
        self.cache_modified = [False] * cache_size
        self.bus_size = bus_size
        self.memory_size = len(memory)
        self.memory = memory

        self.index_bits = math.ceil(math.log2(self.cache_size))
        self.tag_bits = BITS - self.index_bits

        self.cache_address = 0
        self.ticks_left = 0

    def _get_tag(self):
        return self.cache_address // (2**self.index_bits)

    def _get_index(self):
        return self.cache_address % (2**self.index_bits)

    def _get_address(self, tag, index):
        return (tag << self.index_bits) + index

    def _read(self):
        orig_address = self.cache_address

        for i in range(self.bus_size):
            index = self._get_index()
            if self.cache_tags[index] == self._get_tag():
                continue
            elif (
                self.cache_tags[index] != self._get_tag() and self.cache_modified[index]
            ):
                self._write()
                self.ticks_left += self.delay
            self.cache_tags[index] = self._get_tag()
            self.cache_lines[index] = self.memory[self.cache_address]
            self.cache_modified[index] = False

            self.cache_address += 1
            if self.cache_address >= self.memory_size:
                break

        self.cache_address = orig_address

    def _write_and_read(self):
        self._write()
        self._read()

    def _write(self):
        index = self._get_index()
        address = self._get_address(self.cache_tags[index], index)
        self.memory[address] = self.cache_lines[index]
        self.cache_modified[index] = False

    def get_line(self):
        assert self.ready()
        index = self._get_index()
        return self.cache_lines[index]

    def set_cache_address(self, addr):
        self.cache_address = addr

    def ready(self):
        tag = self._get_tag()
        return tag in self.cache_tags and self.ticks_left == 0

    def read_data(self):
        assert (
            0 <= self.cache_address < self.memory_size
        ), f"Out of memory: {self.cache_address}"

        if self.ticks_left != 0:
            return

        index = self._get_index()
        if self._get_tag() == self.cache_tags[index]:
            return
        elif self.cache_modified[index]:
            self.ticks_left = self.delay * 2
            self.operation = self._write_and_read
        else:
            self.ticks_left = self.delay
            self.operation = self._read

    def write_data(self, data):
        assert (
            0 <= self.cache_address < self.memory_size
        ), f"Out of memory: {self.cache_address}"

        if self.ticks_left != 0:
            return

        index = self._get_index()
        tag = self._get_tag()
        if self.cache_modified[index]:
            self.ticks_left = self.delay
            self.operation = lambda: self._write()
        else:
            self.cache_modified[index] = True
            self.cache_tags[index] = tag
            self.cache_lines[index] = data

    def clear(self):
        orig_addr = self.cache_address
        for i in range(self.cache_size):
            if self.cache_tags[self._get_index()] != -1:
                self._write()
            self.cache_address += 1
        self.cache_address = orig_addr

    def tick(self):
        if self.ticks_left > 0:
            self.ticks_left -= 1
            if self.ticks_left == 0:
                self.operation()

    def __repr__(self):
        state_repr = (
            " ".join(
                f"[{tag:3}|{line:3}|{'M' if mod else 'U'}]"
                for tag, line, mod in zip(
                    self.cache_tags, self.cache_lines, self.cache_modified
                )
            )
            + f" Ticks_left: {self.ticks_left} Ready: {self.ready()}"
        )
        return state_repr
