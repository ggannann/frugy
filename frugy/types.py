from dataclasses import dataclass
import bitstruct
from typing import Any
from collections import OrderedDict
def _sizeAlign(size: int, alignment: int) -> int:
    ''' return number of padding bytes & total length after padding '''
    numPadBytes = -size % alignment
    return numPadBytes, size + numPadBytes


@dataclass
class FixedField():
    ''' Fixed length FRU field '''

    format: str  # must be suitable for bitstruct module
    value: Any = None

    def size(self) -> int:
        numBits = bitstruct.calcsize(self.format)
        if numBits % 8 != 0:
            raise RuntimeError("Bitfield not aligned to bytes")
        return int(numBits / 8)

    def serialize(self) -> bytearray:
        if type(self.value) is tuple:
            return bitstruct.pack(self.format + '<', *self.value)
        else:
            return bitstruct.pack(self.format + '<', self.value)

    def deserialize(self, input: bytearray) -> bytearray:
        n = self.size()
        tmp, remainder = input[:n], input[n:]
        result = bitstruct.unpack(self.format + '<', tmp)
        if len(result) > 1:
            self.value = result
        else:
            self.value = result[0]
        return remainder


class FruArea:
    ''' Common base class for FRU areas '''

    def __init__(self, initdict=None):
        self._dict = OrderedDict(self._schema)

    # dict interface

    def __getitem__(self, key):
        # check for special accessor
        fname = f'_get_{key}'
        if hasattr(self, fname):
            return getattr(self, fname)()
        else:
            # use generic accessor
            return self._get(key)

    def __setitem__(self, key, value):
        # check for special accessor
        fname = f'_set_{key}'
        if hasattr(self, fname):
            getattr(self, fname)(value)
        else:
            # use generic accessor
            self._set(key, value)

    def __contains__(self, key):
        return hasattr(self, f'_set_{key}') or key in self._dict

    def __repr__(self):
        return repr({k: self[k] for k in self._dict.keys()})

    def update(self, src):
        for k, v in src.items():
            self[k] = v

    # accessors

    def _get(self, key):
        v = self._dict[key].value
        if type(v) is tuple:
            return list(v)
        else:
            return v

    def _set(self, key, value):
        self._dict[key].value = value if type(value) is not list \
                                else tuple(value)

    # (de)serializing

    def _epilogue(self, payload):
        ''' return checksum and padding to 64 bit alignment '''
        _, numPadBytes = _sizeAlign(len(payload) + 1, 8)
        result = b'\x00' * numPadBytes
        cksum = (-sum(payload)) & 0xff
        result += cksum.to_bytes(length=1, byteorder='little')
        return result

    def size_payload(self):
        return sum([v.size() for v in self._dict.values()])

    def size_total(self):
        n, _ = _sizeAlign(self.size_payload()) + 1, 8)
        return n

    def serialize(self) -> bytearray:
        payload = b''.join([v.serialize() for v in self._dict.values()])
        return payload + self._epilogue(payload)

    def deserialize(self, input: bytearray):
        if len(input) % 8 != 0:
            raise RuntimeError("FRU data not aligned to 64 bit")
        if (sum(input) & 0xff) != 0:
            raise RuntimeError("FRU data checksum invalid")

        remainder = input
        for v in self._dict.values():
            remainder = v.deserialize(remainder)
