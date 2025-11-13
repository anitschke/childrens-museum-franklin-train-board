from collections import OrderedDict

# LimitedSizeOrderedSet is a set that removes the oldest elements when we hit
# the max length
#
# xxx doc
class LimitedSizeOrderedSet:
    def __init__(self, max_size):
        self.max_size = max_size
        self._data = OrderedDict()

    def add(self, element):
        if element not in self._data:
            self._data[element] = None  # Value can be anything, key is what matters
            if len(self._data) > self.max_size:
                # Ideally we would just do `self._data.popitem(last=False)` here
                # but  MicroPython / CircuitPython doesn't support the "last"
                # keyword argument for OrderedDict so we need to work around
                # this by getting the first element in the dict and explicitly
                # popping that element.
                # 
                # See https://github.com/micropython/micropython/issues/18370
                first_key = next(iter(self._data))
                self._data.pop(first_key)
        else:
            self._data.move_to_end(element)

    def clear(self):
        self._data.clear()

    def __contains__(self, element):
        return element in self._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)
    
# xxx doc
class LimitedSizeOrderedDict:
    def __init__(self, max_size):
        self.max_size = max_size
        self._data = OrderedDict()

    def clear(self):
        self._data.clear()

    def __setitem__(self, key, value):
        # if the item is already in the OrderedDict then delete it so when we
        # add it back in it gets added to the end.
        if key in self._data:
            del self._data[key]

        self._data[key] = value
        if len(self._data) > self.max_size:
            # Ideally we would just do `self._data.popitem(last=False)` here
            # but  MicroPython / CircuitPython doesn't support the "last"
            # keyword argument for OrderedDict so we need to work around
            # this by getting the first element in the dict and explicitly
            # popping that element.
            # 
            # See https://github.com/micropython/micropython/issues/18370
            first_key = next(iter(self._data))
            self._data.pop(first_key)

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)