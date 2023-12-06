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
        # self.cpu_cache[cpu_id].update_addr_state(loc.addr, State.I)

    def load_data(self, addr: int, cpu_id: int):
        """
        Load data from the cache
        """

        # Try the private cache first
        if self.cpu_cache[cpu_id].contains_addr(addr):
            # Private cache has the address, now we check the state
            loc = self.cpu_cache[cpu_id].get_loc(addr)
            return loc.data

        # If not found in the private cache we try other caches
        # We create a list of all cpus that have the address (if any)
        cpus = [valid_cpu for valid_cpu in range(self.cpu_count) if valid_cpu != cpu_id
                and self.cpu_cache[valid_cpu].contains_addr(addr)]

        # We need to read data so we make sure caches are set to S state
        for cpu in cpus:
            loc = self.cpu_cache[cpu].get_loc(addr)
            if loc.state in [State.E, State.M]:
                self.cpu_cache[cpu].update_addr_state(addr, State.S)
                loc.update_state(State.S)
                self.cpu_cache[cpu_id].add_loc(loc)
                return loc.data

        # Nopt found in private or other caches, now we check LLC
        if self.llc.contains_addr(addr):
            loc = self.llc.get_loc(addr)
            loc.update_state(State.S)
            self.cpu_cache[cpu_id].add_loc(loc)
            return loc.data

        # No data found so far, now we go to main memory
        # By this point we know loc is not found elsewhere so we go to E state
        main_loc: MemoryLocation = self.main_memory.get_loc(addr)
        main_loc.update_state(State.E)
        self.cpu_cache[cpu_id].add_loc(main_loc)
        return main_loc.data

    def store_data(self, data: int, addr: int, cpu_id: int):
        """
        Store data to the cache
        """

        # Try the private cache first
        if self.cpu_cache[cpu_id].contains_addr(addr):
            # Private cache has the address, now we check the state
            pass
        pass
