from enum import Enum
from struct import unpack

class FramerState(Enum):
    wait = 1    # Waiting for new data
    inlen = 2   # Stopped receiving in the middle of length value
    indata = 3  # We have lenght and are just past len or in data area

class Framer(object):
    """Framer to convert between the TCP data stream and packages
       Frame Format: 
            Len  := 32-bit Big-Endian Int
            Data := Len * Byte
    """

    def __init__(self, callback):
        """ctor"""
        self._state = FramerState.wait
        self._data_len = 0
        self._data_buf = bytearray()
        self._len_buf = bytearray()
        self._callback = callback
        
    def DataReceived(self, data):
        """Called with data from TCP"""
        data_parsed = 0
        while data_parsed != len(data):
            data_parsed = data_parsed + _ParseData(data[data_parsed:])

    def _ParseData(self, data):
        if self._state == FramerState.wait:
            # Did we get enough data to reconstruct length?
            if len(data) >= 4:
                # Extract length and continue in indata state
                self._data_len = unpack('>I', data)[0]
                self._state = FramerState.indata
                return 4
            else:
                # We did not receive enough data to reconstruct lenght
                self._len_buf = data
                self._state = FramerState.inlen
                return len(data)
        elif self._state == FramerState.inlen:
            # Did we get enough data to reconstruct len?
            if len(data) + len(self._len_buf) >= 4:
                # Build len and continue
                missing_data = 4 - len(self._len_buf)
                self._len_buf.extend(data[0:missing_data-1])
                self._data_len = unpack('>I', self._len_buf)[0]
                self._data_buf = bytearray()
                self._state = FramerState.indata
                return missing_data
            else:
                # Continue appending the len buf
                self._len_buf.extend(data)
                return len(data)
        elif self._state == FramerState.indata:
            # Do we have enough data to finish the packet?
            missing_data = self._data_len - len(self._data_buf)

            if missing_data <= len(data):
                # We have enough data!
                # Build the data buffer
                self._data_buf.extend(data[0:missing_data-1])

                # Make a callback with data buffer
                self._callback(self._data_buf)

                # Clear the state
                self._data_buf = bytearray()
                self._data_len = 0
                self._state = FramerState.wait

                # Return amount of data consumed
                return missing_data
            else:
                # This data will not fill the buffer
                self._data_buf.extend(data)

                # Return amount of data consumed
                return len(data)