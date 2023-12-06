"""
THIS FILE IS NOT GRADED.

This file defines the base types used in the homework.
"""

from abc import ABC, abstractmethod
from enum import Enum

from typing import Generic

"""
MESI states. You MUST use State Enum to assign state to data.
"""


class State(Enum):
    M = 0
    E = 1
    S = 2
    I = 3


"""
This class defines a memory location that is stored in main memory and caches.
The autograder uses the properties defined in this class to test code so make
sure you correctly assign values.
"""


class MemoryLocation:
    addr: int
    data: int
    state: State
    last_used: int

    def __init__(self, addr: int, data: int):
        self.addr = addr
        self.data = data
        self.state = None
        self.last_used = -1

    def update_state(self, state: State):
        self.state = state


"""
This defines a main memory with infinite space. The class does not do any error
or sanity checks.
"""


class MainMemory:
    _data: dict()

    def __init__(self):
        self._data = dict()

    def update_data(self, addr, data):
        loc = self.get_loc(addr)
        loc.data = data
        self._data[addr] = loc

    def get_loc(self, addr: int):
        if addr not in self._data.keys():
            loc = MemoryLocation(addr, 0)
            self._data[addr] = loc
        return self._data[addr]


"""
This defines the abstract class that you need to code.
"""


class StudentCode(ABC):
    cpu_count: int  # defines the number of cpus in the system
    cpu_cache: list()  # defines the private cache for each cpu
    llc = None  # defines a shared cache
    main_memory: MainMemory()  # defines an infinite memory

    # llc_size is large enough to prevent evictions
    def __init__(self, cpu_count: int, cache_size: int, llc_size: int):
        self.cpu_count = cpu_count
        self.cpu_cache = [Cache(i, cache_size, self) for i in range(cpu_count)]
        self.llc = Cache(-1, llc_size, self)
        self.main_memory = MainMemory()

    # this function increments the timestamp for caches that is used when evicting data
    def tick(self):
        for cache in self.cpu_cache:
            cache.tick()
        self.llc.tick()

    @abstractmethod
    def evict_from_private_cache(self, loc, cpu_id: int):
        pass

    @abstractmethod
    def load_data(self, addr: int, cpu_id: int):
        pass

    @abstractmethod
    def store_data(self, data: int, addr: int, cpu_id: int):
        pass


"""
This class defines a cache. Many functions are helper function that you do not 
have to use in order to pass the autograder. 
"""


class Cache:
    _id: int
    _size: int
    _data: dict()
    _filled: int
    _coherence: StudentCode
    _clock: int

    def __init__(self, _id: int, _size: int, _coherence):
        self._id = _id
        self._size = _size
        self._data = dict()
        self._filled = 0
        self._coherence = _coherence
        self._clock = 0

    def tick(self):
        self._clock += 1

    # this function clones the loc when it is added to the cache
    def add_loc(self, loc):
        if self._size == self._filled:
            self.evict_loc()
        new_loc = MemoryLocation(loc.addr, loc.data)
        new_loc.state = loc.state
        new_loc.last_used = self._clock
        self._data[new_loc.addr] = new_loc
        self._filled += 1

    def update_addr_state(self, addr: int, state):
        if addr not in self._data.keys():
            raise Exception("Addr not in cache {0} updated".format(self._id))
        self._data[addr].update_state(state)

    def update_addr_data(self, addr: int, data: int):
        if addr not in self._data.keys():
            raise Exception("Addr not in cache {0} updated".format(self._id))
        self._data[addr].last_used = self._clock
        self._data[addr].data = data

    def update_last_used(self, addr: int, timestamp: int):
        if addr not in self._data.keys():
            raise Exception("Addr not in cache {0} updated".format(self._id))
        self._data[addr].last_used = timestamp

    # this function returns a new object for the MemoryLocation
    def get_loc(self, addr: int):
        if addr not in self._data.keys():
            return None
        self._data[addr].last_used = self._clock
        loc = self._data[addr]
        new_loc = MemoryLocation(loc.addr, loc.data)
        new_loc.state = loc.state
        new_loc.last_used = loc.last_used
        return new_loc

    def contains_addr(self, addr: int):
        return addr in self._data.keys()

    def evict_loc(self):
        if self._filled == 0:
            raise Exception("Evicting from empty cache {0}".format(self._id))
        last_used_addr = -1
        last_used_time = -1
        for key, value in self._data.items():
            if value.state == State.I:
                if last_used_addr == -1:
                    last_used_addr = key
                    last_used_time = value.last_used
                else:
                    if value.last_used < last_used_time:
                        last_used_addr = key
                        last_used_time = value.last_used

        if last_used_addr == -1:
            for key, value in self._data.items():
                if last_used_addr == -1:
                    last_used_addr = key
                    last_used_time = value.last_used
                else:
                    if value.last_used < last_used_time:
                        last_used_addr = key
                        last_used_time = value.last_used
        loc = self.get_loc(last_used_addr)
        self._data.pop(last_used_addr)
        self._filled -= 1
        self._coherence.evict_from_private_cache(loc, self._id)
