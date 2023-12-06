from base import State, StudentCode, MemoryLocation

class MESICoherence(StudentCode):
    # loc is of type MemoryLocation defined in base.py
    def evict_from_private_cache(self, loc, cpu_id : int):
        pass

    def load_data(self, addr : int, cpu_id : int):
        pass

    def store_data(self, data : int, addr : int, cpu_id : int):
        pass