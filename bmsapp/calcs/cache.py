"""`cache` module implementing a cache for objects referenced by a key.
"""
import time

class Cache:
    """Implements a cache for an object identified by a key.  Allows for a timeout of the
    cached object.
    """
    
    def __init__(self, timeout=600):
        self.timeout = timeout   # number of seconds before timeout of cache item
        self.cache = {}
        
    def store(self, key, obj):
        """
        Stores an object 'obj' in the cache having a key of 'key'.
        """
        self.cache[key] = (time.time(), obj)
        
    def get(self, key):
        """
        Returns an object matching 'key' from the cache if it is present and hasn't 
        timed out.  Returns None otherwise.
        """
        if key in self.cache:
            tm, obj = self.cache[key]
            if (time.time() - tm) < self.timeout:
                return obj
        
        return None
