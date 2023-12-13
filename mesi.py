from base import State, StudentCode, MemoryLocation, Cache

"""
MESI

I - E : Read the only copy


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
            if not self.llc.contains_addr(loc.addr):
                self.llc.add_loc(loc)

        # We need to write back to llc and main memory
        if state is State.M:
            # If address exists, simply update it
            if self.llc.contains_addr(loc.addr):
                self.llc.update_addr_data(loc.addr, loc.data)
            else:
                self.llc.add_loc(loc)

            self.main_memory.update_data(loc.addr, loc.data)

    def load_data(self, addr: int, cpu_id: int):
        """
        Load data from the cache
        """

        # Try the private cache first
        if self.cpu_cache[cpu_id].contains_addr(addr):
            # Private cache has the address, now we check the state
            loc = self.cpu_cache[cpu_id].get_loc(addr)
            self.cpu_cache[cpu_id]._data[loc.addr].last_used = self.cpu_cache[cpu_id]._clock
            if loc.state is not State.I:
                return loc.data

        # If not found in the private cache we try other caches
        # We create a list of all cpus that have the address (if any)
        cpus = [valid_cpu for valid_cpu in range(self.cpu_count) if valid_cpu != cpu_id
                and self.cpu_cache[valid_cpu].contains_addr(addr) and self.cpu_cache[valid_cpu].get_loc(
            addr).state is not State.I]

        # We need to read data so we make sure caches are set to S state
        loc = None
        modified_loc = None
        for cpu in cpus:
            loc = self.cpu_cache[cpu].get_loc(addr)
            # If in M state, write the data
            if loc.state == State.M:
                modified_loc = loc
                if self.llc.contains_addr(loc.addr):
                    self.llc.update_addr_data(loc.addr, loc.data)
                else:
                    self.llc.add_loc(loc)
                self.main_memory.update_data(loc.addr, loc.data)

            self.cpu_cache[cpu].update_addr_state(addr, State.S)
            loc.update_state(State.S)

        if modified_loc:
            if not self.cpu_cache[cpu_id].contains_addr(addr):
                self.cpu_cache[cpu_id].add_loc(modified_loc)
            else:
                self.cpu_cache[cpu_id].update_addr_data(addr, modified_loc.data)
                self.cpu_cache[cpu_id].update_addr_state(addr, State.S)
            return modified_loc.data
        elif loc:
            if not self.cpu_cache[cpu_id].contains_addr(addr):
                self.cpu_cache[cpu_id].add_loc(loc)
            else:
                self.cpu_cache[cpu_id].update_addr_data(addr, loc.data)
                self.cpu_cache[cpu_id].update_addr_state(addr, State.S)
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

        # Update LLC
        self.llc.add_loc(main_loc)
        self.cpu_cache[cpu_id].add_loc(main_loc)

        return main_loc.data

    def store_data(self, data: int, addr: int, cpu_id: int):
        """
        Store data to the cache
        """

        # Try the private cache first
        if self.cpu_cache[cpu_id].contains_addr(addr):
            # Private cache has the address, now we check the state
            loc = self.cpu_cache[cpu_id].get_loc(addr)
            self.cpu_cache[cpu_id]._data[loc.addr].last_used = self.cpu_cache[cpu_id]._clock

            # Not shared
            if loc.state in [State.E, State.M]:
                self.cpu_cache[cpu_id].update_addr_data(addr, data)

                if loc.state == State.E:
                    loc.update_state(State.M)

                # In this case we don't need to send any messages since its not shared
                return

        # Invalidate all others
        cpus = [valid_cpu for valid_cpu in range(self.cpu_count) if
                valid_cpu != cpu_id and self.cpu_cache[valid_cpu].contains_addr(addr)]

        modified_loc = None
        for cpu in cpus:
            loc = self.cpu_cache[cpu].get_loc(addr)
            if loc.state == State.M:
                modified_loc = loc
            self.cpu_cache[cpu].update_addr_state(addr, State.I)

        if modified_loc:
            # write back
            if not self.llc.contains_addr(modified_loc.addr):
                self.llc.add_loc(modified_loc)
            else:
                self.llc.update_addr_data(modified_loc.addr, modified_loc.data)

            self.main_memory.update_data(modified_loc.addr, modified_loc.data)
        else:
            # Update LLC
            main_loc = self.main_memory.get_loc(addr)

            if not self.llc.contains_addr(addr):
                self.llc.add_loc(main_loc)
            else:
                self.llc.update_addr_data(main_loc.addr, main_loc.data)

        loc = MemoryLocation(addr, data)
        loc.update_state(State.M)

        if not self.cpu_cache[cpu_id].contains_addr(addr):
            self.cpu_cache[cpu_id].add_loc(loc)
        else:
            self.cpu_cache[cpu_id].update_addr_data(addr, data)
            self.cpu_cache[cpu_id].update_addr_state(addr, State.M)
