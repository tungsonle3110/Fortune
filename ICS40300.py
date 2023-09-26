from labjack import ljm
import numpy as np
import scipy.signal as signal


class ICS40300:
    def __init__(self, handle, FS_ADC, DATA_LEN_ADC):
        self.handle = handle
        self.scanRate = FS_ADC
        self.scansPerRead = DATA_LEN_ADC

        # Stream Configuration
        self.aScanListNames = ["AIN0"]  # Scan list names to stream
        self.numAddresses = len(self.aScanListNames)
        try:
            self.aScanList = ljm.namesToAddresses(self.numAddresses, self.aScanListNames)[0]
        except Exception:
            pass

    def get_values(self):
        self.set_buffer_size()
        self.start_stream()
        try:
            ret = ljm.eStreamRead(self.handle)
            mic = ret[0]
        except ljm.LJMError:
            mic = None
        self.stop_stream()

        # # Filter
        # [b, a] = signal.butter(2, [100, 49e3], btype='bandpass', fs=self.scanRate)
        # self.mic = signal.filtfilt(b, a, self.mic)

        # [b, a] = signal.butter(2, [0.002, 0.008], btype='bandpass')
        # self.mic = signal.filtfilt(b, a, self.mic)
        return mic

    def set_buffer_size(self):
        try:
            ljm.eWriteName(self.handle, "STREAM_BUFFER_SIZE_BYTES", 4096 * 8)
        except ljm.LJMError:
            pass

    def start_stream(self):
        try:
            self.scanRate = ljm.eStreamStart(self.handle, self.scansPerRead, self.numAddresses, self.aScanList,
                                             self.scanRate)
        except ljm.LJMError:
            pass

    def stop_stream(self):
        try:
            ljm.eStreamStop(self.handle)
        except ljm.LJMError:
            pass
