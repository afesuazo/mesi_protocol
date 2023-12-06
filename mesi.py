from base import State, StudentCode, MemoryLocation

"""
MESI

I - E : Read the only copy
I - S : Read a shared copy
I - M : Write the only copy

S - I : Someone wants to write 
S - M : Write, tell others to invalidate
 
M - I : Someone else wants to write
M - S : Someone else wants to read 

E - M : Write the only copy 
E - S : Someone else wants to read
E - I : Someone else wants to write

"""


class MESICoherence(StudentCode):
    # loc is of type MemoryLocation defined in base.py
    def evict_from_private_cache(self, loc, cpu_id: int):
        """
        Called when loc is evicted from the cache, should happen when a cpu wants to write
        and loc is shared with other cpus
        """

        # Check the current state
        state = loc.state

        if state in [State.E, State.S]:
            # Make sure that no duplicate addresses are added
            if self.llc.contains_addr(loc.addr):
                self.llc.update_addr_state(loc.addr, state)
            else:
                self.llc.add_loc(loc)

        # We need to write back to llc and main memory
        elif state == State.M:
            # If address exists, simply update it
            if self.llc.contains_addr(loc.addr):
                self.llc.update_addr_state(loc.addr, state)
            else:
                self.llc.add_loc(loc)

            self.main_memory.update_data(loc.addr, loc.data)

        # Set as invalid in the private cache
        self.cpu_cache[cpu_id].update_addr_state(loc.addr, State.I)

    def load_data(self, addr: int, cpu_id: int):
        """
        Load data from the cache
        """

        # Try the private cache first
        if self.cpu_cache[cpu_id].contains_addr(addr):
            # Private cache has the address, now we check the state
            loc = self.cpu_cache[cpu_id].get_loc(addr)

        pass

    def store_data(self, data: int, addr: int, cpu_id: int):
        """
        Store data to the cache
        """

        # Try the private cache first
        if self.cpu_cache[cpu_id].contains_addr(addr):
            # Private cache has the address, now we check the state
            pass
        pass
